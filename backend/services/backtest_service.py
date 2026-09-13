"""Backend access to the deterministic historical statistical replay."""

from typing import Any, Dict

from src.backtest.historical_replay import run_historical_replay


def historical_replay() -> Dict[str, Any]:
    return run_historical_replay()
