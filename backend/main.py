from fastapi.staticfiles import StaticFiles
import os
import logging
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

# Routes
from app.routes import auth_route, scripts, voices, videos, dashboard
from app.api.public import approval_links
from app.api.webhooks import whatsapp_webhook

# ✅ SINGLE SOURCE OF TRUTH — scheduler logic
from app.scripts.run_scheduler import (
    process_queued_jobs,
    process_running_jobs,
)

# Load environment variables
load_dotenv()

# ==============================================================
# LOGGING CONFIGURATION
# ==============================================================

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# --- App Logger ---
app_logger = logging.getLogger("app_logger")
app_logger.setLevel(logging.INFO)

app_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "app.log"),
    maxBytes=5_000_000,
    backupCount=5,
    encoding="utf-8",
)
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
app_handler.setFormatter(formatter)
app_logger.addHandler(app_handler)

# --- Scheduler Logger ---
scheduler_logger = logging.getLogger("scheduler_logger")
scheduler_logger.setLevel(logging.INFO)

scheduler_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "scheduler.log"),
    maxBytes=5_000_000,
    backupCount=5,
    encoding="utf-8",
)
scheduler_handler.setFormatter(formatter)
scheduler_logger.addHandler(scheduler_handler)

# --- Console Logging ---
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
app_logger.addHandler(console_handler)
scheduler_logger.addHandler(console_handler)

# ==============================================================
# APSCHEDULER SETUP (CRON-DRIVEN)
# ==============================================================

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):

    cron_expr = os.getenv("VIDEO_JOB_CRON", "*/1 * * * *")  # every 1 minute
    trigger = CronTrigger.from_crontab(cron_expr)

    if not scheduler.get_jobs():
        scheduler.add_job(
            func=run_job_cycle,
            trigger=trigger,
            id="video_job_scheduler",
            replace_existing=True,
        )
        scheduler.start()

        scheduler_logger.info(
            f"🕒 Video Job Scheduler started (cron: {cron_expr})"
        )
        app_logger.info("✅ FastAPI startup complete")

    yield

    try:
        scheduler.shutdown(wait=False)
        scheduler_logger.info("🛑 Scheduler stopped gracefully")
    except Exception as e:
        scheduler_logger.error(f"⚠️ Scheduler shutdown error: {e}")

# ==============================================================
# JOB CYCLE — DELEGATED TO run_scheduler.py
# ==============================================================

def run_job_cycle():
    """
    ONE authoritative scheduler cycle.
    """
    try:
        scheduler_logger.info("🔵 Scheduler cycle started")
        process_queued_jobs()
        process_running_jobs()
        scheduler_logger.info("🟢 Scheduler cycle completed")
    except Exception as e:
        scheduler_logger.error(f"❌ Scheduler cycle error: {e}", exc_info=True)

# ==============================================================
# FASTAPI APP
# ==============================================================

app = FastAPI(
    title="AI YouTube Automation API",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = [
    os.getenv("FRONTEND_URL"),  # frontend
    # "https://yourdomain.com"  # production later
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # ❌ never use ["*"] with auth
    allow_credentials=False,        # ✅ header-based auth (no cookies)
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/assets",
    StaticFiles(directory="assets"),
    name="assets"
)

# Routers
app.include_router(auth_route.router, tags=["Authentication"])
app.include_router(scripts.router, tags=["Script Generation"])
app.include_router(voices.router, tags=["TTS Voice Generation"])
app.include_router(videos.router, tags=["Video Generation"])
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(approval_links.router, tags=["Approval Video Links"])
app.include_router(whatsapp_webhook.router, tags=["Whatsapp Webhooks"])

# Root endpoint
@app.get("/")
def root():
    app_logger.info("Root endpoint accessed")
    return {"message": "🚀 AI YouTube Automation API is running!"}
