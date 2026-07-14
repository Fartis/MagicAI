from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache

from magicai.rules_parser import parse_rules


@dataclass(frozen=True, slots=True)
class _IndexedSection:
    section: dict
    number: str
    title: str
    body: str
    whole: str
    title_bag: dict[str, int]
    body_bag: dict[str, int]
    whole_bag: dict[str, int]
    token_count: int


_rules: dict[str, dict] | None = None
_index: tuple[_IndexedSection, ...] | None = None
_doc_frequency: dict[str, int] = {}
_postings: dict[str, tuple[int, ...]] = {}
_index_builds = 0


def load() -> dict[str, dict]:
    global _rules
    if _rules is None:
        _rules = parse_rules()
    return _rules


def warm_rule_index() -> dict[str, int]:
    _ensure_index()
    return {
        "sections": len(_index or ()),
        "terms": len(_doc_frequency),
        "builds": _index_builds,
    }


def clear_rule_caches(*, reset_index: bool = False) -> None:
    global _index, _doc_frequency, _postings, _index_builds
    _find_rule_cached.cache_clear()
    _search_rules_cached.cache_clear()
    if reset_index:
        _index = None
        _doc_frequency = {}
        _postings = {}
        _index_builds = 0


def rule_search_cache_info() -> dict[str, object]:
    return {
        "find_rule": _find_rule_cached.cache_info()._asdict(),
        "search_rules": _search_rules_cached.cache_info()._asdict(),
        "index": warm_rule_index(),
    }


def find_rule(query: str):
    normalized = _normalize_query(query)
    if not normalized:
        return None
    return _find_rule_cached(normalized)


@lru_cache(maxsize=4096)
def _find_rule_cached(query: str):
    rules = load()
    if query in rules:
        return rules[query]
    index = _ensure_index()
    for item in index:
        if query == item.title:
            return item.section
    for item in index:
        if query in item.title:
            return item.section
    for item in index:
        for rule_number, text in item.section.get("rules", []):
            if query == rule_number.casefold() or query in text.casefold():
                return item.section
    return None


def search_rules(query: str, limit: int = 5):
    normalized = _normalize_query(query)
    if not normalized or limit <= 0:
        return []
    return list(_search_rules_cached(normalized, int(limit)))


@lru_cache(maxsize=8192)
def _search_rules_cached(query: str, limit: int) -> tuple[dict, ...]:
    tokens = _tokenize(query)
    if not tokens:
        return ()
    rules = load()
    if query in rules:
        return (rules[query],)
    index = _ensure_index()
    total = len(index)
    idf = {
        token: math.log((1 + total) / (1 + _doc_frequency.get(token, 0))) + 1.0
        for token in tokens
    }
    candidate_indexes: set[int] = set()
    for token in tokens:
        candidate_indexes.update(_postings.get(token, ()))
    query_phrases = _phrases(query)
    important_phrases = _important_magic_phrases(query)
    scored: list[tuple[float, dict]] = []
    for item_index in candidate_indexes:
        item = index[item_index]
        score = _score_section(
            tokens=tokens,
            idf=idf,
            item=item,
            original_query=query,
            query_phrases=query_phrases,
            important_phrases=important_phrases,
        )
        if score > 0:
            scored.append((score, item.section))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    ranked = _remove_redundant_lower_ranked_sections(
        [section for _score, section in scored]
    )
    return tuple(ranked[:limit])


def _ensure_index() -> tuple[_IndexedSection, ...]:
    global _index, _doc_frequency, _postings, _index_builds
    if _index is not None:
        return _index
    built: list[_IndexedSection] = []
    document_frequency: Counter[str] = Counter()
    posting_lists: dict[str, list[int]] = {}
    for section in load().values():
        number = str(section.get("number", "")).casefold()
        title = str(section.get("title", "")).casefold()
        body = _rules_text(section).casefold()
        whole = f"{number}\n{title}\n{body}".casefold()
        title_bag = _token_bag(title)
        body_bag = _token_bag(body)
        whole_bag = _token_bag(whole)
        document_frequency.update(whole_bag.keys())
        section_index = len(built)
        for token in whole_bag:
            posting_lists.setdefault(token, []).append(section_index)
        built.append(
            _IndexedSection(
                section=section,
                number=number,
                title=title,
                body=body,
                whole=whole,
                title_bag=title_bag,
                body_bag=body_bag,
                whole_bag=whole_bag,
                token_count=max(1, sum(whole_bag.values())),
            )
        )
    _index = tuple(built)
    _doc_frequency = dict(document_frequency)
    _postings = {token: tuple(items) for token, items in posting_lists.items()}
    _index_builds += 1
    return _index


def _score_section(
    *,
    tokens: list[str],
    idf: dict[str, float],
    item: _IndexedSection,
    original_query: str,
    query_phrases: list[str],
    important_phrases: list[str],
) -> float:
    matched = [token for token in tokens if token in item.whole_bag]
    if not matched:
        return 0.0
    coverage = len(matched) / len(tokens)
    title_hits = sum(1 for token in tokens if token in item.title_bag)
    body_hits = sum(1 for token in tokens if token in item.body_bag)
    score = 100000.0 if original_query == item.number else 0.0
    for token in tokens:
        score += 12.0 * idf[token] * min(item.title_bag.get(token, 0), 4)
        score += 2.0 * idf[token] * min(item.body_bag.get(token, 0), 8)
    score += (coverage * coverage) * 120.0
    score += title_hits * 90.0
    score += body_hits * 15.0
    if all(token in item.title_bag for token in tokens):
        score += 700.0
    if _is_top_level(item.number):
        if title_hits and coverage >= 0.60:
            score += 500.0
        elif title_hits >= 2:
            score += 350.0
        elif coverage < 0.75:
            score *= 0.30
    elif coverage < 0.40:
        score *= 0.20
    for phrase in query_phrases:
        if phrase in item.title:
            score += 400.0
        elif phrase in item.body:
            score += 160.0
    important_phrase_hits = 0
    for phrase in important_phrases:
        if phrase in item.title:
            score += 600.0
            important_phrase_hits += 1
        elif phrase in item.body:
            score += 300.0
            important_phrase_hits += 1
    if _is_top_level(item.number) and title_hits == 0 and important_phrase_hits == 0:
        score *= 0.03
    return score / math.log(item.token_count + 10)


def _important_magic_phrases(query: str) -> list[str]:
    q = query.casefold()
    phrases: list[str] = []
    if "power" in q and "toughness" in q:
        phrases.extend([
            "power and/or toughness", "set power and/or toughness",
            "modify power and/or toughness", "specific number or value",
            "base power and/or toughness",
        ])
    if "priority" in q:
        phrases.extend(["timing and priority", "player with priority", "receives priority"])
    if "layers" in q or "continuous effects" in q:
        phrases.extend(["series of layers", "continuous effects", "interaction of continuous effects"])
    if "in response" in q or "resolves" in q:
        phrases.extend(["in response to", "will resolve first", "all players pass"])
    return phrases


def _remove_redundant_lower_ranked_sections(sections: list[dict]) -> list[dict]:
    result: list[dict] = []
    for section in sections:
        number = str(section.get("number", ""))
        if _has_better_parent(number, result):
            continue
        result.append(section)
    return result


def _has_better_parent(number: str, sections: list[dict]) -> bool:
    for section in sections:
        parent = str(section.get("number", ""))
        if parent != number and _is_parent_rule(parent, number):
            return True
    return False


def _is_parent_rule(parent: str, child: str) -> bool:
    if not parent or not child:
        return False
    return child.startswith(parent + ".") if "." not in parent else child.startswith(parent)


def _is_top_level(number: str) -> bool:
    return "." not in number


def _rules_text(section: dict) -> str:
    parts: list[str] = []
    for rule_number, text in section.get("rules", []):
        parts.extend((str(rule_number), str(text)))
    return "\n".join(parts)


def _token_bag(text: str) -> dict[str, int]:
    bag: dict[str, int] = {}
    for token in re.findall(r"[a-z0-9/+_-]+", text.casefold()):
        bag[token] = bag.get(token, 0) + 1
    return bag


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(
        r"(?<![a-z0-9/+_-])" + re.escape(phrase) + r"(?![a-z0-9/+_-])",
        text,
    ) is not None


def _phrases(query: str) -> list[str]:
    return [
        chunk.strip()
        for chunk in re.split(r"[,;]", query.casefold())
        if " " in chunk.strip() and len(chunk.strip()) >= 5
    ]


def _tokenize(query: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9/+_-]{2,}", query.casefold())
    stopwords = {
        "the", "and", "for", "with", "from", "that", "this", "what",
        "when", "where", "into", "onto", "que", "qué", "con", "una",
        "uno", "por", "para", "antes", "despues", "después", "como", "cómo",
    }
    result: list[str] = []
    for token in tokens:
        if token not in stopwords and token not in result:
            result.append(token)
    return result


def _normalize_query(query: str) -> str:
    return re.sub(r"\s+", " ", (query or "").strip().casefold())
