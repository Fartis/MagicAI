import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RULES_FILE = (
    PROJECT_ROOT /
    "sources" /
    "rules" /
    "MagicCompRules.txt"
)


TOP_LEVEL_RE = re.compile(
    r"^(\d+)\.\s+(.+)$"
)

SECTION_RE = re.compile(
    r"^(\d+\.\d+)\.\s+(.+)$"
)

SUBRULE_RE = re.compile(
    r"^(\d+\.\d+[a-z])\s+(.*)$"
)


def parse_rules():

    data = {}

    with open(RULES_FILE, encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            top_level = TOP_LEVEL_RE.match(line)

            if top_level:

                number = top_level.group(1)
                title = top_level.group(2)

                data[number] = {
                    "number": number,
                    "title": title,
                    "rules": [],
                }

                continue

            section = SECTION_RE.match(line)

            if section:

                number = section.group(1)
                text = section.group(2)

                top_number = _top_number(number)

                if top_number in data:

                    data[top_number]["rules"].append(
                        (
                            number,
                            text,
                        )
                    )

                data[number] = {
                    "number": number,
                    "title": text,
                    "rules": [],
                }

                continue

            subrule = SUBRULE_RE.match(line)

            if subrule:

                number = subrule.group(1)
                text = subrule.group(2)

                parent_number = _parent_number(number)
                top_number = _top_number(number)

                if top_number in data:

                    data[top_number]["rules"].append(
                        (
                            number,
                            text,
                        )
                    )

                if parent_number in data:

                    data[parent_number]["rules"].append(
                        (
                            number,
                            text,
                        )
                    )

                data[number] = {
                    "number": number,
                    "title": text,
                    "rules": [],
                }

    return data


def _top_number(rule_number: str) -> str:

    return rule_number.split(".")[0]


def _parent_number(rule_number: str) -> str:

    return rule_number[:-1]