from __future__ import annotations

import random

from tests.quality.dynamic.card_catalog import CardCatalog, CardCandidate
from tests.quality.dynamic.models import DynamicConcept, DynamicScenario


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
        self._remaining_templates: dict[str, list] = {}

    def generate(self, count: int) -> list[DynamicScenario]:
        if count <= 0:
            raise ValueError("--cases must be greater than zero.")

        scenarios = []
        concept_queue: list[DynamicConcept] = []

        for index in range(1, count + 1):
            if not concept_queue:
                concept_queue = list(self.concepts)
                self.random.shuffle(concept_queue)

            concept = concept_queue.pop()
            card = self._next_card(concept)
            template = self._next_template(concept)

            scenarios.append(
                DynamicScenario(
                    id=f"DG-{index:03d}",
                    seed=self.seed,
                    concept_id=concept.id,
                    concept_name=concept.name,
                    card_name=card.name,
                    template_id=template.id,
                    question=template.render(card.name),
                    tags=concept.tags + (f"template:{template.id}",),
                    contract=concept.contract,
                    oracle_evidence=card.oracle_text,
                    card_type_line=card.type_line,
                    card_keywords=card.keywords,
                )
            )

        return scenarios

    def _next_card(self, concept: DynamicConcept) -> CardCandidate:
        remaining = self._remaining_cards.get(concept.id)

        if not remaining:
            remaining = list(self.catalog.select(concept.selector))
            self.random.shuffle(remaining)
            self._remaining_cards[concept.id] = remaining

        return remaining.pop()

    def _next_template(self, concept: DynamicConcept):
        remaining = self._remaining_templates.get(concept.id)

        if not remaining:
            remaining = list(concept.templates)
            self.random.shuffle(remaining)
            self._remaining_templates[concept.id] = remaining

        return remaining.pop()
