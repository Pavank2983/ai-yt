from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.automation_log import AutomationLogCreate
from app.services.automation_log_service import create_automation_log, get_automation_logs

router = APIRouter()

@router.post("/")
def add_automation_log(data: AutomationLogCreate, db: Session = Depends(get_db)):
    return create_automation_log(db, data)

@router.get("/")
def list_automation_logs(db: Session = Depends(get_db)):
    return get_automation_logs(db)
