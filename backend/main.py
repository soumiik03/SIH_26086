from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.backtest import router as backtest_router
from backend.routes.forecast import router as forecast_router
from backend.routes.spatial import router as spatial_router


app = FastAPI(
    title="VARSHASENTINEL API",
    version="1.0.0",
    description=(
        "Verified spatial access to VARSHASENTINEL forecast artifacts. "
        "Forecasts remain in EXPERIMENTAL_OBSERVATION_STATE."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(forecast_router)
app.include_router(spatial_router)
app.include_router(backtest_router)

