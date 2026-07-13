from pathlib import Path
from tempfile import TemporaryDirectory

from magicai.sources.versions import get_source_versions


def main() -> int:
    with TemporaryDirectory(prefix="magicai-source-versions-") as tmp:
        root = Path(tmp)
        rules = root / "rules"
        scryfall = root / "scryfall"
        rules.mkdir(parents=True)
        scryfall.mkdir(parents=True)

        (rules / "MagicCompRules.txt").write_text(
            "Magic rules\nThese rules are effective as of July 1, 2026.\n",
            encoding="utf-8",
        )
        (scryfall / "oracle-cards.json").write_text("[]", encoding="utf-8")

        versions = get_source_versions(root)

        assert versions["comprehensive_rules"] == "2026-07-01"
        assert "scryfall_oracle_file_mtime" in versions
        assert "scryfall_symbology_file_mtime" not in versions

    print("Source versions test: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
