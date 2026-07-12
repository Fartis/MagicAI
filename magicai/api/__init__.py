from fastapi import FastAPI

from magicai.api.errors import install_error_handlers
from magicai.api.routes import router
from magicai.versioning import get_project_version


app = FastAPI(
    title="MagicAI",
    version=get_project_version(),
)

install_error_handlers(app)
app.include_router(router)
