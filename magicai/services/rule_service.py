import math
import re

from magicai.rules_parser import parse_rules

_rules = None


def load():

    global _rules

    if _rules is None:

        _rules = parse_rules()

    return _rules


def find_rule(query: str):

    query = query.strip().lower()

    rules = load()

    if query in rules:

        return rules[query]

    for section in rules.values():

        title = section.get("title", "").lower()

        if query == title:

            return section

    for section in rules.values():

        title = section.get("title", "").lower()

        if query and query in title:

            return section

    for section in rules.values():

        for rule_number, text in section.get("rules", []):

            if query == rule_number.lower():

                return section

            if query and query in text.lower():

                return section

    return None


def search_rules(query: str, limit: int = 5):

    query = query.strip()

    tokens = _tokenize(query)

    if not tokens:

        return []

    rules = load()

    if query.lower() in rules:

        return [
            rules[query.lower()]
        ]

    docs = _searchable_docs()
    idf = _idf(tokens, docs)

    scored = []

    for section in docs:

        score = _score_section(
            tokens=tokens,
            idf=idf,
            section=section,
            original_query=query,
        )

        if score > 0:

            scored.append(
                (
                    score,
                    section,
                )
            )

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    ranked = [
        section
        for score, section in scored
    ]

    ranked = _remove_redundant_lower_ranked_sections(ranked)

    return ranked[:limit]


def _searchable_docs() -> list[dict]:

    return list(
        load().values()
    )


def _score_section(
    tokens: list[str],
    idf: dict[str, float],
    section: dict,
    original_query: str,
) -> float:

    number = section.get("number", "").lower()
    title = section.get("title", "").lower()
    body = _rules_text(section).lower()
    whole = _section_text(section)

    if not whole.strip():

        return 0.0

    title_bag = _token_bag(title)
    body_bag = _token_bag(body)
    whole_bag = _token_bag(whole)

    score = 0.0

    matched = [
        token
        for token in tokens
        if token in whole_bag
    ]

    if not matched:

        return 0.0

    coverage = len(matched) / len(tokens)

    title_hits = sum(
        1
        for token in tokens
        if token in title_bag
    )

    body_hits = sum(
        1
        for token in tokens
        if token in body_bag
    )

    if original_query.lower() == number:

        score += 100000.0

    for token in tokens:

        score += 12.0 * idf[token] * title_bag.get(token, 0)
        score += 2.0 * idf[token] * body_bag.get(token, 0)

    score += (coverage * coverage) * 120.0
    score += title_hits * 90.0
    score += body_hits * 15.0

    if _all_tokens_in_title(tokens, title):

        score += 700.0

    if _is_top_level(number):

        #
        # Las secciones padre no deben ganar por mencionar una palabra suelta,
        # pero sí deben ganar cuando el título y el cuerpo cubren bien el tema.
        #

        if title_hits and coverage >= 0.60:

            score += 500.0

        elif title_hits >= 2:

            score += 350.0

        elif coverage < 0.75:

            score *= 0.30

    else:

        if coverage < 0.40:

            score *= 0.20

    for phrase in _phrases(original_query):

        if _contains_phrase(title, phrase):

            score += 400.0

        elif _contains_phrase(body, phrase):

            score += 160.0

    important_phrase_hits = 0

    for phrase in _important_magic_phrases(original_query):

        if _contains_phrase(title, phrase):

            score += 600.0
            important_phrase_hits += 1

        elif _contains_phrase(body, phrase):

            score += 300.0
            important_phrase_hits += 1
            
    if _is_top_level(number) and title_hits == 0 and important_phrase_hits == 0:

        score *= 0.03

    token_count = max(
        1,
        len(re.findall(r"[a-z0-9/+_-]+", whole)),
    )

    #
    # Penalización suave por longitud.
    # Evita que un bloque gigante gane por ruido, pero permite que una sección
    # padre gane cuando tiene mucha cobertura temática.
    #

    score = score / math.log(token_count + 10)

    return score


def _important_magic_phrases(query: str) -> list[str]:

    q = query.lower()

    phrases = []

    if "power" in q and "toughness" in q:

        phrases.extend(
            [
                "power and/or toughness",
                "set power and/or toughness",
                "modify power and/or toughness",
                "specific number or value",
                "base power and/or toughness",
            ]
        )

    if "priority" in q:

        phrases.extend(
            [
                "timing and priority",
                "player with priority",
                "receives priority",
            ]
        )

    if "layers" in q or "continuous effects" in q:

        phrases.extend(
            [
                "series of layers",
                "continuous effects",
                "interaction of continuous effects",
            ]
        )

    if "in response" in q or "resolves" in q:

        phrases.extend(
            [
                "in response to",
                "will resolve first",
                "all players pass",
            ]
        )

    return phrases


def _remove_redundant_lower_ranked_sections(sections: list[dict]) -> list[dict]:

    result = []

    for section in sections:

        number = section.get("number", "")

        if _has_better_parent(number, result):

            continue

        result.append(section)

    return result


def _has_better_parent(number: str, sections: list[dict]) -> bool:

    for section in sections:

        parent = section.get("number", "")

        if parent == number:

            continue

        if _is_parent_rule(parent, number):

            return True

    return False


def _is_parent_rule(parent: str, child: str) -> bool:

    if not parent or not child:

        return False

    if "." not in parent:

        return child.startswith(parent + ".")

    return child.startswith(parent)


def _is_top_level(number: str) -> bool:

    return "." not in number


def _all_tokens_in_title(tokens: list[str], title: str) -> bool:

    if not tokens:

        return False

    title_bag = _token_bag(title)

    return all(
        token in title_bag
        for token in tokens
    )


def _idf(tokens: list[str], docs: list[dict]) -> dict[str, float]:

    total = len(docs)
    result = {}

    for token in tokens:

        containing = 0

        for section in docs:

            if token in _token_bag(_section_text(section)):

                containing += 1

        result[token] = math.log(
            (1 + total) / (1 + containing)
        ) + 1.0

    return result


def _section_text(section: dict) -> str:

    return (
        section.get("number", "")
        + "\n"
        + section.get("title", "")
        + "\n"
        + _rules_text(section)
    ).lower()


def _rules_text(section: dict) -> str:

    parts = []

    for rule_number, text in section.get("rules", []):

        parts.append(rule_number)
        parts.append(text)

    return "\n".join(parts)


def _token_bag(text: str) -> dict[str, int]:

    bag = {}

    for token in re.findall(r"[a-z0-9/+_-]+", text.lower()):

        bag[token] = bag.get(token, 0) + 1

    return bag


def _contains_phrase(text: str, phrase: str) -> bool:

    return re.search(
        r"(?<![a-z0-9/+_-])" + re.escape(phrase) + r"(?![a-z0-9/+_-])",
        text,
    ) is not None


def _phrases(query: str) -> list[str]:

    phrases = []

    for chunk in re.split(r"[,;]", query.lower()):

        chunk = chunk.strip()

        if " " in chunk and len(chunk) >= 5:

            phrases.append(chunk)

    return phrases


def _tokenize(query: str) -> list[str]:

    tokens = re.findall(
        r"[a-z0-9/+_-]{2,}",
        query.lower(),
    )

    stopwords = {
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "what",
        "when",
        "where",
        "into",
        "onto",
        "que",
        "qué",
        "con",
        "una",
        "uno",
        "por",
        "para",
        "antes",
        "despues",
        "después",
        "como",
        "cómo",
    }

    result = []

    for token in tokens:

        if token not in stopwords and token not in result:

            result.append(token)

    return result
