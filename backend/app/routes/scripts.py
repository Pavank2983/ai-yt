from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.script import ScriptCreate, ScriptResponse
from app.services.script_service import create_script
from app.services.script_bulk_service import bulk_generate_scripts
from app.core.security import role_required
from datetime import datetime
import openai

router = APIRouter(prefix="/scripts")

@router.post("/generate", response_model=ScriptResponse)
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
    
@router.post("/bulk-generate")
def bulk_generate_scripts_endpoint(
    count: int = Query(5, ge=1, le=50, description="Number of scripts to generate (max 50)"),
    db: Session = Depends(get_db),
    current_user=Depends(role_required("editor"))
):
    """
    🎬 Generate multiple unique AI scripts (random category per script).

    - Randomly selects categories
    - Validates uniqueness
    - Creates ScriptGenerationJob
    """

    try:
        job = bulk_generate_scripts(db=db, user_id=current_user.id, count=count)

        return {
            "message": f"✅ Successfully generated {job.generated_count}/{job.requested_count} scripts.",
            "job": {
                "id": job.id,
                "status": job.status,
                "requested_count": job.requested_count,
                "generated_count": job.generated_count,
                "created_by": current_user.email,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
            },
        }

    except openai.RateLimitError:
        raise HTTPException(status_code=429, detail="⚠️ OpenAI quota exceeded. Please check your billing plan.")
    
    except openai.AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid or expired OpenAI API key.")
    
    except openai.APIConnectionError:
        raise HTTPException(status_code=503, detail="Cannot connect to OpenAI API.")
    
    except openai.OpenAIError as e:
        raise HTTPException(status_code=500, detail=f"OpenAI internal error: {str(e)}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
