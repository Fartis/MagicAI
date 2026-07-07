from magicai.models import Card


def parse_card(raw: dict) -> Card:

    return Card(
        oracle_id=raw["oracle_id"],
        id=raw["id"],
        name=raw["name"],

        mana_cost=raw.get("mana_cost"),
        cmc=raw["cmc"],

        type_line=raw["type_line"],
        oracle_text=raw.get("oracle_text"),

        power=raw.get("power"),
        toughness=raw.get("toughness"),

        loyalty=raw.get("loyalty"),
        defense=raw.get("defense"),

        colors=raw.get("colors", []),
        color_identity=raw.get("color_identity", []),

        keywords=raw.get("keywords", []),

        legalities=raw.get("legalities", {}),

        rarity=raw.get("rarity"),
        released_at=raw.get("released_at"),

        scryfall_uri=raw["scryfall_uri"],
        rulings_uri=raw["rulings_uri"]
    )
