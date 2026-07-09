import re


TRIGGERED_PATTERN = re.compile(
    r"\b(when|whenever|at)\b",
    flags=re.IGNORECASE,
)


def build_oracle_rule_queries(oracle_text: str) -> list[str]:

    if not oracle_text:

        return []

    queries = []

    for line in oracle_text.splitlines():

        line = line.strip()

        if not line:

            continue

        if _looks_like_activated_ability(line):

            _add_unique(
                queries,
                "activated ability",
            )

            if "add " in line.lower():

                _add_unique(
                    queries,
                    "mana ability",
                )

        if _looks_like_triggered_ability(line):

            _add_unique(
                queries,
                "triggered ability",
            )

    return queries


def _looks_like_activated_ability(line: str) -> bool:

    if ":" not in line:

        return False

    left, _, right = line.partition(":")

    return bool(
        left.strip()
        and right.strip()
    )


def _looks_like_triggered_ability(line: str) -> bool:

    return TRIGGERED_PATTERN.search(line) is not None


def _add_unique(items: list[str], item: str):

    if item and item not in items:

        items.append(item)
