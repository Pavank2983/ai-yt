from datetime import datetime, timedelta, UTC
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config.settings import settings
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -----------------------------
# 🔑 Password Utilities
# -----------------------------
def hash_password(password: str) -> str:
    password = password.strip()
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password length exceeds 72 characters (bcrypt limit)")
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# -----------------------------
# 🔐 JWT Token Utilities
# -----------------------------
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Expiry check
        if payload.get("exp") and datetime.utcnow().timestamp() > payload["exp"]:
            return None

        return payload

    except JWTError:
        return None

# -----------------------------
# 👤 Current User Dependency
# -----------------------------
def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Extracts user from JWT token (cookie-first, bearer fallback)
    """
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    jwt_token = request.cookies.get("access_token")

    if not jwt_token:
        raise credentials_exception

    try:
        payload = jwt.decode(
            jwt_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        email = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise credentials_exception

    return user

# -----------------------------
# 🧩 Role-Based Access Utility
# -----------------------------
def role_required(required_role: str):
    """
    Role-based dependency to restrict route access.
    Usage:
        @router.get("/admin", dependencies=[Depends(role_required("admin"))])
    """
    def role_checker(current_user: User = Depends(get_current_user)):
        hierarchy = {"viewer": 1, "editor": 2, "admin": 3}

        user_role_level = hierarchy.get(current_user.role, 0)
        required_level = hierarchy.get(required_role, 0)

        if user_role_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires '{required_role}' role"
            )

        return current_user

    return role_checker