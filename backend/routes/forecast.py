from fastapi import APIRouter, HTTPException, Path, Query

from backend.schemas.forecast import (
    AgronomicAdvisoryResponse,
    ForecastResponse,
    HealthResponse,
)
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


@router.get("/advisory/{panchayat_id}", response_model=AgronomicAdvisoryResponse)
def get_advisory(
    panchayat_id: str = Path(pattern=r"^gp_[0-9]+$"),
    crop: str = Query(..., min_length=1),
    crop_stage: str | None = Query(default=None),
    planned_sowing_date: str | None = Query(default=None),
):
    try:
        response = service.advisory_for_panchayat(
            panchayat_id,
            crop=crop,
            crop_stage=crop_stage,
            planned_sowing_date=planned_sowing_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if response is None:
        raise HTTPException(status_code=404, detail="Panchayat is not supported in the verified forecast layer")
    return response
