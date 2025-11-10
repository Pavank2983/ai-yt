from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.script_bulk_service import bulk_generate_scripts
from app.core.security import role_required
from datetime import datetime
import openai
from openai import OpenAI

router = APIRouter(tags=["Bulk Script Generation"])


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
