import os
from fastapi import HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import User
from app.schemas.auth_schema import UserCreate, UserLogin
from app.core.security import hash_password, verify_password, create_access_token
from sqlalchemy.exc import IntegrityError

def register_user(user: UserCreate, db: Session):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_pw = hash_password(user.password)
    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed_pw,
    )
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    return {"message": "User registered successfully"}

def login_user(login_data: UserLogin, db: Session):
    user = db.query(User).filter(User.email == login_data.email).first()

    # Email not registered
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )

    # Wrong password
    if not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    # Create JWT token
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}
    )

    # Prepare response
    response = JSONResponse(
        content={
            "message": "Login successful",
            "access_token": access_token,
            "token_type": "bearer",
            "role": user.role,
        }
    )

    # Store token in HttpOnly Secure Cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure= os.getenv("APP_ENV") != "development",      # change to True in production (HTTPS)
        samesite="lax",
        max_age=60 * 60 * 24 * 7,   # 7 days
        path="/"
    )

    return response

def logout_user():
    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie("access_token", path="/")
    return response