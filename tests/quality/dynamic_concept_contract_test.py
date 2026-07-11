from __future__ import annotations

import re

from magicai.retrieval.rule_queries import build_rule_queries
from magicai.validation.rule_renderer import render_rule_answer
from tests.quality.dynamic.concepts import CONCEPTS
from tests.quality.reddit_gauntlet_test import validate_answer


_RULE_FIXTURE = """
RULE 113. Abilities
RULE 117. Timing and Priority
RULE 122. Counters
RULE 400.7. Zone changes create new objects
RULE 405. The Stack
RULE 514. Cleanup Step
RULE 603. Handling Triggered Abilities
RULE 614. Replacement Effects
RULE 616. Interaction of Replacement Effects
RULE 700.4. Dies
RULE 702.79a. Persist
RULE 702.93a. Undying
RULE 704. State-Based Actions
RULE 704.5f. Zero toughness
RULE 704.5q. Counter cancellation
RULE 903.3. Commander designation
RULE 903.9a. Commander graveyard and exile
RULE 903.9b. Commander hand and library
""".strip()


def _knowledge(question: str) -> str:
    return f"QUESTION\n{question}\n{'=' * 80}\nRULES\n{_RULE_FIXTURE}\n"


def _knowledge_from_detected_rule_queries(question: str) -> str:
    queries = build_rule_queries(
        question=question,
        keywords=[],
        action_terms=[],
    )
    rule_numbers = [
        query
        for query in queries
        if re.fullmatch(r"\d+(?:\.\d+[a-z]?)?", query)
    ]
    rules = "\n".join(f"RULE {number}" for number in rule_numbers)
    return f"QUESTION\n{question}\n{'=' * 80}\nRULES\n{rules}\n"


def test_every_rules_only_template_routes_and_satisfies_contract():
    checked = 0

    for concept in CONCEPTS:
        if concept.selector is not None:
            continue

        for template in concept.templates:
            answer = render_rule_answer(_knowledge(template.render()))

            assert answer is not None, (
                f"No deterministic renderer matched "
                f"{concept.id}/{template.id}"
            )

            failures, warnings = validate_answer(
                answer=answer,
                required_all=list(concept.contract.required_all),
                required_any=[list(group) for group in concept.contract.required_any],
                forbidden=list(concept.contract.forbidden),
                recommended_all=list(concept.contract.recommended_all),
                recommended_any=[
                    list(group)
                    for group in concept.contract.recommended_any
                ],
                soft_forbidden=list(concept.contract.soft_forbidden),
            )

            assert not failures, (
                f"Contract failure for {concept.id}/{template.id}: "
                + "; ".join(failures)
                + f"\nANSWER: {answer}"
            )
            assert not warnings, (
                f"Contract warning for {concept.id}/{template.id}: "
                + "; ".join(warnings)
                + f"\nANSWER: {answer}"
            )
            checked += 1

    expected = sum(
        len(concept.templates)
        for concept in CONCEPTS
        if concept.selector is None
    )
    assert checked == expected
    assert checked >= 30


def test_every_rules_only_template_recovers_enough_rule_markers():
    checked = 0

    for concept in CONCEPTS:
        if concept.selector is not None:
            continue

        for template in concept.templates:
            question = template.render()
            answer = render_rule_answer(
                _knowledge_from_detected_rule_queries(question)
            )

            assert answer is not None, (
                f"Rule-query routing did not recover enough evidence for "
                f"{concept.id}/{template.id}: {question}"
            )
            checked += 1

    expected = sum(
        len(concept.templates)
        for concept in CONCEPTS
        if concept.selector is None
    )
    assert checked == expected


def main():
    test_every_rules_only_template_routes_and_satisfies_contract()
    test_every_rules_only_template_recovers_enough_rule_markers()
    template_count = sum(
        len(concept.templates)
        for concept in CONCEPTS
        if concept.selector is None
    )
    print("OK: test_every_rules_only_template_routes_and_satisfies_contract")
    print("OK: test_every_rules_only_template_recovers_enough_rule_markers")
    print()
    print("=" * 80)
    print("RESULT")
    print("=" * 80)
    print(f"Templates: {template_count}")
    print("Errors   : 0")
    print("OK")


if __name__ == "__main__":
    main()
