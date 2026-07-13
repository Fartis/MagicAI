from __future__ import annotations

from magicai.sources.rulings import find_rulings_by_oracle_id


class RulingRepository:
    def find_by_oracle_id(
        self,
        oracle_id: str,
        *,
        limit: int = 8,
    ) -> list[dict[str, str]]:
        return find_rulings_by_oracle_id(oracle_id, limit=limit)
