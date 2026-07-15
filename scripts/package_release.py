#!/usr/bin/env python3
"""Build clean, deterministic MagicAI source and full release archives."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tomllib
import zipfile


FULL_SOURCE_FILES = (
    PurePosixPath("sources/scryfall/oracle-cards.json"),
    PurePosixPath("sources/scryfall/rulings.json"),
)

EXCLUDED_PREFIXES = (
    ".git/",
    ".venv/",
    "backups/",
    "backup/",
    "build/",
    "dist/",
    "github-analysis-",
    "htmlcov/",
    "logs/",
    "node_modules/",
    "quality-results/",
    "reports/",
    "resultado_",
    "site/",
    "test-results/",
)

EXCLUDED_PARTS = {
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}


@dataclass(frozen=True, slots=True)
class ReleaseIdentity:
    public_version: str
    package_version: str
    tag: str
    channel: str
    codename: str


@dataclass(frozen=True, slots=True)
class PackageEntry:
    relative_path: PurePosixPath
    source_path: Path
    executable: bool


def run_git(repo: Path, *arguments: str, text: bool = True) -> str | bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=text,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() if text else result.stderr.decode(errors="replace").strip()
        raise RuntimeError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout


def repository_root(configured: str | None) -> Path:
    candidate = Path(configured or Path.cwd()).expanduser().resolve()
    output = subprocess.run(
        ["git", "-C", str(candidate), "rev-parse", "--show-toplevel"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if output.returncode != 0:
        raise RuntimeError(f"{candidate} is not inside a Git repository")
    return Path(output.stdout.strip()).resolve()


def load_release_identity(repo: Path) -> ReleaseIdentity:
    module_path = repo / "magicai" / "versioning.py"
    spec = importlib.util.spec_from_file_location("magicai_release_versioning", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    pyproject = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))
    package_version = str(pyproject["project"]["version"])
    expected_package_version = str(module.PACKAGE_FALLBACK_VERSION)
    if package_version != expected_package_version:
        raise RuntimeError(
            "Version mismatch: pyproject.toml declares "
            f"{package_version!r}, but magicai/versioning.py declares "
            f"{expected_package_version!r}."
        )

    return ReleaseIdentity(
        public_version=str(module.PUBLIC_VERSION),
        package_version=package_version,
        tag=str(module.RELEASE_TAG),
        channel=str(module.RELEASE_CHANNEL),
        codename=str(module.RELEASE_CODENAME),
    )


def tracked_paths(repo: Path) -> list[PurePosixPath]:
    raw = run_git(repo, "ls-files", "-z", text=False)
    assert isinstance(raw, bytes)
    paths = []
    for value in raw.split(b"\0"):
        if not value:
            continue
        paths.append(PurePosixPath(value.decode("utf-8", errors="strict")))
    return sorted(paths, key=str)


def should_exclude(path: PurePosixPath) -> bool:
    value = path.as_posix()
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return True
    return any(value == prefix.rstrip("/") or value.startswith(prefix) for prefix in EXCLUDED_PREFIXES)


def collect_entries(repo: Path, mode: str) -> list[PackageEntry]:
    entries: dict[PurePosixPath, PackageEntry] = {}

    for relative in tracked_paths(repo):
        if should_exclude(relative):
            continue
        if mode == "source" and relative in FULL_SOURCE_FILES:
            continue
        source = repo / relative
        if not source.is_file():
            raise RuntimeError(f"Tracked file is missing from the working tree: {relative}")
        if source.is_symlink():
            raise RuntimeError(f"Release packages do not include symbolic links: {relative}")
        executable = bool(source.stat().st_mode & stat.S_IXUSR)
        entries[relative] = PackageEntry(relative, source, executable)

    if mode == "full":
        missing = [path for path in FULL_SOURCE_FILES if not (repo / path).is_file()]
        if missing:
            formatted = ", ".join(str(path) for path in missing)
            raise RuntimeError(
                "Full package requires local bulk sources. Missing: " + formatted
            )
        for relative in FULL_SOURCE_FILES:
            source = repo / relative
            entries[relative] = PackageEntry(relative, source, False)

    return [entries[path] for path in sorted(entries, key=str)]


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_epoch(repo: Path) -> int:
    configured = os.environ.get("SOURCE_DATE_EPOCH")
    if configured:
        try:
            return max(int(configured), 315532800)
        except ValueError as error:
            raise RuntimeError("SOURCE_DATE_EPOCH must be an integer") from error

    output = run_git(repo, "log", "-1", "--format=%ct")
    assert isinstance(output, str)
    return max(int(output.strip()), 315532800)


def zip_datetime(epoch: int) -> tuple[int, int, int, int, int, int]:
    value = datetime.fromtimestamp(epoch, tz=timezone.utc)
    second = value.second - (value.second % 2)
    return value.year, value.month, value.day, value.hour, value.minute, second


def git_metadata(repo: Path) -> dict[str, str]:
    commit = str(run_git(repo, "rev-parse", "HEAD")).strip()
    branch = str(run_git(repo, "branch", "--show-current")).strip() or "detached"
    status = str(run_git(repo, "status", "--porcelain", "--untracked-files=no"))
    return {
        "commit": commit,
        "branch": branch,
        "tracked_worktree": "clean" if not status.strip() else "modified",
    }


def build_metadata(
    *,
    repo: Path,
    identity: ReleaseIdentity,
    mode: str,
    entries: list[PackageEntry],
    epoch: int,
) -> tuple[bytes, bytes]:
    git_info = git_metadata(repo)
    files = []
    for entry in entries:
        files.append(
            {
                "path": entry.relative_path.as_posix(),
                "size": entry.source_path.stat().st_size,
                "sha256": sha256_file(entry.source_path),
            }
        )

    generated_at = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
    manifest = {
        "schema_version": "1.0",
        "project": "MagicAI",
        "package_mode": mode,
        "public_version": identity.public_version,
        "package_version": identity.package_version,
        "release_tag": identity.tag,
        "release_channel": identity.channel,
        "release_codename": identity.codename,
        "generated_at": generated_at,
        "git": git_info,
        "files": files,
    }
    manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    info = "\n".join(
        [
            "MagicAI release package",
            "",
            f"Public version: {identity.public_version}",
            f"Package version: {identity.package_version}",
            f"Codename: {identity.codename}",
            f"Channel: {identity.channel}",
            f"Tag: {identity.tag}",
            f"Package mode: {mode}",
            f"Git branch: {git_info['branch']}",
            f"Git commit: {git_info['commit']}",
            f"Tracked worktree: {git_info['tracked_worktree']}",
            f"Generated from commit time: {generated_at}",
            f"Packaged files: {len(entries)}",
            "",
            "See PACKAGE_MANIFEST.json for per-file SHA-256 values.",
            "",
        ]
    ).encode("utf-8")
    return info, manifest_bytes


def write_zip_entry(
    archive: zipfile.ZipFile,
    archive_name: str,
    content: bytes,
    *,
    timestamp: tuple[int, int, int, int, int, int],
    executable: bool = False,
) -> None:
    info = zipfile.ZipInfo(archive_name, date_time=timestamp)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    mode = 0o755 if executable else 0o644
    info.external_attr = (stat.S_IFREG | mode) << 16
    archive.writestr(info, content, compresslevel=9)


def build_archive(
    *,
    repo: Path,
    mode: str,
    output_dir: Path,
    force: bool,
    allow_dirty: bool = False,
) -> Path:
    identity = load_release_identity(repo)
    current_git = git_metadata(repo)
    if current_git["tracked_worktree"] != "clean" and not allow_dirty:
        raise RuntimeError(
            "Tracked files are modified. Commit or restore them before packaging, "
            "or use --allow-dirty for a diagnostic archive."
        )
    entries = collect_entries(repo, mode)
    epoch = source_epoch(repo)
    timestamp = zip_datetime(epoch)
    root_name = f"MagicAI-v{identity.public_version}-{mode}"
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / f"{root_name}.zip"
    checksum_path = archive_path.with_suffix(archive_path.suffix + ".sha256")

    if (archive_path.exists() or checksum_path.exists()) and not force:
        raise RuntimeError(
            f"Output already exists: {archive_path}. Use --force to replace it."
        )

    info_bytes, manifest_bytes = build_metadata(
        repo=repo,
        identity=identity,
        mode=mode,
        entries=entries,
        epoch=epoch,
    )

    temporary = archive_path.with_suffix(".zip.tmp")
    temporary.unlink(missing_ok=True)
    try:
        with zipfile.ZipFile(temporary, "w", allowZip64=True) as archive:
            for entry in entries:
                write_zip_entry(
                    archive,
                    f"{root_name}/{entry.relative_path.as_posix()}",
                    entry.source_path.read_bytes(),
                    timestamp=timestamp,
                    executable=entry.executable,
                )
            write_zip_entry(
                archive,
                f"{root_name}/INFO.txt",
                info_bytes,
                timestamp=timestamp,
            )
            write_zip_entry(
                archive,
                f"{root_name}/PACKAGE_MANIFEST.json",
                manifest_bytes,
                timestamp=timestamp,
            )
        temporary.replace(archive_path)
    finally:
        temporary.unlink(missing_ok=True)

    checksum = sha256_file(archive_path)
    checksum_path.write_text(f"{checksum}  {archive_path.name}\n", encoding="utf-8")
    return archive_path


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--source", action="store_true", help="Build the clean source package")
    mode.add_argument("--full", action="store_true", help="Build the full package with local bulk sources")
    parser.add_argument("--repo", help="Repository path; defaults to the current repository")
    parser.add_argument(
        "--output-dir",
        default="dist/releases",
        help="Output directory relative to the repository unless absolute",
    )
    parser.add_argument("--force", action="store_true", help="Replace an existing archive")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow packaging modified tracked files for diagnostics",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(argv or sys.argv[1:])
    try:
        repo = repository_root(arguments.repo)
        output_dir = Path(arguments.output_dir).expanduser()
        if not output_dir.is_absolute():
            output_dir = repo / output_dir
        mode = "full" if arguments.full else "source"
        archive = build_archive(
            repo=repo,
            mode=mode,
            output_dir=output_dir.resolve(),
            force=arguments.force,
            allow_dirty=arguments.allow_dirty,
        )
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    checksum_path = archive.with_suffix(archive.suffix + ".sha256")
    print(f"Created: {archive}")
    print(f"Checksum: {checksum_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
