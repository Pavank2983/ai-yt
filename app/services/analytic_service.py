from sqlalchemy.orm import Session
from app.models.analytic import Analytic
from app.schemas.analytic import AnalyticCreate

def create_analytic(db: Session, data: AnalyticCreate):
    analytic = Analytic(name=data.name, description=data.description)
    db.add(analytic)
    db.commit()
    db.refresh(analytic)
    return analytic

def get_analytics(db: Session):
    return db.query(Analytic).all()
