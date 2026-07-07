from dataclasses import dataclass, fields


@dataclass(slots=True)
class Card:

    oracle_id: str
    id: str

    name: str

    mana_cost: str | None
    cmc: float

    type_line: str
    oracle_text: str | None

    power: str | None
    toughness: str | None

    loyalty: str | None
    defense: str | None

    colors: str
    color_identity: str
    keywords: str
    legalities: str

    rarity: str | None
    released_at: str | None

    scryfall_uri: str
    rulings_uri: str
