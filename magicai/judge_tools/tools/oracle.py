from __future__ import annotations

from collections.abc import Callable
from typing import Any

from magicai.judge_tools.models import JudgeToolPayload, JudgeToolStatus
from magicai.judge_tools.tools.common import card_to_evidence, clean_string_list
from magicai.repositories.card_repository import CardRepository
from magicai.scryfall import search_cards_by_name


class OracleLookupTool:
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
        if not names:
            raise ValueError("oracle_lookup requires card_names")

        evidence: list[dict[str, Any]] = []
        missing: list[str] = []
        for name in names[:result_limit]:
            card = self.repository.find_by_name(name)
            if card is None:
                missing.append(name)
                continue
            evidence.append(card_to_evidence(card))

        warnings = []
        if missing:
            warnings.append("Cards not resolved exactly: " + ", ".join(missing))
        return JudgeToolPayload(
            evidence=evidence,
            warnings=warnings,
            status=(JudgeToolStatus.SUCCESS if evidence else JudgeToolStatus.NOT_FOUND),
            metadata={"requested_names": names, "resolved_count": len(evidence)},
        )


class OracleSearchTool:
    def __init__(
        self,
        search: Callable[[str], list[dict[str, Any]]] | None = None,
    ):
        self.search = search or search_cards_by_name

    def __call__(
        self,
        arguments: dict[str, Any],
        *,
        conversation=None,
        result_limit: int = 8,
    ) -> JudgeToolPayload:
        query = str(arguments.get("query", "")).strip()
        if not query:
            raise ValueError("oracle_search requires query")

        cards = self.search(query)[:result_limit]
        return JudgeToolPayload(
            evidence=[card_to_evidence(card) for card in cards],
            status=(JudgeToolStatus.SUCCESS if cards else JudgeToolStatus.NOT_FOUND),
            metadata={"query": query, "match_count": len(cards)},
        )
