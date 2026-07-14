from __future__ import annotations

import random

from tests.quality.dynamic.card_catalog import (
    CardAbilityCandidate,
    CardCandidate,
    CardCatalog,
)
from tests.quality.dynamic.models import DynamicConcept, DynamicScenario
from tests.quality.dynamic.concepts import contract_for_scenario


_ABILITY_SELECTORS = {
    "mana_ability",
    "activated_nonmana",
    "source_independence_ability",
}


class ScenarioGenerator:
    def __init__(
        self,
        seed: int,
        catalog: CardCatalog,
        concepts: list[DynamicConcept],
    ):
        if not concepts:
            raise ValueError("At least one dynamic concept is required.")
        self.seed = seed
        self.catalog = catalog
        self.concepts = list(concepts)
        self.random = random.Random(seed)
        self._remaining_cards: dict[str, list[CardCandidate]] = {}
        self._remaining_abilities: dict[str, list[CardAbilityCandidate]] = {}
        self._remaining_templates: dict[str, list] = {}

    def generate(self, count: int) -> list[DynamicScenario]:
        if count <= 0:
            raise ValueError("--cases must be greater than zero.")
        scenarios: list[DynamicScenario] = []
        concept_queue: list[DynamicConcept] = []
        for index in range(1, count + 1):
            if not concept_queue:
                concept_queue = list(self.concepts)
                self.random.shuffle(concept_queue)
            concept = concept_queue.pop()
            ability_candidate = None
            card = None
            if concept.selector:
                if concept.selector in _ABILITY_SELECTORS:
                    ability_candidate = self._next_ability(concept)
                    card = ability_candidate.card
                else:
                    card = self._next_card(concept)
            template = self._next_template(concept)
            ability = ability_candidate.ability if ability_candidate else None
            card_name = card.name if card else ""
            ability_text = ability.text if ability else ""
            scenarios.append(
                DynamicScenario(
                    id=f"DG-{index:03d}",
                    seed=self.seed,
                    concept_id=concept.id,
                    concept_name=concept.name,
                    card_name=card_name,
                    template_id=template.id,
                    question=template.render(card_name, ability_text),
                    tags=concept.tags + (f"template:{template.id}",),
                    contract=contract_for_scenario(
                        concept,
                        source_dependency=ability.source_dependency if ability else "",
                    ),
                    oracle_evidence=card.oracle_text if card else "",
                    card_type_line=card.type_line if card else "",
                    card_keywords=card.keywords if card else (),
                    card_set_code=card.set_code if card else "",
                    card_set_name=card.set_name if card else "",
                    card_set_type=card.set_type if card else "",
                    card_legal_formats=card.legal_formats if card else (),
                    source_kind="card" if card else "rules",
                    ability_index=ability.index if ability else None,
                    ability_text=ability.text if ability else "",
                    ability_cost=ability.cost if ability else "",
                    ability_effect=ability.effect if ability else "",
                    ability_is_mana=ability.is_mana if ability else None,
                    ability_source_zone=ability.source_zone if ability else "",
                    source_removed_as_cost=ability.source_removed_as_cost if ability else None,
                    source_dependency=ability.source_dependency if ability else "",
                )
            )
        return scenarios

    def _next_card(self, concept: DynamicConcept) -> CardCandidate:
        if concept.selector is None:
            raise ValueError(f"Concept {concept.id!r} does not use a card selector.")
        remaining = self._remaining_cards.get(concept.id)
        if not remaining:
            remaining = list(self.catalog.select(concept.selector))
            self.random.shuffle(remaining)
            self._remaining_cards[concept.id] = remaining
        return remaining.pop()

    def _next_ability(self, concept: DynamicConcept) -> CardAbilityCandidate:
        if concept.selector is None:
            raise ValueError(f"Concept {concept.id!r} does not use an ability selector.")
        remaining = self._remaining_abilities.get(concept.id)
        if not remaining:
            remaining = list(self.catalog.select_abilities(concept.selector))
            self.random.shuffle(remaining)
            self._remaining_abilities[concept.id] = remaining
        return remaining.pop()

    def _next_template(self, concept: DynamicConcept):
        remaining = self._remaining_templates.get(concept.id)
        if not remaining:
            remaining = list(concept.templates)
            self.random.shuffle(remaining)
            self._remaining_templates[concept.id] = remaining
        return remaining.pop()
