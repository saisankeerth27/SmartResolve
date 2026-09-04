import logging
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from src.api.schemas import HealthResponse
from src.core.config import SERVICE_NAME, GEMINI_CONFIGURED, FRONTEND_DIST

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=SERVICE_NAME,
        gemini_configured=GEMINI_CONFIGURED,
    )


def serve_frontend(app) -> None:
    dist = FRONTEND_DIST
    index_file = dist / "index.html"

    if not dist.exists() or not index_file.exists():
        @app.get("/{full_path:path}")
        async def serve_frontend_fallback(full_path: str):
            return JSONResponse(
                status_code=200,
                content={
                    "message": "SmartResolve API is running. Frontend not built yet.",
                    "hint": "Run 'npm run build' inside frontend/ to build the UI.",
                    "docs": "/docs",
                },
            )
        return

    @app.get("/{full_path:path}")
    async def serve_frontend_assets(full_path: str):
        file_path = dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(index_file)
