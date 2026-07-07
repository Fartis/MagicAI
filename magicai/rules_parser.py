import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RULES_FILE = PROJECT_ROOT / "sources" / "rules" / "MagicCompRules.txt"


HEADER_RE = re.compile(r"^(\d+\.\d+)\.\s+(.+)$")
RULE_RE = re.compile(r"^(\d+\.\d+[a-z])\s+(.*)$")


def parse_rules():

    data = {}

    current = None

    with open(RULES_FILE, encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            header = HEADER_RE.match(line)

            if header:

                current = header.group(1)

                data[current] = {
                    "title": header.group(2),
                    "rules": []
                }

                continue

            rule = RULE_RE.match(line)

            if rule and current:

                data[current]["rules"].append(
                    (
                        rule.group(1),
                        rule.group(2)
                    )
                )

    return data