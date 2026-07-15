from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shlex
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from magicai.assistant import MagicAI

from .diagnostics import build_findings_by_family
from .execution import run_feedback_case
from .models import (
    FeedbackCase,
    FeedbackCaseResult,
    FeedbackFailureFamily,
    FeedbackOutcome,
)
from .reports import write_feedback_reports


CAMPAIGN_SCHEMA_VERSION = "1.0"
RESULT_SCHEMA_VERSION = "1.0"
CAMPAIGN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SOURCE_SNAPSHOT_PATHS = (
    Path("sources/rules/MagicCompRules.txt"),
    Path("sources/scryfall/oracle-cards.json"),
    Path("sources/scryfall/rulings.json"),
    Path("sources/scryfall/symbology.json"),
)


class FeedbackCampaignError(ValueError):
    pass


@dataclass(slots=True)
class FeedbackCampaignRun:
    results: list[FeedbackCaseResult]
    output_dir: Path
    manifest: dict[str, Any]
    interrupted: bool = False


class FeedbackCampaignStore:
    def __init__(
        self,
        *,
        campaign_id: str,
        output_dir: Path,
        input_path: Path,
        project_root: Path,
        command: list[str] | None = None,
        include_source_hashes: bool = True,
    ) -> None:
        self.campaign_id = validate_campaign_id(campaign_id)
        self.output_dir = output_dir
        self.input_path = input_path
        self.project_root = project_root
        self.command = list(command or sys.argv)
        self.include_source_hashes = include_source_hashes
        self.manifest_path = self.output_dir / "campaign_manifest.json"
        self.progress_path = self.output_dir / "campaign_progress.json"
        self.completed_dir = self.output_dir / "completed"
        self.errors_dir = self.output_dir / "execution_errors"

    def prepare(self, cases: list[FeedbackCase], *, resume: bool) -> dict[str, Any]:
        fingerprints = case_fingerprints(cases)
        current_sources = source_snapshots(
            self.project_root,
            include_hashes=self.include_source_hashes,
        )
        current_model = model_snapshot()
        current_code = code_snapshot(self.project_root)
        if resume:
            manifest = self._load_manifest()
            self._validate_manifest(
                manifest,
                fingerprints,
                current_sources=current_sources,
                current_model=current_model,
                current_code=current_code,
            )
            self._ensure_directories()
            manifest["last_resumed_at"] = now_iso()
            manifest["status"] = "running"
            manifest["updated_at"] = now_iso()
            atomic_write_json(self.manifest_path, manifest)
            return manifest

        if self.output_dir.exists() and any(self.output_dir.iterdir()):
            raise FeedbackCampaignError(
                f"Output directory is not empty: {self.output_dir}. "
                "Use --resume for the same campaign or choose another campaign id."
            )

        self._ensure_directories()
        created_at = now_iso()
        manifest = {
            "schema_version": CAMPAIGN_SCHEMA_VERSION,
            "artifact_purpose": "evaluation",
            "training_allowed": False,
            "automatic_learning": False,
            "automatic_promotion": False,
            "campaign_id": self.campaign_id,
            "status": "running",
            "created_at": created_at,
            "updated_at": created_at,
            "finished_at": "",
            "input_path": str(self.input_path),
            "command": shlex.join(self.command),
            "case_ids": [case.id for case in cases],
            "case_fingerprints": fingerprints,
            "runtime": runtime_snapshot(),
            "git": git_snapshot(self.project_root),
            "model": current_model,
            "code": current_code,
            "sources": current_sources,
            "counts": empty_counts(len(cases)),
            "elapsed_seconds": 0.0,
        }
        atomic_write_json(self.manifest_path, manifest)
        self.write_progress(cases, {}, status="running", last_case_id="")
        return manifest

    def load_results(self) -> dict[str, FeedbackCaseResult]:
        candidates: dict[str, tuple[float, Path]] = {}
        for directory in (self.completed_dir, self.errors_dir):
            if not directory.is_dir():
                continue
            for path in directory.glob("*.json"):
                current = candidates.get(path.stem)
                modified = path.stat().st_mtime
                if current is None or modified > current[0]:
                    candidates[path.stem] = (modified, path)

        results: dict[str, FeedbackCaseResult] = {}
        for _, path in sorted(candidates.values(), key=lambda item: item[1].name):
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("campaign_id") != self.campaign_id:
                raise FeedbackCampaignError(
                    f"Persisted result belongs to another campaign: {path}"
                )
            raw_result = payload.get("result")
            if not isinstance(raw_result, dict):
                raise FeedbackCampaignError(f"Invalid persisted result: {path}")
            result = FeedbackCaseResult.from_dict(raw_result)
            results[result.case.id] = result
        return results

    def save_result(self, result: FeedbackCaseResult) -> Path:
        has_error = result_has_execution_error(result)
        target_dir = self.errors_dir if has_error else self.completed_dir
        opposite_dir = self.completed_dir if has_error else self.errors_dir
        filename = safe_name(result.case.id) + ".json"
        target = target_dir / filename
        envelope = {
            "schema_version": RESULT_SCHEMA_VERSION,
            "artifact_purpose": "evaluation",
            "training_allowed": False,
            "automatic_learning": False,
            "automatic_promotion": False,
            "campaign_id": self.campaign_id,
            "saved_at": now_iso(),
            "result": result.to_dict(),
        }
        atomic_write_json(target, envelope)
        opposite = opposite_dir / filename
        if opposite.exists():
            opposite.unlink()
        return target

    def checkpoint(
        self,
        *,
        cases: list[FeedbackCase],
        results_by_id: dict[str, FeedbackCaseResult],
        status: str,
        session_elapsed: float,
        last_case_id: str,
    ) -> dict[str, Any]:
        ordered_results = [
            results_by_id[case.id] for case in cases if case.id in results_by_id
        ]
        manifest = self._load_manifest()
        previous_elapsed = float(manifest.get("elapsed_seconds", 0.0))
        manifest["status"] = status
        manifest["updated_at"] = now_iso()
        manifest["finished_at"] = now_iso() if status == "completed" else ""
        manifest["elapsed_seconds"] = round(previous_elapsed + session_elapsed, 6)
        manifest["counts"] = campaign_counts(cases, ordered_results)
        atomic_write_json(self.manifest_path, manifest)

        metadata = {
            "campaign_id": self.campaign_id,
            "created_at": manifest.get("created_at", ""),
            "updated_at": manifest.get("updated_at", ""),
            "status": status,
            "python": manifest.get("runtime", {}).get("python", ""),
            "platform": manifest.get("runtime", {}).get("platform", ""),
            "model": manifest.get("model", {}).get("name", ""),
            "temperature": manifest.get("model", {}).get("temperature", 0),
            "artifact_purpose": "evaluation",
            "training_allowed": False,
            "automatic_learning": False,
            "automatic_promotion": False,
            "authority_notice": (
                "Community text supplies scenarios only; current CR, Oracle and rulings remain authoritative."
            ),
        }
        write_feedback_reports(ordered_results, self.output_dir, metadata)
        atomic_write_json(
            self.output_dir / "findings_by_family.json",
            build_findings_by_family(ordered_results),
        )
        atomic_write_text(
            self.output_dir / "replay_commands.txt",
            build_replay_commands(
                ordered_results,
                input_path=self.input_path,
                campaign_id=self.campaign_id,
            ),
        )
        self.write_progress(
            cases,
            results_by_id,
            status=status,
            last_case_id=last_case_id,
        )
        return manifest

    def write_progress(
        self,
        cases: list[FeedbackCase],
        results_by_id: dict[str, FeedbackCaseResult],
        *,
        status: str,
        last_case_id: str,
    ) -> None:
        ordered_results = [
            results_by_id[case.id] for case in cases if case.id in results_by_id
        ]
        processed = set(results_by_id)
        payload = {
            "schema_version": CAMPAIGN_SCHEMA_VERSION,
            "artifact_purpose": "evaluation",
            "training_allowed": False,
            "automatic_learning": False,
            "automatic_promotion": False,
            "campaign_id": self.campaign_id,
            "status": status,
            "updated_at": now_iso(),
            "last_case_id": last_case_id,
            "counts": campaign_counts(cases, ordered_results),
            "completed_case_ids": [case.id for case in cases if case.id in processed],
            "pending_case_ids": [case.id for case in cases if case.id not in processed],
        }
        atomic_write_json(self.progress_path, payload)

    def _ensure_directories(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.completed_dir.mkdir(parents=True, exist_ok=True)
        self.errors_dir.mkdir(parents=True, exist_ok=True)

    def _load_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.is_file():
            raise FeedbackCampaignError(
                f"Campaign manifest not found for resume: {self.manifest_path}"
            )
        payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise FeedbackCampaignError(f"Invalid campaign manifest: {self.manifest_path}")
        return payload

    def _validate_manifest(
        self,
        manifest: dict[str, Any],
        fingerprints: dict[str, str],
        *,
        current_sources: dict[str, dict[str, Any]],
        current_model: dict[str, Any],
        current_code: dict[str, Any],
    ) -> None:
        if manifest.get("campaign_id") != self.campaign_id:
            raise FeedbackCampaignError("Campaign id does not match existing manifest.")
        if manifest.get("artifact_purpose") != "evaluation":
            raise FeedbackCampaignError("Only evaluation campaigns can be resumed.")
        for key in ("training_allowed", "automatic_learning", "automatic_promotion"):
            if manifest.get(key) is not False:
                raise FeedbackCampaignError(
                    f"Unsafe campaign manifest: {key} must remain false."
                )
        if manifest.get("case_fingerprints") != fingerprints:
            raise FeedbackCampaignError(
                "The selected cases changed since the campaign was created. "
                "Start a new campaign id instead of mixing definitions."
            )
        if manifest.get("model") != current_model:
            raise FeedbackCampaignError(
                "The configured model or Ollama endpoint changed. "
                "Start a new campaign id to preserve reproducibility."
            )
        if manifest.get("sources") != current_sources:
            raise FeedbackCampaignError(
                "One or more authority source snapshots changed. "
                "Start a new campaign id instead of mixing source versions."
            )
        if manifest.get("code") != current_code:
            raise FeedbackCampaignError(
                "The Judge or campaign code changed. "
                "Start a new campaign id instead of mixing implementations."
            )


def execute_feedback_campaign(
    cases: list[FeedbackCase],
    *,
    store: FeedbackCampaignStore,
    resume: bool = False,
    retry_errors: bool = False,
    checkpoint_every: int = 1,
    assistant_factory: Callable[[], MagicAI] = MagicAI,
    on_case_complete: Callable[[FeedbackCaseResult, int, int, bool], None] | None = None,
) -> FeedbackCampaignRun:
    if checkpoint_every < 1:
        raise FeedbackCampaignError("checkpoint_every must be at least 1.")
    ensure_unique_case_ids(cases)
    store.prepare(cases, resume=resume)
    results_by_id = store.load_results() if resume else {}

    pending: list[FeedbackCase] = []
    for case in cases:
        persisted = results_by_id.get(case.id)
        if persisted is None:
            pending.append(case)
        elif retry_errors and result_has_execution_error(persisted):
            pending.append(case)

    session_started = time.perf_counter()
    checkpoint_started = session_started
    since_checkpoint = 0
    last_case_id = ""

    try:
        for index, case in enumerate(pending, start=1):
            result = run_feedback_case(case, assistant_factory)
            store.save_result(result)
            results_by_id[case.id] = result
            last_case_id = case.id
            since_checkpoint += 1
            store.write_progress(
                cases,
                results_by_id,
                status="running",
                last_case_id=last_case_id,
            )
            if on_case_complete is not None:
                on_case_complete(result, index, len(pending), False)

            if since_checkpoint >= checkpoint_every:
                now = time.perf_counter()
                store.checkpoint(
                    cases=cases,
                    results_by_id=results_by_id,
                    status="running",
                    session_elapsed=now - checkpoint_started,
                    last_case_id=last_case_id,
                )
                checkpoint_started = now
                since_checkpoint = 0
    except KeyboardInterrupt:
        now = time.perf_counter()
        manifest = store.checkpoint(
            cases=cases,
            results_by_id=results_by_id,
            status="interrupted",
            session_elapsed=now - checkpoint_started,
            last_case_id=last_case_id,
        )
        ordered = [results_by_id[case.id] for case in cases if case.id in results_by_id]
        return FeedbackCampaignRun(
            results=ordered,
            output_dir=store.output_dir,
            manifest=manifest,
            interrupted=True,
        )

    now = time.perf_counter()
    manifest = store.checkpoint(
        cases=cases,
        results_by_id=results_by_id,
        status="completed",
        session_elapsed=now - checkpoint_started,
        last_case_id=last_case_id,
    )
    ordered = [results_by_id[case.id] for case in cases if case.id in results_by_id]
    return FeedbackCampaignRun(
        results=ordered,
        output_dir=store.output_dir,
        manifest=manifest,
        interrupted=False,
    )


def validate_campaign_id(value: str) -> str:
    normalized = str(value).strip()
    if not CAMPAIGN_ID_PATTERN.fullmatch(normalized):
        raise FeedbackCampaignError(
            "campaign_id must contain only letters, numbers, dot, underscore or hyphen "
            "and be at most 128 characters."
        )
    return normalized


def ensure_unique_case_ids(cases: list[FeedbackCase]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for case in cases:
        if case.id in seen:
            duplicates.add(case.id)
        seen.add(case.id)
    if duplicates:
        raise FeedbackCampaignError(
            "Duplicate community feedback case ids: " + ", ".join(sorted(duplicates))
        )


def case_fingerprints(cases: list[FeedbackCase]) -> dict[str, str]:
    return {case.id: case_fingerprint(case) for case in cases}


def case_fingerprint(case: FeedbackCase) -> str:
    payload = normalize_json_value(asdict(case))
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def normalize_json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): normalize_json_value(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize_json_value(child) for child in value]
    return value


def result_has_execution_error(result: FeedbackCaseResult) -> bool:
    return any(
        turn.outcome is FeedbackOutcome.EXECUTION_ERROR or bool(turn.exception)
        for turn in result.turns
    )


def campaign_counts(
    cases: list[FeedbackCase],
    results: list[FeedbackCaseResult],
) -> dict[str, Any]:
    turns = [turn for result in results for turn in result.turns]
    errors = sum(result_has_execution_error(result) for result in results)
    outcomes: dict[str, int] = {}
    families: dict[str, int] = {}
    for turn in turns:
        outcomes[turn.outcome.value] = outcomes.get(turn.outcome.value, 0) + 1
        families[turn.failure_family.value] = families.get(turn.failure_family.value, 0) + 1
    return {
        "total_cases": len(cases),
        "processed_cases": len(results),
        "successful_cases": len(results) - errors,
        "execution_error_cases": errors,
        "pending_cases": max(0, len(cases) - len(results)),
        "turns": len(turns),
        "review_required": sum(
            turn.outcome is FeedbackOutcome.REVIEW_REQUIRED for turn in turns
        ),
        "outcomes": dict(sorted(outcomes.items())),
        "failure_families": dict(sorted(families.items())),
    }


def empty_counts(total_cases: int) -> dict[str, Any]:
    return {
        "total_cases": total_cases,
        "processed_cases": 0,
        "successful_cases": 0,
        "execution_error_cases": 0,
        "pending_cases": total_cases,
        "turns": 0,
        "review_required": 0,
        "outcomes": {},
        "failure_families": {},
    }


def runtime_snapshot() -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
    }


def model_snapshot() -> dict[str, Any]:
    return {
        "name": os.environ.get("MAGICAI_MODEL", "qwen3:8b"),
        "temperature": 0,
        "ollama_url": os.environ.get(
            "OLLAMA_URL", "http://127.0.0.1:11434/api/chat"
        ),
    }


def code_snapshot(project_root: Path) -> dict[str, Any]:
    patterns = (
        "magicai/**/*.py",
        "magicai/**/*.md",
        "tests/quality/community_feedback/**/*.py",
        "tests/quality/open_judge/**/*.py",
    )
    paths: set[Path] = set()
    for pattern in patterns:
        paths.update(path for path in project_root.glob(pattern) if path.is_file())
    for relative in ("pyproject.toml", "requirements.txt", "requirements.lock.txt"):
        path = project_root / relative
        if path.is_file():
            paths.add(path)

    digest = hashlib.sha256()
    ordered = sorted(paths, key=lambda path: str(path.relative_to(project_root)))
    for path in ordered:
        relative = str(path.relative_to(project_root)).replace("\\", "/")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\0")
    return {
        "sha256": digest.hexdigest(),
        "files": len(ordered),
    }


def git_snapshot(project_root: Path) -> dict[str, Any]:
    def run(*args: str) -> str:
        try:
            completed = subprocess.run(
                ["git", *args],
                cwd=project_root,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=10,
            )
            return completed.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""

    commit = run("rev-parse", "HEAD")
    branch = run("branch", "--show-current")
    status = run("status", "--porcelain")
    return {
        "commit": commit or "unavailable",
        "branch": branch or "unavailable",
        "dirty": bool(status),
    }


def source_snapshots(
    project_root: Path,
    *,
    include_hashes: bool,
) -> dict[str, dict[str, Any]]:
    snapshots: dict[str, dict[str, Any]] = {}
    for relative in SOURCE_SNAPSHOT_PATHS:
        path = project_root / relative
        item: dict[str, Any] = {
            "path": str(relative),
            "exists": path.is_file(),
            "size_bytes": path.stat().st_size if path.is_file() else 0,
            "sha256": "",
        }
        if path.is_file() and include_hashes:
            item["sha256"] = sha256_file(path)
        snapshots[str(relative)] = item
    return snapshots


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_replay_commands(
    results: list[FeedbackCaseResult],
    *,
    input_path: Path,
    campaign_id: str,
) -> str:
    lines = [
        "# MagicAI Community Feedback replay commands",
        "# Evaluation only. These commands do not train or modify model weights.",
        "",
    ]
    interesting = [
        result
        for result in results
        if any(
            turn.failure_family is not FeedbackFailureFamily.NO_FAILURE
            for turn in result.turns
        )
    ]
    if not interesting:
        lines.append("# No review or failure cases were recorded.")
    for result in interesting:
        replay_id = safe_name(f"{campaign_id}-replay-{result.case.id}")[:128]
        command = [
            "PYTHONPATH=.",
            "python",
            "-m",
            "tests.quality.community_feedback_test",
            "--input",
            str(input_path),
            "--case",
            result.case.id,
            "--campaign-id",
            replay_id,
        ]
        lines.append(" ".join(shlex.quote(part) for part in command))
    return "\n".join(lines).rstrip() + "\n"


def atomic_write_json(path: Path, payload: Any) -> None:
    atomic_write_text(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def safe_name(value: str) -> str:
    cleaned = "".join(
        character if character.isalnum() or character in "-_" else "_"
        for character in value
    )
    return cleaned.strip("_") or datetime.now().strftime("feedback_%Y%m%d_%H%M%S")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()
