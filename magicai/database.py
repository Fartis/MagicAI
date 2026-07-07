from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_DIR = PROJECT_ROOT / "database"

DATABASE_FILE = DATABASE_DIR / "magic.db"

SCHEMA_FILE = DATABASE_DIR / "schema.sql"


def create_database():

    DATABASE_DIR.mkdir(exist_ok=True)

    connection = sqlite3.connect(DATABASE_FILE)

    with open(SCHEMA_FILE, encoding="utf-8") as f:
        connection.executescript(f.read())

    connection.commit()
    connection.close()

    return DATABASE_FILE
