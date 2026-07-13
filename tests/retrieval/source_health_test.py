import json
from pathlib import Path
from tempfile import TemporaryDirectory

from magicai.sources.health import get_source_health


def _write_sources(root: Path, *, include_optional: bool = True) -> None:
    (root / "scryfall").mkdir(parents=True, exist_ok=True)
    (root / "rules").mkdir(parents=True, exist_ok=True)

    (root / "scryfall" / "oracle-cards.json").write_text(
        json.dumps([{"name": "Young Wolf"}]),
        encoding="utf-8",
    )
    (root / "rules" / "MagicCompRules.txt").write_text(
        "Magic: The Gathering Comprehensive Rules\n",
        encoding="utf-8",
    )

    if include_optional:
        (root / "scryfall" / "symbology.json").write_text(
            json.dumps({"data": []}),
            encoding="utf-8",
        )
        (root / "scryfall" / "rulings.json").write_text(
            json.dumps([]),
            encoding="utf-8",
        )


def test_complete_source_set_is_ready() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        _write_sources(root)

        health = get_source_health(root)

        assert health.status == "ready"
        assert health.ready is True
        assert health.complete is True
        assert health.sources["scryfall_oracle"].available is True


def test_missing_optional_source_is_degraded_but_ready() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        _write_sources(root, include_optional=False)

        health = get_source_health(root)

        assert health.status == "degraded"
        assert health.ready is True
        assert health.complete is False
        assert health.sources["scryfall_rulings"].required is False


def test_missing_required_source_is_unavailable() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        _write_sources(root)
        (root / "scryfall" / "oracle-cards.json").unlink()

        health = get_source_health(root)

        assert health.status == "unavailable"
        assert health.ready is False


def test_truncated_json_is_invalid() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        _write_sources(root)
        (root / "scryfall" / "oracle-cards.json").write_text(
            '[{"name":"Young Wolf"}',
            encoding="utf-8",
        )

        health = get_source_health(root)

        assert health.status == "unavailable"
        assert health.sources["scryfall_oracle"].status == "invalid"


def main() -> int:
    tests = [
        test_complete_source_set_is_ready,
        test_missing_optional_source_is_degraded_but_ready,
        test_missing_required_source_is_unavailable,
        test_truncated_json_is_invalid,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Source health tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
