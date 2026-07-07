#!/usr/bin/env python3

import sys

from magicai.services.rule_service import find_rule


def main():

    if len(sys.argv) < 2:
        print("Uso:")
        print('python scripts/search_rule.py "Undying"')
        return

    result = find_rule(sys.argv[1])

    if result is None:
        print("No se ha encontrado ninguna regla.")
        return

    print("=" * 60)
    print(result["title"])
    print("=" * 60)
    print()

    for rule_number, text in result["rules"]:

        print(rule_number)
        print(text)
        print()


if __name__ == "__main__":
    main()