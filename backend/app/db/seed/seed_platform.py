import logging
from datetime import datetime, timezone
import os

from app.db.database import SessionLocal
from app.models.platform import Platform

logger = logging.getLogger("platform_seeder")
logger.setLevel(logging.INFO)

if not logger.handlers:
    os.makedirs("logs", exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    fh = logging.FileHandler("logs/platform_seeder.log", encoding="utf-8")
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)


def seed_platforms():
    db = SessionLocal()

    try:
        platforms = [
            {"name": "youtube", "enabled": True},
            {"name": "instagram", "enabled": False},
            {"name": "tiktok", "enabled": False},
        ]

        for p in platforms:
            existing = (
                db.query(Platform)
                .filter(Platform.name == p["name"])
                .first()
            )

            if existing:
                logger.info(f"⏭️ Platform already exists: {p['name']}")
                continue

            new_platform = Platform(
                name=p["name"],
                enabled=p["enabled"],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            db.add(new_platform)

            logger.info(f"✅ Added platform: {p['name']}")

        db.commit()
        logger.info("🎉 Platform seeding completed")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Seeder failed: {e}", exc_info=True)

    finally:
        db.close()


if __name__ == "__main__":
    seed_platforms()