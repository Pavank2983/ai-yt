from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate

def create_notification(db: Session, data: NotificationCreate):
    notification = Notification(name=data.name, description=data.description)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification

def get_notifications(db: Session):
    return db.query(Notification).all()
