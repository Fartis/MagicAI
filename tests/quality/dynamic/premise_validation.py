from __future__ import annotations

from magicai.oracle_abilities import extract_activated_abilities
from tests.quality.dynamic.models import DynamicScenario


_VALID_DEPENDENCIES = {
    "independent", "source_object", "information", "source_bound_effect", "partial"
}


def validate_dynamic_premise(scenario: DynamicScenario) -> list[str]:
    """Validate generator-owned facts before asking the Judge.

    Stored metadata is diagnostic, not authority. The exact bound ability is
    reparsed with the current Oracle parser so a stale manifest cannot turn an
    impossible premise into a Judge PASS after parser improvements.
    """

    problems: list[str] = []
    parsed = _reparse_bound_ability(scenario)

    if scenario.concept_id == "mana_ability":
        if not scenario.ability_text:
            problems.append("The mana scenario is not bound to an exact Oracle ability.")
        if parsed is None:
            problems.append("The bound mana ability cannot be reparsed.")
        elif parsed.is_mana is not True:
            problems.append("The selected Oracle ability is not classified as a mana ability.")
        if scenario.ability_is_mana is not True:
            problems.append("Stored mana metadata does not classify the ability as mana.")
        if scenario.ability_source_zone and scenario.ability_source_zone != "battlefield":
            problems.append("The selected mana ability is not activated from the battlefield.")

    if scenario.concept_id == "source_independence":
        if not scenario.ability_text:
            problems.append("The source scenario is not bound to an exact Oracle ability.")
        if parsed is None:
            problems.append("The bound source ability cannot be reparsed.")
        else:
            if parsed.is_mana:
                problems.append("Source-independence scenarios require a non-mana activated ability.")
            if parsed.source_zone != "battlefield":
                problems.append(
                    "The selected ability is not activated from a battlefield permanent."
                )
            if parsed.source_removed_as_cost:
                problems.append(
                    "The selected ability removes its own source as an activation cost, "
                    "so the later source-removal sequence is impossible."
                )
            if scenario.source_removed_as_cost != parsed.source_removed_as_cost:
                problems.append(
                    "Stored source-removal metadata disagrees with the current Oracle parser."
                )
            if (
                scenario.source_may_be_removed_as_cost is not None
                and scenario.source_may_be_removed_as_cost
                != parsed.source_may_be_removed_as_cost
            ):
                problems.append(
                    "Stored optional source-payment metadata disagrees with the current Oracle parser."
                )
            if (
                scenario.source_may_be_target is not None
                and scenario.source_may_be_target != parsed.source_may_be_target
            ):
                problems.append(
                    "Stored source-target metadata disagrees with the current Oracle parser."
                )
            if parsed.source_may_be_removed_as_cost and not parsed.source_removed_as_cost:
                normalized_question = scenario.question.casefold()
                if not any(marker in normalized_question for marker in (
                    "no fue uno de los objetos sacrificados",
                    "no fue sacrificad",
                )):
                    problems.append(
                        "The source could pay a generic sacrifice cost, but the question does not state that other objects were sacrificed instead."
                    )
            if parsed.source_may_be_target:
                normalized_question = scenario.question.casefold()
                if not any(marker in normalized_question for marker in (
                    "ninguno de los objetivos",
                    "todos eran objetos distintos",
                )):
                    problems.append(
                        "The source could be a legal target, but the question does not exclude it from every target."
                    )
            if scenario.source_dependency != parsed.source_dependency:
                problems.append(
                    "Stored source-dependency metadata disagrees with the current Oracle parser "
                    f"({scenario.source_dependency!r} != {parsed.source_dependency!r})."
                )
        if scenario.ability_is_mana is True:
            problems.append("Source-independence scenarios require a non-mana activated ability.")
        if scenario.ability_source_zone != "battlefield":
            problems.append(
                "The selected ability is not activated from a battlefield permanent."
            )
        if scenario.source_removed_as_cost is not False:
            problems.append(
                "The selected ability removes its own source as an activation cost, "
                "so the later source-removal sequence is impossible."
            )
        if scenario.source_dependency not in _VALID_DEPENDENCIES:
            problems.append(
                f"Unknown source-dependency classification: {scenario.source_dependency!r}."
            )

    return _dedupe(problems)


def _reparse_bound_ability(scenario: DynamicScenario):
    if not scenario.ability_text:
        return None
    abilities = extract_activated_abilities(
        scenario.ability_text,
        card_name=scenario.card_name,
        type_line=scenario.card_type_line,
    )
    return abilities[0] if len(abilities) == 1 else None


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item not in result:
            result.append(item)
    return result
