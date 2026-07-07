import requests

response = requests.post(
    "http://127.0.0.1:11434/api/chat",
    json={
        "model": "qwen3:8b",
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": """
You are an intent parser.

Return ONLY valid JSON.

Schema:

{
  "language":"",
  "intent":"",
  "cards":[],
  "keywords":[],
  "rules":[]
}

Never answer the question.
Never invent card data.
Never invent Oracle text.
Never add extra fields.
"""
            },
            {
                "role": "user",
                "content": "¿Qué hace Prossh, Skyraider of Kher?"
            }
        ]
    }
)

print(response.json()["message"]["content"])