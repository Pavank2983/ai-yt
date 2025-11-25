from sqlalchemy.orm import Session
from app.models.automation_log import AutomationLog
from app.schemas.automation_log import AutomationLogCreate

def create_automation_log(db: Session, data: AutomationLogCreate):
    automation_log = AutomationLog(name=data.name, description=data.description)
    db.add(automation_log)
    db.commit()
    db.refresh(automation_log)
    return automation_log

def get_automation_logs(db: Session):
    return db.query(AutomationLog).all()
