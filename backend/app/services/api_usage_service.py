from sqlalchemy.orm import Session
from app.models.api_usage import ApiUsage
from app.schemas.api_usage import ApiUsageCreate

def create_api_usage(db: Session, data: ApiUsageCreate):
    api_usage = ApiUsage(name=data.name, description=data.description)
    db.add(api_usage)
    db.commit()
    db.refresh(api_usage)
    return api_usage

def get_api_usages(db: Session):
    return db.query(ApiUsage).all()
