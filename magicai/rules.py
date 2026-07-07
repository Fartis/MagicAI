from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RULES_FILE = (
    PROJECT_ROOT /
    "sources" /
    "rules" /
    "MagicCompRules.txt"
)


_rules = None


def load_rules():

    global _rules

    if _rules is None:

        with open(RULES_FILE, encoding="utf-8") as f:
            _rules = f.read()

    return _rules