from magicai.assistant import MagicAI
from magicai.conversation import Conversation

assistant = MagicAI()

conversation = Conversation()

questions = [

    "¿Qué hace Young Wolf?",

    "¿Y si muere?",

    "¿Y si lo sacrifico?",

    "¿Y si lo exilio?"

]

for question in questions:

    print("=" * 80)
    print(question)
    print("=" * 80)

    answer = assistant.ask(
        conversation,
        question,
    )

    print(answer)
    print()