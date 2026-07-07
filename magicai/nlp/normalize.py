import re
import unicodedata


def normalize(text: str) -> str:

    text = text.lower()

    text = unicodedata.normalize("NFD", text)

    text = "".join(
        c
        for c in text
        if unicodedata.category(c) != "Mn"
    )

    text = text.replace("¿", "")
    text = text.replace("?", "")
    text = text.replace("¡", "")
    text = text.replace("!", "")

    text = re.sub(r"\s+", " ", text)

    return text.strip()