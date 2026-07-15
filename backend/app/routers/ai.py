from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ai_service import get_action_suggestion

router = APIRouter()

class AnomalyInfo(BaseModel):
    facility_type: str = "Bilinmiyor"
    machine_speed: float = 0.0
    defect_rate: float = 0.0
    quality_score: float = 0.0
    energy_waste_flag: int = 0

@router.post("/analyze_anomaly")
async def analyze_anomaly(info: AnomalyInfo):
    # On-demand AI trigger
    suggestion = get_action_suggestion(info.dict())
    return {"suggestion": suggestion}
