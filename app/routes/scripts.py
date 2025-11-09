from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.script import ScriptCreate
from app.services.script_service import create_script, get_scripts

router = APIRouter()

@router.post("/")
def add_script(data: ScriptCreate, db: Session = Depends(get_db)):
    return create_script(db, data)

@router.get("/")
def list_scripts(db: Session = Depends(get_db)):
    return get_scripts(db)
