#!/usr/bin/env python3

from magicai.context_builder import build_context


def main():

    print("=" * 60)
    print(" MagicAI Context Builder")
    print("=" * 60)

    while True:

        question = input("> ")

        if not question:
            break

        context = build_context(question)

        print()
        print(context)
        print()


if __name__ == "__main__":
    main()