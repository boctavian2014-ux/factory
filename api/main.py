"""
AI Content Factory — FastAPI gateway.
Mounts trend, idea, script, video, virality, and scheduler services.
"""
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

from shared.config import settings
from shared.database import init_db

# Import routers from services (underscore package names for Python import)
from services.trend_service.main import router as trend_router
from services.idea_service.main import router as idea_router
from services.script_service.main import router as script_router
from services.video_service.main import router as video_router
from services.virality_service.main import router as virality_router
from services.scheduler_service.main import router as scheduler_router
from services.clip_service.main import router as clip_router
from services.repo_service.main import router as repo_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup. If DB is unavailable (e.g. no Docker), app still starts for dashboard/docs."""
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning("Database init skipped (not available): %s", e)
    yield
    logger.info("Shutdown")


app = FastAPI(
    title=settings.app_name,
    description="Scalable AI Content Factory for short-form video generation, scoring, and scheduling.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,  # custom /docs with same-style theme
    redoc_url=None,  # custom /redoc with same-style theme
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trend_router)
app.include_router(idea_router)
app.include_router(script_router)
app.include_router(video_router)
app.include_router(virality_router)
app.include_router(scheduler_router)
app.include_router(clip_router)
app.include_router(repo_router)

# Static files (theme, overrides for docs)
_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

_DASHBOARD_PATH = _STATIC_DIR / "dashboard.html"
_RUN_PATH = _STATIC_DIR / "run.html"


@app.get("/", response_class=HTMLResponse)
def root():
    """Dashboard — același stil în toată aplicația."""
    if _DASHBOARD_PATH.exists():
        return FileResponse(_DASHBOARD_PATH, media_type="text/html")
    return HTMLResponse("<h1>AI Content Factory</h1><p><a href='/docs'>API Docs</a> | <a href='/health'>Health</a></p>", status_code=200)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page():
    """Dashboard (alias for /)."""
    return root()


@app.get("/run", response_class=HTMLResponse)
def run_page():
    """Run pipeline — trigger pași din UI."""
    if _RUN_PATH.exists():
        return FileResponse(_RUN_PATH, media_type="text/html")
    return HTMLResponse("<h1>Run not found</h1><p><a href='/'>Dashboard</a></p>", status_code=404)


# Docs cu același stil (theme dark)
@app.get("/docs", include_in_schema=False)
def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " — API",
        swagger_ui_parameters={"customCssUrl": "/static/swagger-override.css"},
    )


@app.get("/redoc", include_in_schema=False)
def custom_redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " — API",
        redoc_ui_parameters={"customCssUrl": "/static/redoc-override.css"},
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-content-factory"}
