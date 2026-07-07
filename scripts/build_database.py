from magicai.database import create_database


def main():

    print("=" * 40)
    print(" MagicAI Database Builder")
    print("=" * 40)

    db = create_database()

    print()
    print("✓ Base creada correctamente")
    print(db)


if __name__ == "__main__":
    main()
