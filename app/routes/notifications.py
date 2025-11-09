from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.notification import NotificationCreate
from app.services.notification_service import create_notification, get_notifications

router = APIRouter()

@router.post("/")
def add_notification(data: NotificationCreate, db: Session = Depends(get_db)):
    return create_notification(db, data)

@router.get("/")
def list_notifications(db: Session = Depends(get_db)):
    return get_notifications(db)
