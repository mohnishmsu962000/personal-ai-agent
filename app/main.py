import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.routers.webhook import router as webhook_router
from app.tools.calendar import get_upcoming_events
from app.tools.notion import get_pending_tasks
from app.tools.telegram import send_daily_summary

logger = structlog.get_logger()
settings = get_settings()

scheduler = AsyncIOScheduler()


async def daily_summary_job():
    """Runs every morning and sends a summary to Telegram."""
    logger.info("daily_summary_job_started")
    events = await get_upcoming_events()
    tasks = await get_pending_tasks()
    await send_daily_summary(settings.telegram_allowed_user_id, events, tasks)
    logger.info("daily_summary_job_completed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("starting_up")
    scheduler.add_job(
        daily_summary_job,
        CronTrigger(
            hour=settings.daily_summary_hour,
            minute=settings.daily_summary_minute,
        ),
        id="daily_summary",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("scheduler_started")
    yield
    # Shutdown
    scheduler.shutdown()
    logger.info("scheduler_stopped")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="LangGraph-powered personal AI agent that manages tasks, events and reminders across Telegram, Google Calendar and Notion",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router)


@app.get("/", tags=["health"])
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}