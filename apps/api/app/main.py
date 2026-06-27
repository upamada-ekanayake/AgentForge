from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import status as http_status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import check_database_connection, close_database_connection
from app.models import import_all_models

import_all_models()

from app.modules.applications.router import router as applications_router
from app.modules.agents.router import router as agents_router
from app.modules.documents.router import router as documents_router
from app.modules.internships.router import router as internships_router
from app.modules.users.router import router as users_router
from app.modules.workspaces.router import router as workspaces_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await close_database_connection()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["system"])
    async def health_check() -> JSONResponse:
        database_connected = await check_database_connection()
        payload = {
            "status": "ok" if database_connected else "error",
            "database": "connected" if database_connected else "disconnected",
            "service": settings.app_name,
        }
        response_status = (
            http_status.HTTP_200_OK
            if database_connected
            else http_status.HTTP_503_SERVICE_UNAVAILABLE
        )

        return JSONResponse(status_code=response_status, content=payload)

    app.include_router(users_router)
    app.include_router(workspaces_router)
    app.include_router(documents_router)
    app.include_router(internships_router)
    app.include_router(applications_router)
    app.include_router(agents_router)

    return app


app = create_app()
