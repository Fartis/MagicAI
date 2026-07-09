import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

SYMBOLS_FILE = (
    PROJECT_ROOT
    / "sources"
    / "scryfall"
    / "symbology.json"
)

_symbols_by_code = None


SYMBOL_PATTERN = re.compile(
    r"\{[^}]+\}"
)


def load_symbols() -> dict[str, dict]:

    global _symbols_by_code

    if _symbols_by_code is not None:

        return _symbols_by_code

    if not SYMBOLS_FILE.exists():

        _symbols_by_code = {}

        return _symbols_by_code

    payload = json.loads(
        SYMBOLS_FILE.read_text(
            encoding="utf-8",
        )
    )

    _symbols_by_code = {
        item["symbol"]: item
        for item in payload.get("data", [])
        if "symbol" in item
    }

    return _symbols_by_code


def extract_symbols_from_text(text: str) -> list[dict]:

    if not text:

        return []

    symbols = load_symbols()

    found = []

    for code in SYMBOL_PATTERN.findall(text):

        symbol = symbols.get(code)

        if symbol is None:

            symbol = {
                "symbol": code,
                "english": "",
            }

        _add_unique_symbol(
            found,
            symbol,
        )

    return found


def extract_symbols_from_card(card) -> list[dict]:

    parts = [
        getattr(card, "mana_cost", "") or "",
        getattr(card, "oracle_text", "") or "",
    ]

    found = []

    for part in parts:

        for symbol in extract_symbols_from_text(part):

            _add_unique_symbol(
                found,
                symbol,
            )

    return found


def _add_unique_symbol(items: list[dict], symbol: dict):

    code = symbol.get("symbol")

    for item in items:

        if item.get("symbol") == code:

            return

    items.append(symbol)