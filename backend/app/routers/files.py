from fastapi import APIRouter, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
import pandas as pd
import io
from app.database import get_db
from app.models.db_models import UploadedFile

router = APIRouter()

@router.post("/upload")
async def upload(file: UploadFile, db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="You can only upload a CSV file.")

    content = await file.read()
    df = pd.read_csv(io.BytesIO(content))

    record = UploadedFile(
        filename=file.filename,
        row_count=len(df),
        column_count=len(df.columns),
        columns=list(df.columns),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return {
        "id": record.id,
        "filename": record.filename,
        "row_count": record.row_count,
        "column_count": record.column_count,
        "columns": record.columns,
        "uploaded_at": record.uploaded_at,
    }