from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SCENARIO_SCHEMA_VERSION = 3


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
            required_any=tuple(tuple(group) for group in payload.get("required_any", [])),
            forbidden=tuple(payload.get("forbidden", [])),
            recommended_all=tuple(payload.get("recommended_all", [])),
            recommended_any=tuple(tuple(group) for group in payload.get("recommended_any", [])),
            soft_forbidden=tuple(payload.get("soft_forbidden", [])),
        )

    def to_step(self, question: str) -> dict[str, Any]:
        return {"question": question, **self.to_dict()}


@dataclass(frozen=True)
class QuestionTemplate:
    id: str
    text: str

    def render(self, card_name: str = "", ability_text: str = "") -> str:
        return self.text.format(card=card_name, ability=ability_text)


@dataclass(frozen=True)
class DynamicConcept:
    id: str
    name: str
    selector: str | None
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
    card_set_code: str = ""
    card_set_name: str = ""
    card_set_type: str = ""
    card_legal_formats: tuple[str, ...] = ()
    source_kind: str = "card"
    ability_index: int | None = None
    ability_text: str = ""
    ability_cost: str = ""
    ability_effect: str = ""
    ability_is_mana: bool | None = None
    ability_source_zone: str = ""
    source_removed_as_cost: bool | None = None
    source_may_be_removed_as_cost: bool | None = None
    source_dependency: str = ""
    source_may_be_target: bool | None = None

    def to_case(self) -> dict[str, Any]:
        case_name = self.concept_name
        if self.card_name:
            case_name += f" · {self.card_name}"
        return {
            "id": self.id,
            "name": case_name,
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
            "card_set_code": self.card_set_code,
            "card_set_name": self.card_set_name,
            "card_set_type": self.card_set_type,
            "card_legal_formats": list(self.card_legal_formats),
            "source_kind": self.source_kind,
            "ability_index": self.ability_index,
            "ability_text": self.ability_text,
            "ability_cost": self.ability_cost,
            "ability_effect": self.ability_effect,
            "ability_is_mana": self.ability_is_mana,
            "ability_source_zone": self.ability_source_zone,
            "source_removed_as_cost": self.source_removed_as_cost,
            "source_may_be_removed_as_cost": self.source_may_be_removed_as_cost,
            "source_dependency": self.source_dependency,
            "source_may_be_target": self.source_may_be_target,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DynamicScenario":
        schema_version = int(payload.get("schema_version", 1))
        if schema_version not in {1, 2, SCENARIO_SCHEMA_VERSION}:
            raise ValueError(
                "Unsupported dynamic scenario schema version: "
                f"{schema_version!r}"
            )
        ability_index = payload.get("ability_index")
        ability_is_mana = payload.get("ability_is_mana")
        source_removed = payload.get("source_removed_as_cost")
        source_may_be_removed = payload.get("source_may_be_removed_as_cost")
        source_may_be_target = payload.get("source_may_be_target")
        return cls(
            id=str(payload["id"]),
            seed=int(payload["seed"]),
            concept_id=str(payload["concept_id"]),
            concept_name=str(payload["concept_name"]),
            card_name=str(payload.get("card_name", "")),
            template_id=str(payload["template_id"]),
            question=str(payload["question"]),
            tags=tuple(payload.get("tags", [])),
            contract=EvaluationContract.from_dict(payload["contract"]),
            oracle_evidence=str(payload.get("oracle_evidence", "")),
            card_type_line=str(payload.get("card_type_line", "")),
            card_keywords=tuple(payload.get("card_keywords", [])),
            card_set_code=str(payload.get("card_set_code", "")),
            card_set_name=str(payload.get("card_set_name", "")),
            card_set_type=str(payload.get("card_set_type", "")),
            card_legal_formats=tuple(payload.get("card_legal_formats", [])),
            source_kind=str(payload.get("source_kind", "card" if payload.get("card_name") else "rules")),
            ability_index=int(ability_index) if ability_index is not None else None,
            ability_text=str(payload.get("ability_text", "")),
            ability_cost=str(payload.get("ability_cost", "")),
            ability_effect=str(payload.get("ability_effect", "")),
            ability_is_mana=bool(ability_is_mana) if ability_is_mana is not None else None,
            ability_source_zone=str(payload.get("ability_source_zone", "")),
            source_removed_as_cost=bool(source_removed) if source_removed is not None else None,
            source_may_be_removed_as_cost=(
                bool(source_may_be_removed) if source_may_be_removed is not None else None
            ),
            source_dependency=str(payload.get("source_dependency", "")),
            source_may_be_target=(
                bool(source_may_be_target) if source_may_be_target is not None else None
            ),
        )
