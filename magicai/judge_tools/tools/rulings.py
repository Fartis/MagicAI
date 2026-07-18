from __future__ import annotations

from typing import Any

from magicai.judge_tools.models import JudgeToolPayload, JudgeToolStatus
from magicai.judge_tools.tools.common import clean_string_list
from magicai.repositories.card_repository import CardRepository
from magicai.repositories.ruling_repository import RulingRepository


class RulingsLookupTool:
    def __init__(
        self,
        card_repository: CardRepository | None = None,
        ruling_repository: RulingRepository | None = None,
    ):
        self.card_repository = card_repository or CardRepository()
        self.ruling_repository = ruling_repository or RulingRepository()

    def __call__(
        self,
        arguments: dict[str, Any],
        *,
        conversation=None,
        result_limit: int = 8,
    ) -> JudgeToolPayload:
        names = clean_string_list(arguments.get("card_names"), field_name="card_names")
        oracle_ids = clean_string_list(arguments.get("oracle_ids"), field_name="oracle_ids")
        if not names and not oracle_ids:
            raise ValueError("rulings_lookup requires card_names or oracle_ids")

        resolved: list[tuple[str, str]] = []
        missing: list[str] = []
        for name in names:
            card = self.card_repository.find_by_name(name)
            if card is None:
                missing.append(name)
                continue
            resolved.append((card.name, card.oracle_id))
        resolved.extend(("", oracle_id) for oracle_id in oracle_ids)

        evidence: list[dict[str, Any]] = []
        for card_name, oracle_id in resolved:
            remaining = max(0, result_limit - len(evidence))
            if remaining <= 0:
                break
            for ruling in self.ruling_repository.find_by_oracle_id(
                oracle_id,
                limit=remaining,
            ):
                data = dict(ruling)
                if card_name:
                    data["card_name"] = card_name
                evidence.append(
                    {
                        "kind": "ruling",
                        "identifier": f"{oracle_id}:{data.get('published_at', '')}",
                        "data": data,
                    }
                )

        warnings = []
        if missing:
            warnings.append("Cards not resolved for rulings: " + ", ".join(missing))
        return JudgeToolPayload(
            evidence=evidence,
            warnings=warnings,
            status=(JudgeToolStatus.SUCCESS if evidence else JudgeToolStatus.NOT_FOUND),
            metadata={"oracle_ids_checked": [oracle_id for _, oracle_id in resolved]},
        )
