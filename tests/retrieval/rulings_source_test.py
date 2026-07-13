from __future__ import annotations

import json
import tempfile
from pathlib import Path

from magicai.sources.rulings import find_rulings_by_oracle_id
from magicai.sources.versions import get_source_versions


def test_local_rulings_are_indexed_and_sorted() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        target = root / "scryfall" / "rulings.json"
        target.parent.mkdir(parents=True)
        target.write_text(
            json.dumps(
                [
                    {
                        "oracle_id": "oracle-1",
                        "source": "wotc",
                        "published_at": "2020-01-01",
                        "comment": "Older ruling.",
                    },
                    {
                        "oracle_id": "oracle-1",
                        "source": "wotc",
                        "published_at": "2024-01-01",
                        "comment": "Newer ruling.",
                    },
                    {
                        "oracle_id": "oracle-2",
                        "source": "scryfall",
                        "published_at": "2023-01-01",
                        "comment": "Other card.",
                    },
                ]
            ),
            encoding="utf-8",
        )

        rulings = find_rulings_by_oracle_id(
            "oracle-1",
            source_root=root,
        )
        versions = get_source_versions(root)

    assert [item["comment"] for item in rulings] == [
        "Newer ruling.",
        "Older ruling.",
    ]
    assert rulings[0]["source"] == "wotc"
    assert "scryfall_rulings_file_mtime" in versions


def test_missing_rulings_file_is_safe() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        assert find_rulings_by_oracle_id(
            "oracle-1",
            source_root=temporary,
        ) == []


def main() -> int:
    tests = [
        test_local_rulings_are_indexed_and_sorted,
        test_missing_rulings_file_is_safe,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print(f"Rulings source tests: {len(tests)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
