from pathlib import Path
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from geopolitical_market_forecaster.config import get_settings
from geopolitical_market_forecaster.decisions import build_sector_decisions
from geopolitical_market_forecaster.ingestion import NewsIngestionService
from geopolitical_market_forecaster.orchestration.pipeline import ForecastPipeline
from geopolitical_market_forecaster.realtime import (
    ConnectionManager,
    background_poll,
    dashboard_payload,
    run_ingestion_and_pipeline,
)
from geopolitical_market_forecaster.storage import (
    dashboard_summary,
    initialize_database,
    list_dashboard_signals,
    record_audit_event,
    save_news_items,
)

manager = ConnectionManager()
poll_stop_event = asyncio.Event()
poll_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global poll_task
    settings = get_settings()
    initialize_database(settings.database_url)
    if settings.enable_background_polling:
        poll_stop_event.clear()
        poll_task = asyncio.create_task(background_poll(settings, manager, poll_stop_event))
    yield
    if poll_task:
        poll_stop_event.set()
        poll_task.cancel()
        try:
            await poll_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="Geopolitical Market Forecaster", lifespan=lifespan)
PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = PACKAGE_DIR / "templates"
STATIC_DIR = PACKAGE_DIR / "static"

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR), check_dir=True),
    name="static",
)


@app.get("/health")
async def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "environment": settings.app_env}


@app.post("/pipeline/run")
async def run_pipeline() -> dict:
    settings = get_settings()
    result = await ForecastPipeline(settings).run()
    await manager.broadcast(dashboard_payload(settings, "pipeline_run"))
    return result.model_dump(mode="json")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    return await dashboard(request)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    settings = get_settings()
    initialize_database(settings.database_url)
    signals = list_dashboard_signals(settings.database_url)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "summary": dashboard_summary(settings.database_url),
            "signals": signals,
            "sector_decisions": build_sector_decisions(signals),
            "analysis_provider": settings.resolved_analysis_provider(),
        },
    )


@app.get("/api/dashboard")
async def dashboard_data() -> dict:
    settings = get_settings()
    initialize_database(settings.database_url)
    payload = dashboard_payload(settings, "snapshot")
    payload["analysis_provider"] = settings.resolved_analysis_provider()
    return payload


@app.post("/api/ingest/run")
async def ingest_and_refresh(source: str = "auto") -> dict:
    settings = get_settings()
    initialize_database(settings.database_url)
    result = await run_ingestion_and_pipeline(settings, source)
    await manager.broadcast(dashboard_payload(settings, "manual_refresh"))
    return result


@app.websocket("/ws/alerts")
async def alerts_socket(websocket: WebSocket) -> None:
    settings = get_settings()
    await manager.connect(websocket)
    try:
        await websocket.send_json(dashboard_payload(settings, "connected"))
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
