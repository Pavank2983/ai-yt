from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.script import ScriptCreate, ScriptResponse
from app.services.script_service import create_script
from app.core.security import get_current_user, role_required

router = APIRouter(tags=["Script Generation"])


@router.post("/", response_model=ScriptResponse)
def generate_script_endpoint(
    data: ScriptCreate,
    db: Session = Depends(get_db),
    current_user=Depends(role_required("editor"))
):
    try:
        script = create_script(db, data, current_user.id)
        return script
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
