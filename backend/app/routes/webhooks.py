from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.webhook import WebhookCreate
from app.services.webhook_service import create_webhook, get_webhooks

router = APIRouter()

@router.post("/")
def add_webhook(data: WebhookCreate, db: Session = Depends(get_db)):
    return create_webhook(db, data)

@router.get("/")
def list_webhooks(db: Session = Depends(get_db)):
    return get_webhooks(db)
