from magicai.llm.intent_parser import parse_intent

while True:

    q = input("> ")

    print(parse_intent(q))