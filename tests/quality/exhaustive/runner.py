from __future__ import annotations

import contextlib
import gzip
import hashlib
import json
import multiprocessing
import os
import shutil
import sys
import time
import traceback
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from magicai.assistant import MagicAI
from magicai.services.rule_service import warm_rule_index
from magicai.scryfall import configure_card_source, load_cards
from tests.quality.dynamic.execution import run_dynamic_scenarios, summarize_results
from tests.quality.dynamic.models import DynamicScenario

MANIFEST_VERSION = 1
SHARD_COMPLETE_VERSION = 1
CODE_PATHS = (
    "magicai/assistant/core.py",
    "magicai/answer_generator.py",
    "magicai/oracle_abilities.py",
    "magicai/validation/rule_renderer.py",
    "tests/quality/dynamic/card_catalog.py",
    "tests/quality/dynamic/concepts.py",
    "tests/quality/dynamic/models.py",
    "tests/quality/dynamic/premise_validation.py",
    "tests/quality/dynamic/scenario_generator.py",
    "tests/quality/dynamic/semantic_validation.py",
    "tests/quality/exhaustive/planner.py",
    "tests/quality/exhaustive/runner.py",
    "tests/quality/oracle_exhaustive_test.py",
)


class ExhaustiveAuditError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def code_fingerprint(project_root: Path) -> dict[str, object]:
    files: list[dict[str, str]] = []
    combined = hashlib.sha256()
    for relative in CODE_PATHS:
        path = project_root / relative
        if not path.is_file():
            raise ExhaustiveAuditError(f"Fingerprint file missing: {relative}")
        digest = sha256_file(path)
        files.append({"path": relative, "sha256": digest})
        combined.update(relative.encode("utf-8"))
        combined.update(b"\0")
        combined.update(digest.encode("ascii"))
        combined.update(b"\0")
    return {"sha256": combined.hexdigest(), "files": files}


def prepare_exhaustive_campaign(
    *,
    project_root: Path,
    output_root: Path,
    oracle_file: Path,
    scenarios: Iterable[DynamicScenario],
    static_summary: dict[str, object],
    static_findings: Iterable[dict[str, object]],
    workers: int,
    shard_size: int,
    template_mode: str,
    families: tuple[str, ...],
    resume: bool,
    allow_llm: bool,
    command: list[str],
) -> dict[str, Any]:
    scenario_list = list(scenarios)
    fingerprint = {
        "schema_version": MANIFEST_VERSION,
        "artifact_purpose": "evaluation",
        "training_allowed": False,
        "automatic_learning": False,
        "automatic_promotion": False,
        "oracle_file": str(oracle_file.resolve()),
        "oracle_sha256": sha256_file(oracle_file),
        "code_fingerprint": code_fingerprint(project_root),
        "scenario_sha256": _scenario_fingerprint(scenario_list),
        "scenario_total": len(scenario_list),
        "shard_size": shard_size,
        "template_mode": template_mode,
        "families": list(families),
        "allow_llm": allow_llm,
    }
    manifest_path = output_root / "campaign_manifest.json"
    if resume:
        if not manifest_path.is_file():
            raise ExhaustiveAuditError("--resume requires an existing campaign_manifest.json")
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        comparable = {key: existing.get(key) for key in fingerprint}
        if comparable != fingerprint:
            raise ExhaustiveAuditError(
                "Cannot resume: Oracle, code, scenarios, families, templates, or shard size changed."
            )
    else:
        if output_root.exists() and any(output_root.iterdir()):
            raise ExhaustiveAuditError(
                f"Output directory is not empty: {output_root}. Use a new directory or --resume."
            )
        output_root.mkdir(parents=True, exist_ok=True)
        payload = {
            **fingerprint,
            "status": "prepared",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "workers_requested": workers,
            "command": command,
            "static_summary": static_summary,
        }
        _atomic_json(manifest_path, payload)
        _write_jsonl_gz(output_root / "scenarios.jsonl.gz", (item.to_dict() for item in scenario_list))
        _write_jsonl_gz(output_root / "static_findings.jsonl.gz", static_findings)
        _atomic_json(output_root / "static_summary.json", static_summary)
    return fingerprint


def execute_exhaustive_campaign(
    *,
    project_root: Path,
    output_root: Path,
    oracle_file: Path,
    scenarios: Iterable[DynamicScenario],
    workers: int,
    shard_size: int,
    resume: bool,
    allow_llm: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scenario_list = list(scenarios)
    shards = [scenario_list[index:index + shard_size] for index in range(0, len(scenario_list), shard_size)]
    completed: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []

    for shard_index, shard in enumerate(shards, start=1):
        shard_dir = output_root / f"shard_{shard_index:04d}"
        complete_path = shard_dir / "shard_complete.json"
        if resume and complete_path.is_file():
            completed.append(json.loads(complete_path.read_text(encoding="utf-8"))["summary"])
            print(f"[RESUME] shard {shard_index}/{len(shards)} already complete")
            continue
        if shard_dir.exists():
            shutil.rmtree(shard_dir)
        shard_dir.mkdir(parents=True, exist_ok=True)
        tasks.append(
            {
                "project_root": str(project_root),
                "output_root": str(output_root),
                "oracle_file": str(oracle_file),
                "shard_index": shard_index,
                "shard_total": len(shards),
                "scenarios": [item.to_dict() for item in shard],
                "allow_llm": allow_llm,
            }
        )

    if not tasks:
        return sorted(completed, key=lambda item: item["index"]), []

    configure_card_source(oracle_file)
    load_cards()
    warm_rule_index()

    errors: list[dict[str, Any]] = []
    max_workers = min(workers, len(tasks))
    executor_kwargs: dict[str, Any] = {"max_workers": max_workers}
    if sys.platform != "win32":
        try:
            executor_kwargs["mp_context"] = multiprocessing.get_context("fork")
        except ValueError:
            pass

    if max_workers == 1:
        outcomes = [_execute_shard(task) for task in tasks]
    else:
        outcomes = []
        with ProcessPoolExecutor(**executor_kwargs) as executor:
            futures = {executor.submit(_execute_shard, task): task for task in tasks}
            for future in as_completed(futures):
                task = futures[future]
                try:
                    outcomes.append(future.result())
                except Exception:
                    outcomes.append(
                        {
                            "index": task["shard_index"],
                            "error": traceback.format_exc(),
                        }
                    )

    for outcome in outcomes:
        if outcome.get("error"):
            errors.append(outcome)
            print(f"[ERROR] shard {outcome['index']}")
        else:
            completed.append(outcome["summary"])
            summary = outcome["summary"]
            print(
                f"[DONE] shard {summary['index']}/{len(shards)} "
                f"cases={summary['cases']} failures={summary['failures']} "
                f"warnings={summary['warnings']} wall={summary['wall_seconds']:.2f}s"
            )
    return sorted(completed, key=lambda item: item["index"]), errors


def finalize_exhaustive_campaign(
    output_root: Path,
    *,
    shard_summaries: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    wall_seconds: float,
    static_summary: dict[str, object],
) -> dict[str, Any]:
    origin_counts: Counter[str] = Counter()
    dependency_counts: Counter[str] = Counter()
    cases = failures = warnings = llm_calls = 0
    for shard in shard_summaries:
        cases += int(shard["cases"])
        failures += int(shard["failures"])
        warnings += int(shard["warnings"])
        llm_calls += int(shard.get("llm_calls", 0))
        origin_counts.update(shard.get("origin_counts", {}))
        dependency_counts.update(shard.get("source_dependency_counts", {}))
    status = "FAIL" if failures or errors else ("WARN" if warnings else "PASS")
    payload = {
        "artifact_purpose": "evaluation",
        "training_allowed": False,
        "automatic_learning": False,
        "automatic_promotion": False,
        "status": status,
        "cases": cases,
        "failures": failures,
        "warnings": warnings,
        "llm_calls": llm_calls,
        "origin_counts": dict(sorted(origin_counts.items())),
        "source_dependency_counts": dict(sorted(dependency_counts.items())),
        "wall_seconds": round(wall_seconds, 6),
        "shards_completed": len(shard_summaries),
        "errors": errors,
        "static_summary": static_summary,
        "shards": shard_summaries,
    }
    _atomic_json(output_root / "exhaustive_summary.json", payload)
    (output_root / "exhaustive_summary.md").write_text(_render_summary(payload), encoding="utf-8")
    manifest_path = output_root / "campaign_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(
        {
            "status": "failed" if status == "FAIL" else "completed",
            "updated_at": _now_iso(),
            "finished_at": _now_iso(),
            "wall_seconds": round(wall_seconds, 6),
            "shards_completed": len(shard_summaries),
            "errors": errors,
        }
    )
    _atomic_json(manifest_path, manifest)
    return payload


def _execute_shard(task: dict[str, Any]) -> dict[str, Any]:
    output_root = Path(task["output_root"])
    shard_index = int(task["shard_index"])
    shard_dir = output_root / f"shard_{shard_index:04d}"
    log_path = shard_dir / "run.log"
    started = time.perf_counter()
    try:
        with log_path.open("w", encoding="utf-8", buffering=1) as log:
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                os.chdir(task["project_root"])
                oracle_file = Path(task["oracle_file"])
                os.environ["MAGICAI_QUIET_EVALUATION"] = "1"
                if task.get("allow_llm"):
                    os.environ.pop("MAGICAI_EVALUATION_DETERMINISTIC_ONLY", None)
                else:
                    os.environ["MAGICAI_EVALUATION_DETERMINISTIC_ONLY"] = "1"
                configure_card_source(oracle_file)
                load_cards()
                warm_rule_index()
                assistant = MagicAI()
                scenarios = [DynamicScenario.from_dict(item) for item in task["scenarios"]]

                def progress(scenario, result):
                    print(
                        f"[{scenario.id}] {scenario.concept_id} · "
                        f"{scenario.card_name or 'rules-only'} · {result['status']} "
                        f"({result.get('elapsed', 0.0):.3f}s)",
                        flush=True,
                    )

                results, failures_saved, elapsed = run_dynamic_scenarios(
                    assistant,
                    scenarios,
                    failure_dir=shard_dir / "failures",
                    fail_fast=False,
                    progress_callback=progress,
                )
                summary = summarize_results(results)
                dependency_counts = Counter(
                    scenario.source_dependency
                    for scenario in scenarios
                    if scenario.source_dependency
                )
                compact = (_compact_result(result) for result in results)
                _write_jsonl_gz(shard_dir / "results.jsonl.gz", compact)
                shard_summary = {
                    "index": shard_index,
                    "cases": summary["cases"],
                    "failures": summary["failures"],
                    "warnings": summary["warnings"],
                    "status": summary["status"],
                    "elapsed_seconds": round(elapsed, 6),
                    "wall_seconds": round(time.perf_counter() - started, 6),
                    "origin_counts": summary.get("origin_counts", {}),
                    "llm_calls": summary.get("llm_calls", 0),
                    "source_dependency_counts": dict(sorted(dependency_counts.items())),
                    "failure_files": [str(path.relative_to(output_root)) for path in failures_saved],
                    "results": str((shard_dir / "results.jsonl.gz").relative_to(output_root)),
                    "log": str(log_path.relative_to(output_root)),
                }
                _atomic_json(
                    shard_dir / "shard_complete.json",
                    {
                        "schema_version": SHARD_COMPLETE_VERSION,
                        "artifact_purpose": "evaluation",
                        "training_allowed": False,
                        "automatic_learning": False,
                        "automatic_promotion": False,
                        "finished_at": _now_iso(),
                        "summary": shard_summary,
                    },
                )
        return {"index": shard_index, "summary": shard_summary}
    except Exception:
        error = traceback.format_exc()
        _atomic_json(shard_dir / "shard_error.json", {"saved_at": _now_iso(), "error": error})
        return {"index": shard_index, "error": error}


def _compact_result(result: dict[str, Any]) -> dict[str, Any]:
    steps = result.get("steps", [])
    first = steps[0] if steps else {}
    judge = first.get("judge_result", {}) or {}
    return {
        "id": result.get("id"),
        "status": result.get("status"),
        "elapsed": result.get("elapsed", 0.0),
        "question": first.get("question", ""),
        "answer": first.get("answer", ""),
        "failures": result.get("failures", []),
        "warnings": result.get("warnings", []),
        "judge": {
            "origin": judge.get("origin", ""),
            "llm_called": judge.get("llm_called", False),
            "status": judge.get("status", ""),
            "confidence": judge.get("confidence", ""),
            "rules": judge.get("rules", []),
            "timings": judge.get("timings", {}),
        },
        "dynamic": result.get("dynamic", {}),
    }


def _scenario_fingerprint(scenarios: list[DynamicScenario]) -> str:
    digest = hashlib.sha256()
    for scenario in scenarios:
        encoded = json.dumps(
            scenario.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest.update(encoded)
        digest.update(b"\n")
    return digest.hexdigest()


def _write_jsonl_gz(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(temporary, "wt", encoding="utf-8", compresslevel=6) as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
            handle.write("\n")
    os.replace(temporary, path)


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _render_summary(payload: dict[str, Any]) -> str:
    static = payload["static_summary"]
    lines = [
        "# MagicAI Exhaustive Oracle Audit",
        "",
        f"- Status: **{payload['status']}**",
        f"- Cases: **{payload['cases']}**",
        f"- Failures: **{payload['failures']}**",
        f"- Warnings: **{payload['warnings']}**",
        f"- LLM calls: **{payload['llm_calls']}**",
        f"- Wall time: **{payload['wall_seconds']:.2f}s**",
        f"- Supported cards scanned: **{static['supported_cards']}**",
        f"- Candidate total: **{static['candidate_total']}**",
        f"- Static findings: **{static['static_findings']}**",
        "",
        "## Candidate families",
        "",
    ]
    for family, count in static["candidate_counts"].items():
        lines.append(f"- `{family}`: {count}")
    lines.extend(["", "## Answer origins", ""])
    for origin, count in payload["origin_counts"].items():
        lines.append(f"- `{origin}`: {count}")
    lines.extend(["", "This artifact is evaluation-only. It is not training data.", ""])
    return "\n".join(lines)
