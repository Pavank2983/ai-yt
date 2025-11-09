from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.platform import PlatformCreate
from app.services.platform_service import create_platform, get_platforms

router = APIRouter()

@router.post("/")
def add_platform(data: PlatformCreate, db: Session = Depends(get_db)):
    return create_platform(db, data)

@router.get("/")
def list_platforms(db: Session = Depends(get_db)):
    return get_platforms(db)
