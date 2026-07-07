#!/usr/bin/env python3

from magicai.assistant.router import answer_question


def print_card(card):

    print()
    print("=" * 60)
    print(card["name"])
    print("=" * 60)

    print()

    print(card.get("type_line"))

    if card.get("mana_cost"):
        print(card["mana_cost"])

    if card.get("power"):
        print(f'{card["power"]}/{card["toughness"]}')

    print()

    print(card.get("oracle_text"))

    print()


def print_rule(rule):

    print()
    print("=" * 60)
    print(rule["title"])
    print("=" * 60)
    print()

    for number, text in rule["rules"]:

        print(number)
        print(text)
        print()


def main():

    print("=" * 60)
    print(" MagicAI 0.1")
    print("=" * 60)

    while True:

        question = input("> ").strip()

        if question.lower() in ("exit", "quit", "salir"):
            break

        answer = answer_question(question)

        if answer["kind"] == "card":

            print_card(answer["data"]["results"][0])

            continue

        if answer["kind"] == "rule":

            print_rule(answer["data"])

            continue

        print()
        print("No he encontrado ninguna carta o regla.")
        print()


if __name__ == "__main__":
    main()