from sqlalchemy.orm import Session
from app.models.webhook import Webhook
from app.schemas.webhook import WebhookCreate

def create_webhook(db: Session, data: WebhookCreate):
    webhook = Webhook(name=data.name, description=data.description)
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return webhook

def get_webhooks(db: Session):
    return db.query(Webhook).all()
