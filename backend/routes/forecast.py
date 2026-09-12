from fastapi import APIRouter, HTTPException, Path

from backend.schemas.forecast import ForecastResponse, HealthResponse
from backend.services import forecast_service as service

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
def get_health():
    return service.health()


@router.get("/forecast/{panchayat_id}", response_model=ForecastResponse)
def get_forecast(panchayat_id: str = Path(pattern=r"^gp_[0-9]+$")):
    feature = service.find_panchayat(panchayat_id)
    if feature is None:
        raise HTTPException(status_code=404, detail="Panchayat is not supported in the verified forecast layer")
    return service.to_forecast_response(feature)

