"""Serializable probability calibration used by the Step 11 V2 artifacts."""

from __future__ import annotations

from typing import Sequence

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


class ProbabilityCalibrator:
    """Platt/sigmoid or isotonic calibration with bounded probabilities."""

    def __init__(self, method: str):
        self.method = method
        self.model = None

    def fit(self, probabilities: Sequence[float], y: Sequence[int]):
        p = np.clip(np.asarray(probabilities, float), 1e-6, 1 - 1e-6)
        if self.method == "sigmoid":
            self.model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
            self.model.fit(np.log(p / (1 - p)).reshape(-1, 1), np.asarray(y, int))
        elif self.method == "isotonic":
            self.model = IsotonicRegression(out_of_bounds="clip")
            self.model.fit(p, np.asarray(y, int))
        else:
            raise ValueError(self.method)
        return self

    def predict(self, probabilities: Sequence[float]) -> np.ndarray:
        p = np.clip(np.asarray(probabilities, float), 1e-6, 1 - 1e-6)
        if self.method == "sigmoid":
            return self.model.predict_proba(np.log(p / (1 - p)).reshape(-1, 1))[:, 1]
        return np.asarray(self.model.predict(p), float)
