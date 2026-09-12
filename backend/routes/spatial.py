from fastapi import APIRouter, HTTPException, Path

from backend.schemas.spatial import (
    BlockResponse, DistrictResponse, PanchayatListItem, PanchayatResponse, RiskMapResponse,
)
from backend.services import forecast_service as service

router = APIRouter(prefix="/api")


@router.get("/districts", response_model=list[DistrictResponse])
def get_districts():
    return service.supported_districts()


@router.get("/blocks", response_model=list[BlockResponse])
def get_blocks():
    return service.supported_blocks()


@router.get("/blocks/{block_id}/panchayats", response_model=list[PanchayatListItem])
def get_block_panchayats(block_id: str = Path(pattern=r"^blk_[0-9]+$")):
    if not any(block["block_id"] == block_id for block in service.supported_blocks()):
        raise HTTPException(status_code=404, detail="Block is not supported in the forecast layer")
    return [service.to_panchayat_list_item(feature) for feature in service.panchayats_for_block(block_id)]


@router.get("/panchayats/{panchayat_id}", response_model=PanchayatResponse)
def get_panchayat(panchayat_id: str = Path(pattern=r"^gp_[0-9]+$")):
    feature = service.find_panchayat(panchayat_id)
    if feature is None:
        raise HTTPException(status_code=404, detail="Panchayat is not supported in the verified safe layer")
    return service.to_panchayat_response(feature)


@router.get("/risk-map", response_model=RiskMapResponse)
def get_risk_map():
    return service.risk_map()

