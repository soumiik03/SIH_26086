from fastapi import APIRouter

from backend.schemas.backtest import BacktestResponse
from backend.services import backtest_service

router = APIRouter(prefix="/api")


@router.get("/backtest", response_model=BacktestResponse)
def get_backtest():
    try:
        return backtest_service.historical_replay()
    except (FileNotFoundError, ValueError, KeyError) as exc:
        return {
            "status": "UNAVAILABLE",
            "limitation": f"Historical statistical replay is unavailable: {exc}",
        }
