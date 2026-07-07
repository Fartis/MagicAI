import requests


OLLAMA_URL = "http://127.0.0.1:11434/api/chat"

MODEL = "qwen3:8b"


def generate(system: str, prompt: str):

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "stream": False,

            "keep_alive": "30m",

            "options": {
                "temperature": 0.2,
                "num_predict": 256,
            },

            "messages": [
                {
                    "role": "system",
                    "content": system,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        },
        timeout=300,
    )

    response.raise_for_status()

    payload = response.json()

    return payload["message"]["content"]