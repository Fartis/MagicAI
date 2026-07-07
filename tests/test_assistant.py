from magicai.assistant import MagicAI
from magicai.conversation import Conversation

assistant = MagicAI()

conversation = Conversation()

while True:

    question = input("> ").strip()

    if not question:
        break

    print()
    print(assistant.ask(conversation, question))
    print()

    print()
    print(conversation.active_cards)
    print(len(conversation.history))
    print()