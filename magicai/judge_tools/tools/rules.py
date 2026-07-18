from __future__ import annotations

from typing import Any

from magicai.judge_tools.models import JudgeToolPayload, JudgeToolStatus
from magicai.judge_tools.tools.common import clean_string_list, rule_to_evidence
from magicai.repositories.rule_repository import RuleRepository


class RulesLookupTool:
    def __init__(self, repository: RuleRepository | None = None):
        self.repository = repository or RuleRepository()

    def __call__(
        self,
        arguments: dict[str, Any],
        *,
        conversation=None,
        result_limit: int = 8,
    ) -> JudgeToolPayload:
        identifiers = clean_string_list(
            arguments.get("identifiers", arguments.get("identifier")),
            field_name="identifiers",
        )
        if not identifiers:
            raise ValueError("rules_lookup requires identifiers")

        evidence: list[dict[str, Any]] = []
        missing: list[str] = []
        seen: set[str] = set()
        for identifier in identifiers[:result_limit]:
            rule = self.repository.find_by_keyword(identifier)
            if rule is None:
                missing.append(identifier)
                continue
            item = rule_to_evidence(rule)
            key = item["identifier"]
            if key in seen:
                continue
            seen.add(key)
            evidence.append(item)

        warnings = []
        if missing:
            warnings.append("Rules not resolved: " + ", ".join(missing))
        return JudgeToolPayload(
            evidence=evidence,
            warnings=warnings,
            status=(JudgeToolStatus.SUCCESS if evidence else JudgeToolStatus.NOT_FOUND),
            metadata={"requested_identifiers": identifiers, "resolved_count": len(evidence)},
        )


class RulesSearchTool:
    def __init__(self, repository: RuleRepository | None = None):
        self.repository = repository or RuleRepository()

    def __call__(
        self,
        arguments: dict[str, Any],
        *,
        conversation=None,
        result_limit: int = 8,
    ) -> JudgeToolPayload:
        query = str(arguments.get("query", "")).strip()
        if not query:
            raise ValueError("rules_search requires query")
        requested_limit = int(arguments.get("limit", result_limit))
        limit = max(1, min(requested_limit, result_limit))
        rules = self.repository.search(query, limit=limit)
        return JudgeToolPayload(
            evidence=[rule_to_evidence(rule) for rule in rules],
            status=(JudgeToolStatus.SUCCESS if rules else JudgeToolStatus.NOT_FOUND),
            metadata={"query": query, "match_count": len(rules)},
        )
