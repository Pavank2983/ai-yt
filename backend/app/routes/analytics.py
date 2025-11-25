from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.analytic import AnalyticCreate
from app.services.analytic_service import create_analytic, get_analytics

router = APIRouter()

@router.post("/")
def add_analytic(data: AnalyticCreate, db: Session = Depends(get_db)):
    return create_analytic(db, data)

@router.get("/")
def list_analytics(db: Session = Depends(get_db)):
    return get_analytics(db)
