from magicai.services.rule_service import find_rule
from magicai.services.rule_service import search_rules


class RuleRepository:

    def find_by_keyword(self, keyword: str):

        return find_rule(keyword)

    def search(self, query: str, limit: int = 5):

        return search_rules(
            query=query,
            limit=limit,
        )
