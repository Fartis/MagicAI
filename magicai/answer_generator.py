from magicai.llm.ollama import generate
from magicai.prompts.answer import SYSTEM_PROMPT


def generate_answer(knowledge: str) -> str:
    """
    Genera una respuesta utilizando únicamente el conocimiento proporcionado.
    """
    print("=" * 80)
    print("KNOWLEDGE SENT TO LLM")
    print("=" * 80)
    print(knowledge)
    print("=" * 80)
    response = generate(
        SYSTEM_PROMPT,
        knowledge,
    )

    return response.strip()