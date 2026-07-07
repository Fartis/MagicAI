from magicai.context_builder import build_context
from magicai.context_enricher import enrich
from magicai.knowledge_builder import build_knowledge

while True:

    question = input("> ")

    context = build_context(question)

    context = enrich(context)

    print()

    print(build_knowledge(context))

    print()