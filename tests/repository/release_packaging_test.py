from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "package_release.py"


def load_packager():
    spec = importlib.util.spec_from_file_location("magicai_package_release", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run(*arguments: str, cwd: Path) -> None:
    subprocess.run(arguments, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def build_fixture(root: Path) -> None:
    (root / "magicai").mkdir(parents=True)
    (root / "sources" / "scryfall").mkdir(parents=True)
    (root / "logs").mkdir(parents=True)

    shutil.copy2(ROOT / "magicai" / "versioning.py", root / "magicai" / "versioning.py")
    shutil.copy2(ROOT / "pyproject.toml", root / "pyproject.toml")
    (root / "README.md").write_text("tracked\n", encoding="utf-8")
    (root / "tracked.txt").write_text("tracked content\n", encoding="utf-8")
    (root / "private.txt").write_text("untracked private content\n", encoding="utf-8")
    (root / "logs" / "tracked.log").write_text("must not ship\n", encoding="utf-8")
    (root / "sources" / "scryfall" / "symbology.json").write_text("{}\n", encoding="utf-8")
    (root / "sources" / "scryfall" / "oracle-cards.json").write_text("[{\"name\":\"A\"}]\n", encoding="utf-8")
    (root / "sources" / "scryfall" / "rulings.json").write_text("[]\n", encoding="utf-8")

    run("git", "init", "-q", cwd=root)
    run("git", "config", "user.name", "MagicAI Test", cwd=root)
    run("git", "config", "user.email", "test@example.invalid", cwd=root)
    run(
        "git",
        "add",
        "README.md",
        "tracked.txt",
        "logs/tracked.log",
        "pyproject.toml",
        "magicai/versioning.py",
        "sources/scryfall/symbology.json",
        cwd=root,
    )
    run("git", "commit", "-q", "-m", "fixture", cwd=root)


def archive_names(path: Path) -> set[str]:
    with zipfile.ZipFile(path) as archive:
        return set(archive.namelist())


def test_source_and_full_packages_are_clean_and_deterministic() -> None:
    packager = load_packager()
    with tempfile.TemporaryDirectory(prefix="magicai-package-test-") as directory:
        repo = Path(directory) / "repo"
        repo.mkdir()
        build_fixture(repo)

        first = Path(directory) / "first"
        second = Path(directory) / "second"
        source_a = packager.build_archive(repo=repo, mode="source", output_dir=first, force=False)
        source_b = packager.build_archive(repo=repo, mode="source", output_dir=second, force=False)
        full = packager.build_archive(repo=repo, mode="full", output_dir=first, force=False)

        source_root = "MagicAI-v0.1.1-beta-source/"
        full_root = "MagicAI-v0.1.1-beta-full/"
        source_names = archive_names(source_a)
        full_names = archive_names(full)

        assert source_root + "README.md" in source_names
        assert source_root + "tracked.txt" in source_names
        assert source_root + "sources/scryfall/symbology.json" in source_names
        assert source_root + "INFO.txt" in source_names
        assert source_root + "PACKAGE_MANIFEST.json" in source_names
        assert source_root + "private.txt" not in source_names
        assert source_root + "logs/tracked.log" not in source_names
        assert source_root + "sources/scryfall/oracle-cards.json" not in source_names
        assert source_root + "sources/scryfall/rulings.json" not in source_names

        assert full_root + "sources/scryfall/oracle-cards.json" in full_names
        assert full_root + "sources/scryfall/rulings.json" in full_names
        assert source_a.read_bytes() == source_b.read_bytes()

        (repo / "tracked.txt").write_text("modified\n", encoding="utf-8")
        try:
            packager.build_archive(
                repo=repo,
                mode="source",
                output_dir=Path(directory) / "dirty",
                force=False,
            )
        except RuntimeError as error:
            assert "Tracked files are modified" in str(error)
        else:
            raise AssertionError("Dirty tracked files must be rejected by default")


def main() -> int:
    test_source_and_full_packages_are_clean_and_deterministic()
    print("OK: test_source_and_full_packages_are_clean_and_deterministic")
    print("Release packaging tests: 1/1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
