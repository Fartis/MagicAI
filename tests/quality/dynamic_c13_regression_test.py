from __future__ import annotations

from dataclasses import replace

from magicai.oracle_abilities import extract_activated_abilities
from tests.quality.dynamic.concepts import contract_for_scenario, get_concepts
from tests.quality.dynamic.models import DynamicScenario
from tests.quality.dynamic.premise_validation import validate_dynamic_premise
from tests.quality.dynamic.semantic_validation import validate_dynamic_answer


def _ability(text: str, name: str, type_line: str):
    abilities = extract_activated_abilities(text, card_name=name, type_line=type_line)
    assert len(abilities) == 1
    return abilities[0]


def test_self_removal_supports_object_subtypes_and_short_names():
    cases = (
        ("Sacrifice this Case: Draw a card.", "Case of Test", "Enchantment — Case"),
        ("Sacrifice this Aura: Draw a card.", "Crown of Test", "Enchantment — Aura"),
        ("Sacrifice King Darien: Draw a card.", "King Darien XLVIII", "Legendary Creature — Human Soldier"),
    )
    for text, name, type_line in cases:
        assert _ability(text, name, type_line).source_removed_as_cost is True


def test_source_dependency_regressions_are_generic():
    cases = (
        ("{T}: Draw a card, then put this artifact on top of its owner's library.", "Top", "Artifact", "partial"),
        ("{5}{U}: Adapt 2.", "Spy", "Creature — Mutant", "source_object"),
        ("{U}{R}: Level 2", "Class", "Enchantment — Class", "source_object"),
        ("{2}{G}: This creature can attack this turn as though it didn't have defender.", "Guard", "Creature", "source_object"),
        ("{1}{W}{U}: Exile Stenn. Return it to the battlefield under its owner's control at the beginning of the next end step.", "Stenn, Paranoid Partisan", "Legendary Creature — Human Wizard", "source_object"),
    )
    for text, name, type_line, expected in cases:
        assert _ability(text, name, type_line).source_dependency == expected


def test_premise_reparses_stale_source_removal_metadata():
    ability = _ability(
        "Sacrifice this Case: Draw a card.",
        "Case of Test",
        "Enchantment — Case",
    )
    concept = get_concepts(["source_independence"])[0]
    scenario = DynamicScenario(
        id="DG-001", seed=1, concept_id=concept.id, concept_name=concept.name,
        card_name="Case of Test", template_id="source-destroyed",
        question="Activo la habilidad «Sacrifice this Case: Draw a card.» y después destruyen la fuente.",
        tags=concept.tags, contract=concept.contract,
        card_type_line="Enchantment — Case", ability_text=ability.text,
        ability_cost=ability.cost, ability_effect=ability.effect,
        ability_is_mana=False, ability_source_zone="battlefield",
        source_removed_as_cost=False, source_dependency=ability.source_dependency,
    )
    failures = validate_dynamic_premise(scenario)
    assert any("removes its own source" in item for item in failures)
    assert any("metadata disagrees" in item for item in failures)


def test_ward_semantic_audit_rejects_old_llm_failure():
    concept = get_concepts(["ward"])[0]
    scenario = DynamicScenario(
        id="DG-013", seed=1, concept_id="ward", concept_name=concept.name,
        card_name="Sire", template_id="ward-stack", question="¿Ward usa la pila?",
        tags=concept.tags, contract=concept.contract,
    )
    bad = (
        "Ward se activa. El jugador paga 7 vidas para evitar que el hechizo se "
        "resuelva y puede responder durante su resolución."
    )
    failures = validate_dynamic_answer(scenario, bad)
    assert len(failures) >= 4


def test_ward_semantic_audit_accepts_correct_procedure():
    concept = get_concepts(["ward"])[0]
    scenario = DynamicScenario(
        id="DG-013", seed=1, concept_id="ward", concept_name=concept.name,
        card_name="Sire", template_id="ward-stack", question="¿Ward usa la pila?",
        tags=concept.tags, contract=concept.contract,
    )
    good = (
        "Ward es una habilidad disparada que se pone en la pila. Se puede "
        "responder antes de que se resuelva. Si el controlador del hechizo no "
        "paga el coste, Ward contrarresta ese hechizo."
    )
    assert validate_dynamic_answer(scenario, good) == []


def test_source_contract_varies_by_dependency():
    concept = get_concepts(["source_independence"])[0]
    independent = contract_for_scenario(concept, source_dependency="independent")
    source_object = contract_for_scenario(concept, source_dependency="source_object")
    information = contract_for_scenario(concept, source_dependency="information")
    partial = contract_for_scenario(concept, source_dependency="partial")
    assert independent != source_object
    assert source_object != information
    assert partial != information


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
