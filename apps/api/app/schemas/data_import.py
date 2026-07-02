from pydantic import BaseModel


class CsvImportResponse(BaseModel):
    dataset_id: str
    rows: int
    symbol_hint: str | None = None
