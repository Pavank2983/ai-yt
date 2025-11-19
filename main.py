import os
import logging
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager

from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

# Routes
from app.routes import auth_route, scripts, script_bulk, voices, videos

# Job processor functions (new architecture)
from app.services.video_job_service import (
    process_queued_jobs,
    process_running_jobs
)

# Load environment variables
load_dotenv()

# ==============================================================
#  LOGGING CONFIGURATION
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
    encoding="utf-8"
)
app_formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
app_handler.setFormatter(app_formatter)
app_logger.addHandler(app_handler)

# --- Scheduler Logger ---
scheduler_logger = logging.getLogger("scheduler_logger")
scheduler_logger.setLevel(logging.INFO)
scheduler_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "scheduler.log"),
    maxBytes=5_000_000,
    backupCount=5,
    encoding="utf-8"
)
scheduler_handler.setFormatter(app_formatter)
scheduler_logger.addHandler(scheduler_handler)

# --- Console Logging for Development ---
console_handler = logging.StreamHandler()
console_handler.setFormatter(app_formatter)
app_logger.addHandler(console_handler)
scheduler_logger.addHandler(console_handler)

# ==============================================================
#  APSCHEDULER SETUP USING FASTAPI LIFESPAN
# ==============================================================

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):

    cron_expr = os.getenv("VIDEO_JOB_CRON", "*/1 * * * *")  # Every 1 minute
    trigger = CronTrigger.from_crontab(cron_expr)

    # Add scheduler job only once
    if not scheduler.get_jobs():
        scheduler.add_job(
            lambda: run_job_cycle(),
            trigger,
            id="video_job_cycle",
            replace_existing=True
        )
        scheduler.start()

        scheduler_logger.info(f"🕒 Video Job Scheduler started (cron: {cron_expr})")
        app_logger.info(f"✅ FastAPI startup complete. Scheduler running every {cron_expr}")

    yield  # FastAPI runs here

    # Shutdown logic
    try:
        scheduler.shutdown(wait=False)
        scheduler_logger.info("🛑 Scheduler stopped gracefully.")
    except Exception as e:
        scheduler_logger.error(f"⚠️ Scheduler shutdown error: {e}")


# ==============================================================
#  JOB CYCLE (queued + running)
# ==============================================================

def run_job_cycle():
    """Runs both phases: submit queued → poll running."""
    try:
        scheduler_logger.info("🔵 Scheduler cycle started")
        process_queued_jobs(limit=5)
        process_running_jobs(limit=5)
        scheduler_logger.info("🟢 Scheduler cycle completed")
    except Exception as e:
        scheduler_logger.error(f"❌ Scheduler cycle error: {e}")


# ==============================================================
#  FASTAPI INITIALIZATION
# ==============================================================

app = FastAPI(
    title="AI YouTube Automation API",
    lifespan=lifespan
)

# Routers
app.include_router(auth_route.router, tags=["Authentication"])
app.include_router(scripts.router, tags=["Script Generation"])
app.include_router(script_bulk.router, tags=["Bulk Script Generation"])
app.include_router(voices.router, tags=["TTS Voice Generation"])
app.include_router(videos.router, tags=["Video Generation"])

# Root endpoint
@app.get("/")
def root():
    app_logger.info("Root endpoint accessed")
    return {"message": "🚀 AI YouTube Automation API is running!"}
