from __future__ import annotations

import contextlib
import gc
import hashlib
import json
import multiprocessing
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from magicai.assistant import MagicAI
from magicai.llm.ollama import MODEL, OLLAMA_URL
from magicai.services.rule_service import warm_rule_index
from magicai.scryfall import configure_card_source, load_cards
from tests.quality.dynamic.card_catalog import CardCatalog
from tests.quality.dynamic.concepts import get_concepts
from tests.quality.dynamic.execution import (
    run_dynamic_scenarios,
    summarize_results,
    write_dynamic_reports,
)
from tests.quality.dynamic.failure_store import write_manifest
from tests.quality.dynamic.models import DynamicScenario
from tests.quality.dynamic.scenario_generator import ScenarioGenerator


DYNAMIC_CAMPAIGN_MANIFEST_VERSION = 2
RUN_COMPLETE_VERSION = 1
CODE_FINGERPRINT_PATHS = (
    "magicai/assistant/core.py",
    "magicai/context_enricher.py",
    "magicai/judge_result.py",
    "magicai/oracle_abilities.py",
    "magicai/scryfall.py",
    "magicai/retrieval/concept_evidence.py",
    "magicai/retrieval/rule_queries.py",
    "magicai/services/rule_service.py",
    "magicai/validation/answer.py",
    "magicai/validation/premise_guard.py",
    "magicai/validation/rule_renderer.py",
    "tests/quality/dynamic/campaign.py",
    "tests/quality/dynamic/campaign_runner.py",
    "tests/quality/dynamic/card_catalog.py",
    "tests/quality/dynamic/concepts.py",
    "tests/quality/dynamic/execution.py",
    "tests/quality/dynamic/models.py",
    "tests/quality/dynamic/premise_validation.py",
    "tests/quality/dynamic/scenario_generator.py",
    "tests/quality/dynamic/semantic_validation.py",
    "tests/quality/dynamic_campaign_test.py",
)

_PRELOADED_CATALOG: CardCatalog | None = None
_PRELOADED_ORACLE_PATH = ""


class DynamicCampaignError(ValueError):
    pass


def prepare_campaign(
    *,
    project_root: Path,
    output_root: Path,
    base_seed: int,
    seeds: list[int],
    cases_per_seed: int,
    concept_ids: list[str],
    oracle_file: str | None,
    workers: int,
    requires_oracle: bool,
    resume: bool,
    command: list[str],
) -> dict[str, Any]:
    if workers < 1:
        raise DynamicCampaignError("--workers must be at least 1.")
    output_root = output_root.resolve()
    manifest_path = output_root / "campaign_manifest.json"
    current = _campaign_manifest_payload(
        project_root=project_root,
        base_seed=base_seed,
        seeds=seeds,
        cases_per_seed=cases_per_seed,
        concept_ids=concept_ids,
        oracle_file=oracle_file,
        workers=workers,
        requires_oracle=requires_oracle,
        command=command,
    )
    if resume:
        if not manifest_path.is_file():
            raise DynamicCampaignError(
                f"Campaign manifest not found for resume: {manifest_path}"
            )
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        _validate_resume_manifest(previous, current)
        previous.update(
            {
                "status": "running",
                "last_resumed_at": _now_iso(),
                "updated_at": _now_iso(),
                "workers": workers,
                "last_command": command,
            }
        )
        _atomic_write_json(manifest_path, previous)
        return previous
    if output_root.exists() and any(output_root.iterdir()):
        raise DynamicCampaignError(
            f"Output directory is not empty: {output_root}. Use --resume for "
            "the same campaign or choose a new directory."
        )
    output_root.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(manifest_path, current)
    return current


def execute_campaign_runs(
    *,
    project_root: Path,
    output_root: Path,
    base_seed: int,
    seeds: list[int],
    cases_per_seed: int,
    concept_ids: list[str],
    oracle_file: str | None,
    workers: int,
    requires_oracle: bool,
    fail_fast: bool,
    resume: bool,
) -> tuple[list[dict[str, Any]], list[DynamicScenario], list[dict[str, Any]]]:
    if fail_fast and workers > 1:
        raise DynamicCampaignError("--fail-fast is only supported with --workers 1.")

    _preload_shared_state(
        oracle_file,
        requires_oracle=requires_oracle,
        concept_ids=concept_ids,
    )
    tasks: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    scenarios: list[DynamicScenario] = []
    errors: list[dict[str, Any]] = []

    for run_index, seed in enumerate(seeds, start=1):
        run_dir = output_root / _run_dir_name(run_index, seed)
        complete = (
            _load_completed_run(
                run_dir,
                run_index=run_index,
                seed=seed,
                cases_per_seed=cases_per_seed,
            )
            if resume
            else None
        )
        if complete is not None:
            summaries.append(complete["summary"])
            scenarios.extend(_load_run_scenarios(run_dir / "manifest.json"))
            print(
                f"[RESUME] run {run_index}/{len(seeds)} seed={seed} already complete"
            )
            continue
        if run_dir.exists():
            shutil.rmtree(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        concepts = get_concepts(concept_ids)
        catalog = (
            _worker_catalog(oracle_file)
            if requires_oracle
            else CardCatalog(oracle_file)
        )
        generated = ScenarioGenerator(
            seed=seed,
            catalog=catalog,
            concepts=concepts,
        ).generate(cases_per_seed)
        write_manifest(run_dir / "manifest.json", seed, generated)
        tasks.append(
            {
                "project_root": str(project_root),
                "output_root": str(output_root),
                "base_seed": base_seed,
                "run_index": run_index,
                "total_runs": len(seeds),
                "seed": seed,
                "cases_per_seed": cases_per_seed,
                "concept_ids": concept_ids,
                "oracle_file": oracle_file,
                "requires_oracle": requires_oracle,
                "fail_fast": fail_fast,
            }
        )

    if not tasks:
        return _sort_runs(summaries), scenarios, errors

    # The generator corpus is no longer needed after manifests are written.
    # Release it before forking, then preload MagicAI's runtime card index once
    # so worker processes inherit a read-only copy instead of parsing Oracle in
    # parallel.
    global _PRELOADED_CATALOG, _PRELOADED_ORACLE_PATH
    _PRELOADED_CATALOG = None
    _PRELOADED_ORACLE_PATH = ""
    gc.collect()
    if requires_oracle:
        runtime_oracle = Path(oracle_file).resolve() if oracle_file else CardCatalog().oracle_file.resolve()
        configure_card_source(runtime_oracle)
        load_cards()

    max_workers = min(workers, len(tasks))
    if max_workers == 1:
        for task in tasks:
            outcome = _execute_run_task(task)
            _collect_outcome(
                outcome,
                output_root=output_root,
                summaries=summaries,
                scenarios=scenarios,
                errors=errors,
            )
            _print_outcome(outcome)
            if fail_fast and outcome.get("summary", {}).get("failures"):
                break
        return _sort_runs(summaries), scenarios, errors

    executor_kwargs: dict[str, Any] = {"max_workers": max_workers}
    if sys.platform != "win32":
        try:
            executor_kwargs["mp_context"] = multiprocessing.get_context("fork")
        except ValueError:
            pass

    with ProcessPoolExecutor(**executor_kwargs) as executor:
        futures = {executor.submit(_execute_run_task, task): task for task in tasks}
        for future in as_completed(futures):
            task = futures[future]
            try:
                outcome = future.result()
            except Exception:
                outcome = {
                    "run_index": task["run_index"],
                    "seed": task["seed"],
                    "error": traceback.format_exc(),
                }
            _collect_outcome(
                outcome,
                output_root=output_root,
                summaries=summaries,
                scenarios=scenarios,
                errors=errors,
            )
            _print_outcome(outcome)

    return _sort_runs(summaries), scenarios, errors


def finalize_campaign_manifest(
    output_root: Path,
    *,
    status: str,
    run_summaries: list[dict[str, Any]],
    run_errors: list[dict[str, Any]],
    elapsed_seconds: float,
) -> None:
    path = output_root / "campaign_manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(
        {
            "status": status,
            "updated_at": _now_iso(),
            "finished_at": _now_iso() if status in {"completed", "failed"} else "",
            "elapsed_seconds": round(elapsed_seconds, 6),
            "runs_completed": len(run_summaries),
            "run_errors": run_errors,
        }
    )
    _atomic_write_json(path, payload)


def _execute_run_task(task: dict[str, Any]) -> dict[str, Any]:
    project_root = Path(task["project_root"])
    output_root = Path(task["output_root"])
    run_index = int(task["run_index"])
    seed = int(task["seed"])
    run_dir = output_root / _run_dir_name(run_index, seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "run.log"

    try:
        with log_path.open("w", encoding="utf-8", buffering=1) as log:
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                os.chdir(project_root)
                print("=" * 80)
                print(
                    f"RUN {run_index}/{task['total_runs']} · seed {seed} · pid {os.getpid()}"
                )
                print("=" * 80)
                generated = _load_run_scenarios(run_dir / "manifest.json")
                manifest = run_dir / "manifest.json"
                if task.get("requires_oracle"):
                    runtime_oracle = (
                        Path(task["oracle_file"]).resolve()
                        if task.get("oracle_file")
                        else CardCatalog().oracle_file.resolve()
                    )
                    configure_card_source(runtime_oracle)
                    load_cards()
                assistant = MagicAI()

                def progress(scenario, result):
                    source = scenario.card_name or "rules-only"
                    print(
                        f"[{scenario.id}] {scenario.concept_id} · {source} · "
                        f"{scenario.template_id}"
                    )
                    print(f"  {result['status']} ({result['elapsed']:.2f}s)")
                    if result.get("dynamic_failure_file"):
                        print(f"  Saved failure: {result['dynamic_failure_file']}")

                started = time.perf_counter()
                results, saved_failures, elapsed = run_dynamic_scenarios(
                    assistant,
                    generated,
                    failure_dir=run_dir / "failures",
                    fail_fast=bool(task["fail_fast"]),
                    progress_callback=progress,
                )
                metadata = {
                    "Campaign base seed": str(task["base_seed"]),
                    "Campaign run": f"{run_index}/{task['total_runs']}",
                    "Seed": str(seed),
                    "Generated cases": str(len(generated)),
                    "Executed cases": str(len(results)),
                    "Workers": "process",
                    "PID": str(os.getpid()),
                    "Mode": "campaign",
                }
                txt = run_dir / "report.txt"
                xml = run_dir / "report.xml"
                html = run_dir / "report.html"
                write_dynamic_reports(
                    results=results,
                    txt_file=txt,
                    xml_file=xml,
                    html_file=html,
                    total_elapsed=elapsed,
                    metadata=metadata,
                    suite_name="MagicAI Dynamic Campaign Run",
                    suite_subtitle=(
                        "Ejecución individual dentro de una campaña multisemilla "
                        "reproducible."
                    ),
                )
                summary = summarize_results(results)
                run_summary = {
                    "index": run_index,
                    "seed": seed,
                    "cases": summary["cases"],
                    "failures": summary["failures"],
                    "warnings": summary["warnings"],
                    "status": summary["status"],
                    "elapsed_seconds": round(elapsed, 6),
                    "wall_seconds": round(time.perf_counter() - started, 6),
                    "manifest": _relative(manifest, output_root),
                    "txt": _relative(txt, output_root),
                    "xml": _relative(xml, output_root),
                    "html": _relative(html, output_root),
                    "log": _relative(log_path, output_root),
                    "failure_files": [
                        _relative(path, output_root) for path in saved_failures
                    ],
                    "origin_counts": summary.get("origin_counts", {}),
                    "llm_calls": summary.get("llm_calls", 0),
                    "timing_means": summary.get("timing_means", {}),
                    "timing_sums": summary.get("timing_sums", {}),
                    "timing_counts": summary.get("timing_counts", {}),
                }
                _atomic_write_json(
                    run_dir / "run_complete.json",
                    {
                        "schema_version": RUN_COMPLETE_VERSION,
                        "artifact_purpose": "evaluation",
                        "training_allowed": False,
                        "automatic_learning": False,
                        "automatic_promotion": False,
                        "run_index": run_index,
                        "seed": seed,
                        "cases_per_seed": int(task["cases_per_seed"]),
                        "finished_at": _now_iso(),
                        "summary": run_summary,
                    },
                )
                print("RUN COMPLETE")
        return {"run_index": run_index, "seed": seed, "summary": run_summary}
    except Exception:
        error = traceback.format_exc()
        _atomic_write_json(
            run_dir / "run_error.json",
            {
                "run_index": run_index,
                "seed": seed,
                "saved_at": _now_iso(),
                "error": error,
            },
        )
        return {"run_index": run_index, "seed": seed, "error": error}


def _collect_outcome(
    outcome: dict[str, Any],
    *,
    output_root: Path,
    summaries: list[dict[str, Any]],
    scenarios: list[DynamicScenario],
    errors: list[dict[str, Any]],
) -> None:
    if outcome.get("error"):
        errors.append(
            {
                "run_index": outcome.get("run_index"),
                "seed": outcome.get("seed"),
                "error": outcome.get("error"),
            }
        )
        return
    summary = outcome["summary"]
    summaries.append(summary)
    run_dir = output_root / _run_dir_name(summary["index"], summary["seed"])
    scenarios.extend(_load_run_scenarios(run_dir / "manifest.json"))


def _print_outcome(outcome: dict[str, Any]) -> None:
    if outcome.get("error"):
        print(f"[ERROR] run {outcome.get('run_index')} seed={outcome.get('seed')}")
        print(str(outcome["error"]).splitlines()[-1])
        return
    summary = outcome["summary"]
    print(
        f"[DONE] run {summary['index']} seed={summary['seed']} "
        f"cases={summary['cases']} failures={summary['failures']} "
        f"warnings={summary['warnings']} time={summary['elapsed_seconds']:.2f}s"
    )


def _preload_shared_state(
    oracle_file: str | None,
    *,
    requires_oracle: bool,
    concept_ids: list[str],
) -> None:
    global _PRELOADED_CATALOG, _PRELOADED_ORACLE_PATH
    if requires_oracle:
        catalog = CardCatalog(oracle_file)
        catalog.load()
        for concept in get_concepts(concept_ids):
            if concept.selector is None:
                continue
            if concept.selector in {
                "mana_ability",
                "source_independence_ability",
                "activated_nonmana",
            }:
                catalog.select_abilities(concept.selector)
            else:
                catalog.select(concept.selector)
        _PRELOADED_CATALOG = catalog
        _PRELOADED_ORACLE_PATH = str(catalog.oracle_file.resolve())
    warm_rule_index()


def _worker_catalog(oracle_file: str | None) -> CardCatalog:
    requested = str(Path(oracle_file).resolve()) if oracle_file else ""
    if _PRELOADED_CATALOG is not None and (
        not requested or requested == _PRELOADED_ORACLE_PATH
    ):
        return _PRELOADED_CATALOG
    catalog = CardCatalog(oracle_file)
    catalog.load()
    return catalog


def _campaign_manifest_payload(
    *,
    project_root: Path,
    base_seed: int,
    seeds: list[int],
    cases_per_seed: int,
    concept_ids: list[str],
    oracle_file: str | None,
    workers: int,
    requires_oracle: bool,
    command: list[str],
) -> dict[str, Any]:
    oracle_path = (
        Path(oracle_file).resolve()
        if oracle_file
        else CardCatalog().oracle_file.resolve()
    )
    rules_path = (project_root / "sources/rules/MagicCompRules.txt").resolve()
    created = _now_iso()
    return {
        "schema_version": DYNAMIC_CAMPAIGN_MANIFEST_VERSION,
        "artifact_purpose": "evaluation",
        "training_allowed": False,
        "automatic_learning": False,
        "automatic_promotion": False,
        "status": "running",
        "created_at": created,
        "updated_at": created,
        "finished_at": "",
        "base_seed": base_seed,
        "seeds": seeds,
        "runs_requested": len(seeds),
        "cases_per_seed": cases_per_seed,
        "concept_ids": concept_ids,
        "workers": workers,
        "command": command,
        "python": sys.version.split()[0],
        "git_commit": _git_commit(project_root),
        "model": {"name": MODEL, "endpoint": OLLAMA_URL, "temperature": 0},
        "sources": {
            "oracle": (
                {"required": False, "path": str(oracle_path)}
                if not requires_oracle
                else {"required": True, **_file_snapshot(oracle_path)}
            ),
            "rules": {"required": True, **_file_snapshot(rules_path)},
            "rulings": _optional_source_snapshot(
                project_root / "sources/scryfall/rulings.json"
            ),
            "symbology": _optional_source_snapshot(
                project_root / "sources/scryfall/symbology.json"
            ),
        },
        "code_fingerprint": _code_fingerprint(project_root),
        "runs_completed": 0,
        "run_errors": [],
        "elapsed_seconds": 0.0,
    }


def _validate_resume_manifest(previous: dict[str, Any], current: dict[str, Any]) -> None:
    for key in (
        "artifact_purpose",
        "training_allowed",
        "automatic_learning",
        "automatic_promotion",
    ):
        if previous.get(key) != current[key]:
            raise DynamicCampaignError(f"Unsafe or incompatible campaign manifest: {key}")
    stable = (
        "schema_version",
        "base_seed",
        "seeds",
        "runs_requested",
        "cases_per_seed",
        "concept_ids",
        "model",
        "sources",
        "code_fingerprint",
    )
    changed = [key for key in stable if previous.get(key) != current.get(key)]
    if changed:
        raise DynamicCampaignError(
            "Cannot resume because reproducibility inputs changed: "
            + ", ".join(changed)
        )


def _load_completed_run(
    run_dir: Path,
    *,
    run_index: int,
    seed: int,
    cases_per_seed: int,
) -> dict[str, Any] | None:
    path = run_dir / "run_complete.json"
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("run_index") != run_index
        or payload.get("seed") != seed
        or payload.get("cases_per_seed") != cases_per_seed
    ):
        raise DynamicCampaignError(f"Invalid completion marker: {path}")
    if not (run_dir / "manifest.json").is_file():
        raise DynamicCampaignError(
            f"Completed run is missing its manifest: {run_dir}"
        )
    return payload


def _load_run_scenarios(path: Path) -> list[DynamicScenario]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [DynamicScenario.from_dict(item) for item in payload.get("scenarios", [])]


def _sort_runs(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(items, key=lambda item: int(item["index"]))


def _run_dir_name(index: int, seed: int) -> str:
    return f"run_{index:02d}_seed_{seed}"


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _optional_source_snapshot(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.is_file():
        return {"required": False, "exists": False, "path": str(resolved)}
    return {"required": False, "exists": True, **_file_snapshot(resolved)}


def _file_snapshot(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


def _code_fingerprint(project_root: Path) -> dict[str, Any]:
    files: dict[str, str] = {}
    combined = hashlib.sha256()
    for relative in CODE_FINGERPRINT_PATHS:
        path = project_root / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        digest = _sha256_file(path)
        files[relative] = digest
        combined.update(relative.encode("utf-8"))
        combined.update(b"\0")
        combined.update(digest.encode("ascii"))
        combined.update(b"\0")
    return {"sha256": combined.hexdigest(), "files": files}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _git_commit(project_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
