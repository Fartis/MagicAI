from fastapi import FastAPI

from magicai.api.routes import router


app = FastAPI(
    title="MagicAI",
    description="Magic: The Gathering AI Assistant",
    version="0.1.0",
)

app.include_router(router)