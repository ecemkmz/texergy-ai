from fastapi import APIRouter
from app.database import engine

router = APIRouter()

@router.get("/health")
def health():
    try:
        with engine.connect():
            pass
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "ok", "database": "unreachable", "error": str(e)}