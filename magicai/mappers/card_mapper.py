from magicai.models import Card


def to_card(data: dict) -> Card:

    return Card(

        oracle_id=data["oracle_id"],

        id=data["id"],

        name=data["name"],

        mana_cost=data.get("mana_cost"),

        cmc=data["cmc"],

        type_line=data["type_line"],

        oracle_text=data.get("oracle_text"),

        power=data.get("power"),

        toughness=data.get("toughness"),

        loyalty=data.get("loyalty"),

        defense=data.get("defense"),

        colors=data.get("colors", []),

        color_identity=data.get("color_identity", []),

        keywords=data.get("keywords", []),

        legalities=data.get("legalities", {}),

        rarity=data.get("rarity"),

        released_at=data.get("released_at"),

        scryfall_uri=data["scryfall_uri"],

        rulings_uri=data["rulings_uri"],

    )