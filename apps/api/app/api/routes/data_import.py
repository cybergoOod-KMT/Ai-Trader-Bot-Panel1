from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_current_user
from app.db.models import User
from app.schemas.data_import import CsvImportResponse
from app.services.backtest_engine import backtest_engine

router = APIRouter(prefix="/data/import", tags=["data-import"])


@router.post("/csv", response_model=CsvImportResponse)
async def import_csv(
    file: UploadFile = File(...),
    _: User = Depends(get_current_user),
) -> CsvImportResponse:
    payload = await file.read()
    result = await backtest_engine.import_csv(payload, file.filename or "dataset.csv")
    return CsvImportResponse(**result)
