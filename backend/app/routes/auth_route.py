from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from app.db.database import get_db
from app.schemas.auth_schema import UserCreate, UserLogin, Token
from app.schemas.user import UserResponse
from app.services.auth_service import register_user, login_user, logout_user
from app.core.security import get_current_user, decode_access_token
from app.config.settings import settings
from app.models.user import User

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
# 🔐 User Logout
# -------------------------
@router.post("/logout", response_model=Token)
def login():
    return logout_user()


# -------------------------
# 👤 Get Current User Profile
# -------------------------
@router.get("/me")
def current_user(request: Request, db: Session = Depends(get_db)):
    # 1. Extract token from Authorization Header or Cookie
    token = None

    # Priority 1: Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    # Priority 2: Cookie
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # 2. Validate token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user_email = payload.get("sub")

    # 3. Fetch user from DB
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 4. Return user info (NO password)
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
    }
