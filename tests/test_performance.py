from magicai.assistant import MagicAI
from magicai.conversation import Conversation


assistant = MagicAI()


SCENARIOS = [

    {
        "name": "Card basics",
        "questions": [
            "¿Qué hace Young Wolf?",
            "¿Y si muere?",
            "¿Y si lo sacrifico?",
            "¿Y si lo exilio?",
        ],
    },

    {
        "name": "Rule lookup - Undying",
        "questions": [
            "¿Qué dice la regla 702.93?",
            "Explícame Undying con un ejemplo sencillo.",
        ],
    },

    {
        "name": "Layers",
        "questions": [
            "¿Qué dice la regla 613 sobre las capas de Magic?",
            "Explícame de forma sencilla cómo funcionan las capas.",
            "Si una criatura tiene un efecto que fija su fuerza y resistencia y otro que le da +1/+1, ¿qué se aplica antes?",
        ],
    },

    {
        "name": "Priority",
        "questions": [
            "¿Qué dice la regla 117 sobre prioridad?",
            "Explícame cómo funciona la prioridad en Magic.",
            "Si lanzo un hechizo, ¿mi oponente puede responder antes de que se resuelva?",
        ],
    },

    {
        "name": "Commander interaction",
        "questions": [
            "¿Qué hace Korvold, Fae-Cursed King?",
            "¿Qué ocurre si sacrifico un permanente con Korvold en mesa?",
            "¿Y si sacrifico una criatura?",
        ],
    },

    {
        "name": "Topic switch",
        "questions": [
            "¿Qué hace Sol Ring?",
            "¿Merece la pena jugarlo en Commander?",
            "Ahora explícame qué hace Lightning Bolt.",
        ],
    },

]


def run_scenario(name: str, questions: list[str]):

    print()
    print("#" * 80)
    print(name)
    print("#" * 80)
    print()

    conversation = Conversation()

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


def main():

    for scenario in SCENARIOS:

        run_scenario(
            scenario["name"],
            scenario["questions"],
        )


if __name__ == "__main__":

    main()