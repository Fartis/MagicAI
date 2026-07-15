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

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "authority": self.authority,
            "provider": self.provider,
            "description": self.description,
        }


_CAPABILITIES = (
    JudgeCapability(
        name="oracle_lookup",
        status=CapabilityStatus.AVAILABLE,
        authority="official_card_data",
        provider="local_scryfall_oracle",
        description="Resolve supported paper cards and current Oracle text from the local Scryfall snapshot.",
    ),
    JudgeCapability(
        name="rules_search",
        status=CapabilityStatus.AVAILABLE,
        authority="official_rules",
        provider="local_comprehensive_rules",
        description="Retrieve numbered and conceptual rules from the local Comprehensive Rules snapshot.",
    ),
    JudgeCapability(
        name="rulings_lookup",
        status=CapabilityStatus.AVAILABLE,
        authority="official_rulings",
        provider="local_scryfall_rulings",
        description="Retrieve current local Scryfall rulings and preserve their provenance.",
    ),
    JudgeCapability(
        name="conversation_context",
        status=CapabilityStatus.AVAILABLE,
        authority="session_state",
        provider="local_conversation_repository",
        description="Reuse Judge-validated cards and rule topics across follow-up turns.",
    ),
    JudgeCapability(
        name="legality_check",
        status=CapabilityStatus.PARTIAL,
        authority="official_card_data",
        provider="local_scryfall_oracle",
        description="Legality exists in the Oracle snapshot but is not yet exposed through the full Tactician evidence contract.",
    ),
    JudgeCapability(
        name="spellbook_search",
        status=CapabilityStatus.PLANNED,
        authority="community_combo_candidate",
        provider="commander_spellbook",
        description="Find community combo candidates, then revalidate every step through Oracle and the Comprehensive Rules.",
    ),
    JudgeCapability(
        name="strategic_statistics",
        status=CapabilityStatus.PERMISSION_REQUIRED,
        authority="statistical",
        provider="authorized_edhrec_or_import",
        description="Use authorized statistics or an explicitly imported snapshot; never treat popularity as rules authority.",
    ),
    JudgeCapability(
        name="collection_lookup",
        status=CapabilityStatus.PLANNED,
        authority="user_data",
        provider="local_collection",
        description="Check cards owned by the user without exposing the collection directly to the Tactician.",
    ),
)


def get_capability_registry() -> tuple[JudgeCapability, ...]:
    return _CAPABILITIES


def get_capability_registry_payload() -> list[dict[str, Any]]:
    return [capability.to_dict() for capability in _CAPABILITIES]
