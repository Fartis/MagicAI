import json
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_FILE = (
    PROJECT_ROOT
    / "sources"
    / "scryfall"
    / "symbology.json"
)

SCRYFALL_SYMBOLOGY_URL = "https://api.scryfall.com/symbology"


def main():

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    request = urllib.request.Request(
        SCRYFALL_SYMBOLOGY_URL,
        headers={
            "User-Agent": "MagicAI/0.1.1-beta",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:

        payload = json.loads(
            response.read().decode("utf-8")
        )

    OUTPUT_FILE.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    count = len(
        payload.get(
            "data",
            [],
        )
    )

    print(f"Wrote {OUTPUT_FILE}")
    print(f"Symbols: {count}")


if __name__ == "__main__":

    main()