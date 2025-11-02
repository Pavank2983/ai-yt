from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.api_usage import ApiUsageCreate
from app.services.api_usage_service import create_api_usage, get_api_usages

router = APIRouter()

@router.post("/")
def add_api_usage(data: ApiUsageCreate, db: Session = Depends(get_db)):
    return create_api_usage(db, data)

@router.get("/")
def list_api_usages(db: Session = Depends(get_db)):
    return get_api_usages(db)
