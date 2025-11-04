from app.core.security import hash_password, verify_password, create_access_token
from jose import jwt
from app.config.settings import settings

def test_password_hashing():
    password = "secret123"
    hashed = hash_password(password)
    assert verify_password(password, hashed)

def test_jwt_creation_and_decode():
    token = create_access_token({"sub": "test@example.com"})
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded.get("sub") == "test@example.com"
