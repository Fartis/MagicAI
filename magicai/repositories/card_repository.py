from magicai.services.card_service import find_card

from magicai.mappers.card_mapper import to_card


class CardRepository:

    def find_by_name(self, name: str):

        result = find_card(name)

        if result["type"] != "exact":

            return None

        return to_card(

            result["results"][0]

        )