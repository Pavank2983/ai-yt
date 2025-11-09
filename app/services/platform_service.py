from sqlalchemy.orm import Session
from app.models.platform import Platform
from app.schemas.platform import PlatformCreate

def create_platform(db: Session, data: PlatformCreate):
    platform = Platform(name=data.name, description=data.description)
    db.add(platform)
    db.commit()
    db.refresh(platform)
    return platform

def get_platforms(db: Session):
    return db.query(Platform).all()
