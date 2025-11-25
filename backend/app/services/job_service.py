from sqlalchemy.orm import Session
from app.models.job import Job
from app.schemas.job import JobCreate

def create_job(db: Session, data: JobCreate):
    job = Job(name=data.name, description=data.description)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def get_jobs(db: Session):
    return db.query(Job).all()
