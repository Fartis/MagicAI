from magicai.services.rule_service import find_rule


class RuleRepository:

    def find_by_keyword(self, keyword: str):

        return find_rule(keyword)