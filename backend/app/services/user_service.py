from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password(password: str):
    password = password.strip()
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password length exceeds 72 characters (bcrypt limit)")
    return pwd_context.hash(password)

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password(user.password)
    print(f"Password before hashing: {user.password!r} | Length: {len(user.password)} | hashed paswword: {hashed_password}")

    db_user = User(
        name=user.name,
        email=user.email,
        password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user