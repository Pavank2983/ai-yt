from app.db.database import Base, engine
from app.models import user, category, script, video, platform
from sqlalchemy import text

print("⚙️ Reinitializing database...")

with engine.connect() as conn:
    # 🔒 Disable FK checks temporarily
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))

    # Drop all existing tables
    Base.metadata.drop_all(bind=engine)

    # Re-enable FK checks
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))

    # Recreate tables
    Base.metadata.create_all(bind=engine)

    conn.commit()

print("✅ Database reset and tables recreated successfully!")
