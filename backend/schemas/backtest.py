from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class BacktestResponse(BaseModel):
    status: Literal["AVAILABLE", "UNAVAILABLE"]
    evaluation_period: Optional[str] = None
    records_evaluated: int = Field(default=0, ge=0)
    cases: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    methodology: Dict[str, Any] = Field(default_factory=dict)
    limitation: Optional[str] = None
