from __future__ import annotations

from magicai.oracle_abilities import extract_activated_abilities
from tests.quality.dynamic.concepts import contract_for_scenario, get_concepts
from tests.quality.dynamic.models import DynamicScenario
from tests.quality.dynamic.semantic_validation import validate_dynamic_answer


def _ability(text: str, name: str, type_line: str):
    abilities = extract_activated_abilities(text, card_name=name, type_line=type_line)
    assert len(abilities) == 1
    return abilities[0]


def test_source_pronouns_follow_cost_and_prior_clauses():
    cases = (
        (
            "Remove two +1/+1 counters from this creature: Regenerate it.",
            "Experiment One",
            "Creature — Human Ooze",
            "source_object",
        ),
        (
            "{1}{W}: Put a +1/+1 counter on this creature. It gains double strike until end of turn.",
            "Pacesetter Paragon",
            "Creature — Human Knight",
            "source_object",
        ),
        (
            "{2}: This Vehicle becomes an artifact creature. Put a +1/+1 counter on it.",
            "Rangers' Refueler",
            "Artifact — Vehicle",
            "source_object",
        ),
        (
            "{1}{B}, {T}: This creature loses this ability and becomes an Aura enchantment with enchant creature. Attach it to target creature. You may pay {B} to end this effect.",
            "Stinging Licid",
            "Creature — Licid",
            "source_object",
        ),
    )
    for text, name, type_line, expected in cases:
        assert _ability(text, name, type_line).source_dependency == expected


def test_leading_it_is_source_information_not_independent():
    ability = _ability(
        "{T}: It deals 3 damage to any target.",
        "Weather Maker",
        "Creature — Human Wizard",
    )
    assert ability.source_dependency == "information"


def test_modal_mix_with_source_information_is_partial():
    ability = _ability(
        "{T}: Choose one —\n"
        "• It deals 3 damage to any target.\n"
        "• Prevent the next 3 damage that would be dealt to target creature this turn.",
        "Weather Maker",
        "Creature — Human Wizard",
    )
    assert ability.source_dependency == "partial"


def test_future_requirement_bound_to_source_has_own_category():
    ability = _ability(
        "+2: During target opponent's next turn, creatures that player controls attack Gideon Jura if able.",
        "Gideon Jura",
        "Legendary Planeswalker — Gideon",
    )
    assert ability.source_dependency == "source_bound_effect"


def test_source_bound_contract_and_semantic_validator():
    concept = get_concepts(["source_independence"])[0]
    contract = contract_for_scenario(concept, source_dependency="source_bound_effect")
    assert any("objeto identificable" in group for group in contract.required_any)
    scenario = DynamicScenario(
        id="EX-SI-1",
        seed=0,
        concept_id=concept.id,
        concept_name=concept.name,
        card_name="Example",
        template_id="source-resolution",
        question="La habilidad ya está en la pila y destruyen Example.",
        tags=concept.tags,
        contract=contract,
        ability_text="{T}: Creatures attack Example if able.",
        ability_cost="{T}",
        ability_effect="Creatures attack Example if able.",
        ability_is_mana=False,
        ability_source_zone="battlefield",
        source_removed_as_cost=False,
        source_may_be_removed_as_cost=False,
        source_dependency="source_bound_effect",
        source_may_be_target=False,
    )
    incomplete = "No. La habilidad permanece en la pila y es independiente de su fuente."
    assert any("source-bound" in item for item in validate_dynamic_answer(scenario, incomplete))
    complete = (
        "No. La habilidad permanece en la pila y es independiente de su fuente. "
        "Se resuelve, pero el efecto está ligado a que la fuente exista como un "
        "objeto identificable; sin ella esa instrucción puede resultar imposible."
    )
    assert validate_dynamic_answer(scenario, complete) == []



def test_planeswalker_subtype_resolves_short_oracle_name():
    ability = _ability(
        "0: Reveal the top card of your library and put it into your hand. Sarkhan deals damage to himself equal to that card's mana value.",
        "Sarkhan the Mad",
        "Legendary Planeswalker — Sarkhan",
    )
    assert ability.source_dependency == "partial"

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
