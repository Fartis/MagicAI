from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SCENARIO_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class EvaluationContract:
    required_all: tuple[str, ...] = ()
    required_any: tuple[tuple[str, ...], ...] = ()
    forbidden: tuple[str, ...] = ()
    recommended_all: tuple[str, ...] = ()
    recommended_any: tuple[tuple[str, ...], ...] = ()
    soft_forbidden: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, list]:
        return {
            "required_all": list(self.required_all),
            "required_any": [list(group) for group in self.required_any],
            "forbidden": list(self.forbidden),
            "recommended_all": list(self.recommended_all),
            "recommended_any": [list(group) for group in self.recommended_any],
            "soft_forbidden": list(self.soft_forbidden),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EvaluationContract":
        return cls(
            required_all=tuple(payload.get("required_all", [])),
            required_any=tuple(
                tuple(group)
                for group in payload.get("required_any", [])
            ),
            forbidden=tuple(payload.get("forbidden", [])),
            recommended_all=tuple(payload.get("recommended_all", [])),
            recommended_any=tuple(
                tuple(group)
                for group in payload.get("recommended_any", [])
            ),
            soft_forbidden=tuple(payload.get("soft_forbidden", [])),
        )

    def to_step(self, question: str) -> dict[str, Any]:
        return {
            "question": question,
            **self.to_dict(),
        }


@dataclass(frozen=True)
class QuestionTemplate:
    id: str
    text: str

    def render(self, card_name: str) -> str:
        return self.text.format(card=card_name)


@dataclass(frozen=True)
class DynamicConcept:
    id: str
    name: str
    selector: str
    tags: tuple[str, ...]
    templates: tuple[QuestionTemplate, ...]
    contract: EvaluationContract


@dataclass(frozen=True)
class DynamicScenario:
    id: str
    seed: int
    concept_id: str
    concept_name: str
    card_name: str
    template_id: str
    question: str
    tags: tuple[str, ...]
    contract: EvaluationContract
    oracle_evidence: str = ""
    card_type_line: str = ""
    card_keywords: tuple[str, ...] = ()

    def to_case(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": f"{self.concept_name} · {self.card_name}",
            "tags": list(self.tags),
            "steps": [self.contract.to_step(self.question)],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCENARIO_SCHEMA_VERSION,
            "id": self.id,
            "seed": self.seed,
            "concept_id": self.concept_id,
            "concept_name": self.concept_name,
            "card_name": self.card_name,
            "template_id": self.template_id,
            "question": self.question,
            "tags": list(self.tags),
            "contract": self.contract.to_dict(),
            "oracle_evidence": self.oracle_evidence,
            "card_type_line": self.card_type_line,
            "card_keywords": list(self.card_keywords),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DynamicScenario":
        schema_version = payload.get("schema_version", SCENARIO_SCHEMA_VERSION)

        if schema_version != SCENARIO_SCHEMA_VERSION:
            raise ValueError(
                "Unsupported dynamic scenario schema version: "
                f"{schema_version!r}"
            )

        return cls(
            id=str(payload["id"]),
            seed=int(payload["seed"]),
            concept_id=str(payload["concept_id"]),
            concept_name=str(payload["concept_name"]),
            card_name=str(payload["card_name"]),
            template_id=str(payload["template_id"]),
            question=str(payload["question"]),
            tags=tuple(payload.get("tags", [])),
            contract=EvaluationContract.from_dict(payload["contract"]),
            oracle_evidence=str(payload.get("oracle_evidence", "")),
            card_type_line=str(payload.get("card_type_line", "")),
            card_keywords=tuple(payload.get("card_keywords", [])),
        )
