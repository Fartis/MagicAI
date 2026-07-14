from __future__ import annotations

from tests.quality.dynamic.models import DynamicScenario


def validate_dynamic_premise(scenario: DynamicScenario) -> list[str]:
    """Validate generator-owned facts before asking the Judge.

    A failure here means the benchmark premise is invalid. It is never converted
    into a Judge PASS, even if a generic renderer happens to emit expected words.
    """

    problems: list[str] = []

    if scenario.concept_id == "mana_ability":
        if not scenario.ability_text:
            problems.append("The mana scenario is not bound to an exact Oracle ability.")
        if scenario.ability_is_mana is not True:
            problems.append("The selected Oracle ability is not classified as a mana ability.")
        if scenario.ability_source_zone and scenario.ability_source_zone != "battlefield":
            problems.append("The selected mana ability is not activated from the battlefield.")

    if scenario.concept_id == "source_independence":
        if not scenario.ability_text:
            problems.append("The source scenario is not bound to an exact Oracle ability.")
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

    return problems
