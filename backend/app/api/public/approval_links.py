from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.approval_token import ApprovalAction
from app.services.approval.approval_token_service import get_token_record
from app.services.approval.approval_service import process_approval_token, ApprovalError


router = APIRouter(prefix="/w")


@router.get("/approve/{token}", response_class=HTMLResponse)
def approve_video(token: str, db: Session = Depends(get_db)):

    token_record = get_token_record(db, token)

    if not token_record:
        raise HTTPException(status_code=404, detail="Invalid token")

    if token_record.action != ApprovalAction.approve:
        raise HTTPException(status_code=400, detail="Invalid approval link")

    try:
        process_approval_token(db, token_record)
    except ApprovalError as e:
        return HTMLResponse(f"<h2>Approval failed: {str(e)}</h2>")

    return HTMLResponse(
        "<h2>✅ Video Approved Successfully</h2>"
    )


@router.get("/reject/{token}", response_class=HTMLResponse)
def reject_video(token: str, db: Session = Depends(get_db)):

    token_record = get_token_record(db, token)

    if not token_record:
        raise HTTPException(status_code=404, detail="Invalid token")

    if token_record.action != ApprovalAction.reject:
        raise HTTPException(status_code=400, detail="Invalid rejection link")

    try:
        process_approval_token(db, token_record)
    except ApprovalError as e:
        return HTMLResponse(f"<h2>Rejection failed: {str(e)}</h2>")

    return HTMLResponse(
        "<h2>❌ Video Rejected</h2>"
    )