from __future__ import annotations

from magicai.oracle_abilities import extract_activated_abilities
from tests.quality.dynamic.concepts import contract_for_scenario, get_concepts
from tests.quality.dynamic.models import DynamicScenario
from tests.quality.dynamic.semantic_validation import validate_dynamic_answer


def _ability(text: str, name: str, type_line: str):
    abilities = extract_activated_abilities(text, card_name=name, type_line=type_line)
    assert len(abilities) == 1
    return abilities[0]


def test_multiline_modal_ability_keeps_bullet_modes():
    ability = _ability(
        "{G}: Choose one. Activate only once each turn.\n"
        "• Until end of turn, this creature becomes a Rhino with base power and toughness 4/4 and gains trample.\n"
        "• Until end of turn, this creature becomes a Bird with base power and toughness 2/2 and gains flying.\n"
        "• Until end of turn, this creature becomes a Plant with base power and toughness 0/8.",
        "Skinshifter",
        "Creature — Human Shaman",
    )
    assert "• Until end of turn" in ability.text
    assert ability.source_dependency == "source_object"


def test_source_dependency_c14_regressions_are_generic():
    cases = (
        (
            "{4}{G}{G}: Monstrosity 3. (If this creature isn't monstrous, put three +1/+1 counters on it and it becomes monstrous.)",
            "Slime",
            "Creature — Ooze",
            "source_object",
        ),
        (
            "{0}: The next 1 damage that would be dealt to this creature this turn is dealt to target creature you control instead.",
            "Lancer",
            "Creature — Kor Soldier",
            "source_object",
        ),
        (
            "{8}: This creature and up to one other target creature each get +3/+3 until end of turn.",
            "Invoker",
            "Creature — Elf Scout",
            "partial",
        ),
        (
            "{2}: This artifact deals 1 damage to any target. Sacrifice this artifact.",
            "Cannon",
            "Artifact",
            "partial",
        ),
        (
            "{5}, {T}: Draw a card. This ability costs {1} less to activate for each page counter on this artifact.",
            "Diary",
            "Artifact",
            "independent",
        ),
    )
    for text, name, type_line, expected in cases:
        assert _ability(text, name, type_line).source_dependency == expected


def test_optional_generic_sacrifice_cost_detects_source_eligibility():
    cases = (
        ("{T}, Sacrifice three artifacts: Draw a card.", "Forge", "Artifact Creature — Construct"),
        ("{1}, Sacrifice an Elf: Draw a card.", "Commander", "Creature — Elf"),
        ("Sacrifice a creature: Draw a card.", "Hopper", "Creature — Insect"),
    )
    for text, name, type_line in cases:
        ability = _ability(text, name, type_line)
        assert ability.source_removed_as_cost is False
        assert ability.source_may_be_removed_as_cost is True

    safe = _ability(
        "{1}, Sacrifice another creature: Draw a card.",
        "Specialist",
        "Creature — Human",
    )
    assert safe.source_may_be_removed_as_cost is False

    mixed = _ability(
        "{1}, Sacrifice another creature or an artifact: Draw a card.",
        "Relic Beast",
        "Artifact Creature — Beast",
    )
    assert mixed.source_may_be_removed_as_cost is True


def test_source_target_risk_is_bound_separately_from_source_independence():
    risky = _ability(
        "{T}: Put a +1/+1 counter on target creature.",
        "Kraj",
        "Creature — Ooze",
    )
    assert risky.source_may_be_target is True

    safe = _ability(
        "{3}: Put target card from a graveyard on the bottom of its owner's library.",
        "Sentinel",
        "Artifact Creature — Construct",
    )
    assert safe.source_may_be_target is False

    explicit_other = _ability(
        "{8}: This creature and up to one other target creature each get +3/+3 until end of turn.",
        "Invoker",
        "Creature — Elf",
    )
    assert explicit_other.source_may_be_target is False


def test_source_contract_requires_cost_and_target_qualifications():
    concept = get_concepts(["source_independence"])[0]
    base = contract_for_scenario(concept, source_dependency="independent")
    qualified = contract_for_scenario(
        concept,
        source_dependency="independent",
        source_may_be_removed_as_cost=True,
        source_may_be_target=True,
    )
    assert len(qualified.required_any) == len(base.required_any) + 2


def test_semantic_audit_rejects_missing_cost_and_target_caveats():
    concept = get_concepts(["source_independence"])[0]
    scenario = DynamicScenario(
        id="DG-001",
        seed=1,
        concept_id=concept.id,
        concept_name=concept.name,
        card_name="Example",
        template_id="source-destroyed",
        question=(
            "Activo «Sacrifice a creature: Target creature gets +1/+1.» y destruyen la fuente. "
            "Los sacrificios del coste se pagaron con otros objetos; Example no fue uno "
            "de los objetos sacrificados. Ninguno de los objetivos de la habilidad era "
            "Example; todos eran objetos distintos."
        ),
        tags=concept.tags,
        contract=concept.contract,
        ability_text="Sacrifice a creature: Target creature gets +1/+1.",
        ability_cost="Sacrifice a creature",
        ability_effect="Target creature gets +1/+1.",
        ability_is_mana=False,
        ability_source_zone="battlefield",
        source_removed_as_cost=False,
        source_may_be_removed_as_cost=True,
        source_dependency="independent",
        source_may_be_target=True,
    )
    incomplete = (
        "No. La habilidad permanece en la pila y se resuelve independientemente de su fuente."
    )
    failures = validate_dynamic_answer(scenario, incomplete)
    assert any("source-as-cost" in item for item in failures)
    assert any("target legality" in item for item in failures)

    complete = (
        "No. La habilidad permanece en la pila y existe de forma independiente de su fuente. "
        "La pregunta indica que la fuente no fue uno de los objetos sacrificados. Si se hubiera "
        "sacrificado la fuente, ya habría salido al pagar. Si la fuente hubiera sido objetivo y todos sus objetivos fueran "
        "ilegales, la habilidad no se resolvería por las reglas de objetivos."
    )
    assert validate_dynamic_answer(scenario, complete) == []


def main():
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    errors = []
    for test in tests:
        try:
            test()
            print(f"OK: {test.__name__}")
        except Exception as exc:
            errors.append((test.__name__, exc))
            print(f"ERROR: {test.__name__}: {exc}")
    print(f"Tests: {len(tests)} · Errors: {len(errors)}")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
