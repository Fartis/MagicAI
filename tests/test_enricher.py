from magicai.context_builder import build_context
from magicai.context_enricher import enrich

while True:

    q = input("> ")

    context = build_context(q)

    context = enrich(context)

    print()

    print(context)

    print()