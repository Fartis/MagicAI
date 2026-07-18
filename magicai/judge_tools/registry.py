from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CapabilityStatus(str, Enum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    PLANNED = "planned"
    PERMISSION_REQUIRED = "permission_required"


@dataclass(frozen=True, slots=True)
class JudgeCapability:
    name: str
    status: CapabilityStatus
    authority: str
    provider: str
    description: str
    executable: bool = False
    read_only: bool = True
    max_results: int = 8
    arguments: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "authority": self.authority,
            "provider": self.provider,
            "description": self.description,
            "executable": self.executable,
            "read_only": self.read_only,
            "max_results": self.max_results,
            "arguments": list(self.arguments),
        }


_CAPABILITIES = (
    JudgeCapability(
        name="oracle_lookup",
        status=CapabilityStatus.AVAILABLE,
        authority="official_card_data",
        provider="local_scryfall_oracle",
        description="Resolve supported paper cards and current Oracle text from the local Scryfall snapshot.",
        executable=True,
        max_results=20,
        arguments=("card_names",),
    ),
    JudgeCapability(
        name="oracle_search",
        status=CapabilityStatus.AVAILABLE,
        authority="official_card_data",
        provider="local_scryfall_oracle",
        description="Search supported paper card names in the local Scryfall Oracle snapshot.",
        executable=True,
        max_results=20,
        arguments=("query", "limit"),
    ),
    JudgeCapability(
        name="rules_lookup",
        status=CapabilityStatus.AVAILABLE,
        authority="official_rules",
        provider="local_comprehensive_rules",
        description="Resolve exact numbered rules or named rule sections from the local Comprehensive Rules snapshot.",
        executable=True,
        max_results=20,
        arguments=("identifiers",),
    ),
    JudgeCapability(
        name="rules_search",
        status=CapabilityStatus.AVAILABLE,
        authority="official_rules",
        provider="local_comprehensive_rules",
        description="Search conceptual rules in the local Comprehensive Rules snapshot.",
        executable=True,
        max_results=12,
        arguments=("query", "limit"),
    ),
    JudgeCapability(
        name="rulings_lookup",
        status=CapabilityStatus.AVAILABLE,
        authority="official_rulings",
        provider="local_scryfall_rulings",
        description="Retrieve current local Scryfall rulings and preserve their provenance.",
        executable=True,
        max_results=20,
        arguments=("card_names", "oracle_ids"),
    ),
    JudgeCapability(
        name="conversation_context",
        status=CapabilityStatus.AVAILABLE,
        authority="session_state",
        provider="local_conversation_repository",
        description="Reuse Judge-validated cards, rule topics, and bounded recent turns across follow-up questions.",
        executable=True,
        max_results=1,
        arguments=("include_history", "history_limit"),
    ),
    JudgeCapability(
        name="legality_check",
        status=CapabilityStatus.AVAILABLE,
        authority="official_card_data",
        provider="local_scryfall_oracle",
        description="Return local Scryfall legality and color-identity data for explicitly named cards.",
        executable=True,
        max_results=20,
        arguments=("card_names", "formats"),
    ),
    JudgeCapability(
        name="spellbook_search",
        status=CapabilityStatus.PLANNED,
        authority="community_combo_candidate",
        provider="commander_spellbook",
        description="Find community combo candidates, then revalidate every step through Oracle and the Comprehensive Rules.",
        arguments=("card_names", "deck_cards", "max_missing_cards"),
    ),
    JudgeCapability(
        name="strategic_statistics",
        status=CapabilityStatus.PERMISSION_REQUIRED,
        authority="statistical",
        provider="authorized_edhrec_or_import",
        description="Use authorized statistics or an explicitly imported snapshot; never treat popularity as rules authority.",
        arguments=("commander", "card_names", "theme"),
    ),
    JudgeCapability(
        name="collection_lookup",
        status=CapabilityStatus.PLANNED,
        authority="user_data",
        provider="local_collection",
        description="Check cards owned by the user without exposing the collection directly to the Tactician.",
        arguments=("card_names",),
    ),
)

_CAPABILITY_INDEX = {capability.name: capability for capability in _CAPABILITIES}


def get_capability_registry() -> tuple[JudgeCapability, ...]:
    return _CAPABILITIES


def get_capability(name: str) -> JudgeCapability | None:
    return _CAPABILITY_INDEX.get((name or "").strip())


def get_capability_registry_payload() -> list[dict[str, Any]]:
    return [capability.to_dict() for capability in _CAPABILITIES]
