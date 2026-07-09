from fastapi import FastAPI

from magicai.api.routes import router


app = FastAPI(
    title="MagicAI",
    version="0.1.0",
)

app.include_router(router)
