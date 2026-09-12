from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api")


@router.get("/backtest")
def get_backtest():
    raise HTTPException(
        status_code=501,
        detail="Historical backtest API is not implemented because no existing callable backtest capability was found.",
    )

