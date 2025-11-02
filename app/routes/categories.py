from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.category import CategoryCreate
from app.services.category_service import create_category, get_categories

router = APIRouter()

@router.post("/")
def add_category(data: CategoryCreate, db: Session = Depends(get_db)):
    return create_category(db, data)

@router.get("/")
def list_categories(db: Session = Depends(get_db)):
    return get_categories(db)
