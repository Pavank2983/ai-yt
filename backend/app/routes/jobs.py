from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.job import JobCreate
from app.services.job_service import create_job, get_jobs

router = APIRouter()

@router.post("/")
def add_job(data: JobCreate, db: Session = Depends(get_db)):
    return create_job(db, data)

@router.get("/")
def list_jobs(db: Session = Depends(get_db)):
    return get_jobs(db)
