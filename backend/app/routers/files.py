from fastapi import APIRouter, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
import pandas as pd
import io
from app.database import get_db
from app.models.db_models import UploadedFile
from app.services.prediction_service import predict_anomalies
import numpy as np

router = APIRouter()

@router.post("/upload")
async def upload(file: UploadFile, db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="You can only upload a CSV file.")

    content = await file.read()
    df = pd.read_csv(io.BytesIO(content))

    # Run ML Model immediately!
    df_analyzed = predict_anomalies(df)
    
    # Filter anomalies and replace NaNs with None for JSON serialization
    anomalies_df = df_analyzed[df_analyzed["anomaly_label"] == 1].copy()
    anomalies_df = anomalies_df.replace({np.nan: None})
    
    anomalies_list = anomalies_df.head(50).to_dict(orient="records")

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
        "anomalies": anomalies_list,
    }