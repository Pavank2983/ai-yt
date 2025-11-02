from sqlalchemy.orm import Session
from app.models.script import Script
from app.schemas.script import ScriptCreate

def create_script(db: Session, data: ScriptCreate):
    script = Script(name=data.name, description=data.description)
    db.add(script)
    db.commit()
    db.refresh(script)
    return script

def get_scripts(db: Session):
    return db.query(Script).all()
