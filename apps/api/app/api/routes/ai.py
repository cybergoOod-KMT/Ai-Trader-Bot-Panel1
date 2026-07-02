from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import AiDecision, User
from app.schemas.ai import AiAnalyzeRequest, AiDecisionResponse, AiExecuteRequest, AiExecuteResponse
from app.services.ai_engine import AiEngine

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/analyze", response_model=AiDecisionResponse)
async def analyze_ai_signal(
    payload: AiAnalyzeRequest,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AiDecisionResponse:
    result = await AiEngine().analyze(db, payload.symbol)
    return AiDecisionResponse(**result)


@router.post("/execute", response_model=AiExecuteResponse)
async def execute_ai_signal(
    payload: AiExecuteRequest,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AiExecuteResponse:
    result = await AiEngine().execute(db, payload.decision_id, payload.prefer_real_execution, payload.confirm_token)
    return AiExecuteResponse(**result)


@router.get("/decisions", response_model=list[AiDecisionResponse])
def list_ai_decisions(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AiDecisionResponse]:
    rows = db.scalars(select(AiDecision).order_by(AiDecision.created_at.desc()).limit(100)).all()
    return [AiDecisionResponse(**AiEngine.serialize(item)) for item in rows]


@router.get("/decisions/{decision_id}", response_model=AiDecisionResponse)
def get_ai_decision(
    decision_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AiDecisionResponse:
    row = db.get(AiDecision, decision_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI decision not found.")
    return AiDecisionResponse(**AiEngine.serialize(row))
