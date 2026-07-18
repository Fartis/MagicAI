from __future__ import annotations

from typing import Any

from magicai.judge_tools.models import JudgeToolPayload, JudgeToolStatus
from magicai.judge_tools.tools.common import clean_string_list
from magicai.repositories.card_repository import CardRepository


class LegalityCheckTool:
    def __init__(self, repository: CardRepository | None = None):
        self.repository = repository or CardRepository()

    def __call__(
        self,
        arguments: dict[str, Any],
        *,
        conversation=None,
        result_limit: int = 8,
    ) -> JudgeToolPayload:
        names = clean_string_list(
            arguments.get("card_names", arguments.get("name")),
            field_name="card_names",
        )
        formats = [item.casefold() for item in clean_string_list(
            arguments.get("formats"),
            field_name="formats",
        )]
        if not names:
            raise ValueError("legality_check requires card_names")

        evidence: list[dict[str, Any]] = []
        missing: list[str] = []
        for name in names[:result_limit]:
            card = self.repository.find_by_name(name)
            if card is None:
                missing.append(name)
                continue
            legalities = dict(card.legalities or {})
            selected = (
                {format_name: legalities.get(format_name, "not_legal") for format_name in formats}
                if formats
                else legalities
            )
            evidence.append(
                {
                    "kind": "legality",
                    "identifier": card.oracle_id or card.name,
                    "data": {
                        "card_name": card.name,
                        "oracle_id": card.oracle_id,
                        "color_identity": list(card.color_identity or []),
                        "legalities": selected,
                    },
                }
            )

        warnings = []
        if missing:
            warnings.append("Cards not resolved for legality: " + ", ".join(missing))
        return JudgeToolPayload(
            evidence=evidence,
            warnings=warnings,
            status=(JudgeToolStatus.SUCCESS if evidence else JudgeToolStatus.NOT_FOUND),
            metadata={"formats": formats, "resolved_count": len(evidence)},
        )
