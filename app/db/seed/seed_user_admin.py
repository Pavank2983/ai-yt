from datetime import datetime
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password

def seed_admin_user():
    db: Session = SessionLocal()

    admin = db.query(User).filter_by(email="pavank9415@gmail.com").first()
    if admin:
        print("✅ Admin user already exists.")
        db.close()
        return

    user = User(
        name="Admin",
        email="pavank9415@gmail.com",
        password=hash_password("123456"),
        role="admin",
        status="active",
        created_at=datetime.utcnow()
    )

    db.add(user)
    db.commit()
    db.close()
    print("✅ Default admin user created with ID 1 (email: pavank9415@gmail.com, password: 123456)")

if __name__ == "__main__":
    seed_admin_user()
