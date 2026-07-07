PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS rulings;
DROP TABLE IF EXISTS prints;
DROP TABLE IF EXISTS cards;
DROP TABLE IF EXISTS sets;

CREATE TABLE cards (
    oracle_id TEXT PRIMARY KEY,
    id TEXT NOT NULL UNIQUE,

    name TEXT NOT NULL,

    mana_cost TEXT,
    cmc REAL,

    type_line TEXT,
    oracle_text TEXT,

    power TEXT,
    toughness TEXT,
    loyalty TEXT,
    defense TEXT,

    colors TEXT,
    color_identity TEXT,
    keywords TEXT,
    legalities TEXT,

    rarity TEXT,
    released_at TEXT,

    scryfall_uri TEXT,
    rulings_uri TEXT
);

CREATE TABLE prints (
    id TEXT PRIMARY KEY,

    oracle_id TEXT NOT NULL,

    set_code TEXT,
    collector_number TEXT,

    language TEXT,

    artist TEXT,

    image_uri TEXT,

    FOREIGN KEY (oracle_id)
        REFERENCES cards(oracle_id)
);

CREATE TABLE rulings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    oracle_id TEXT NOT NULL,

    published_at TEXT,

    comment TEXT,

    FOREIGN KEY (oracle_id)
        REFERENCES cards(oracle_id)
);

CREATE TABLE sets (
    code TEXT PRIMARY KEY,

    name TEXT,

    released_at TEXT,

    set_type TEXT
);

CREATE INDEX idx_cards_name
ON cards(name);

CREATE INDEX idx_cards_cmc
ON cards(cmc);

CREATE INDEX idx_cards_type
ON cards(type_line);
