from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from app.db.database import get_db
from app.schemas.auth_schema import UserCreate, UserLogin, Token
from app.schemas.user import UserResponse
from app.services.auth_service import register_user, login_user
from app.core.security import get_current_user
from app.config.settings import settings

router = APIRouter(prefix="/auth")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# -------------------------
# 🧩 Register New User
# -------------------------
@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    return register_user(user, db)


# -------------------------
# 🔐 User Login
# -------------------------
@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    return login_user(user, db)


# -------------------------
# 👤 Get Current User Profile
# -------------------------
@router.get("/me", response_model=UserResponse)
def get_profile(current_user=Depends(get_current_user)):
    """
    Returns the currently authenticated user's data.
    """
    return current_user
