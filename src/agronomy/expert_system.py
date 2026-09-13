"""Source-backed deterministic agronomic advisories.

This module consumes forecast results; it never trains models, changes labels,
or creates probabilities. Crop rules are deliberately small and explicit until
additional authoritative West Bengal crop guidance is encoded and reviewed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Mapping, Optional


ACTION_SOW = "SOW"
ACTION_WAIT = "WAIT"
ACTION_PREPARE_IRRIGATION = "PREPARE_IRRIGATION"

# Thresholds reuse the existing production risk framework where applicable:
# onset favorable is the existing advisory's 0.60 threshold; 0.40 and 0.50
# are the existing HIGH boundaries for false-onset and event risk levels.
RULE_THRESHOLDS: Mapping[str, float] = {
    "onset_favorable_min": 0.60,
    "false_onset_high_min": 0.40,
    "dry_spell_elevated_min": 0.50,
    "severe_break_elevated_min": 0.50,
    "heavy_rain_elevated_min": 0.50,
    "dry_spell_extreme_min": 0.70,
}


@dataclass(frozen=True)
class CropProfile:
    key: str
    display_name: str
    earliest_sowing: tuple[int, int]
    preferred_sowing_start: tuple[int, int]
    preferred_sowing_end: tuple[int, int]
    latest_sowing: tuple[int, int]
    geography: str
    source_url: str
    source_note: str


@dataclass(frozen=True)
class AdvisoryInput:
    """Explicit boundary between forecast output and agronomic rules."""

    reference_date: Any
    probabilities: Mapping[str, Any]
    statistical_7_30_day_outlook: Mapping[str, Any]
    crop: Optional[str] = None
    crop_stage: Optional[str] = None
    planned_sowing_date: Optional[str] = None
    location: Optional[Mapping[str, Any]] = None
    observations: Optional[Mapping[str, Any]] = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AdvisoryInput":
        required = ("reference_date", "probabilities", "statistical_7_30_day_outlook")
        missing = [key for key in required if key not in value]
        if missing:
            raise ValueError(f"Missing advisory input fields: {missing}")
        return cls(
            reference_date=value["reference_date"],
            probabilities=value["probabilities"],
            statistical_7_30_day_outlook=value["statistical_7_30_day_outlook"],
            crop=value.get("crop"),
            crop_stage=value.get("crop_stage"),
            planned_sowing_date=value.get("planned_sowing_date"),
            location=value.get("location"),
            observations=value.get("observations"),
        )


SUPPORTED_CROPS: Mapping[str, CropProfile] = {
    "aman_rice": CropProfile(
        key="aman_rice",
        display_name="Aman rice",
        earliest_sowing=(5, 20),
        preferred_sowing_start=(6, 10),
        preferred_sowing_end=(6, 25),
        latest_sowing=(8, 7),
        geography="West Bengal; timing should be confirmed against local extension guidance and land situation",
        source_url="https://icar.gov.in/sites/default/files/Circulars/ICAR-En-Kharif-Agro-Advisories-for-Farmers-2025.pdf",
        source_note=(
            "ICAR West Bengal kharif advisory specifies seedbed preparation from May 20 to June 5 "
            "and transplanting from June 10 to June 25; ICAR-CRIDA contingency guidance documents "
            "delayed transplanting scenarios through the first week of August for North 24 Parganas."
        ),
    ),
}


def supported_crops() -> List[Dict[str, str]]:
    return [
        {
            "key": profile.key,
            "name": profile.display_name,
            "geography": profile.geography,
            "source_url": profile.source_url,
        }
        for profile in SUPPORTED_CROPS.values()
    ]


def get_crop_profile(crop: str) -> CropProfile:
    key = crop.strip().lower()
    if key not in SUPPORTED_CROPS:
        raise ValueError(f"Unsupported crop '{crop}'. Supported crops: {sorted(SUPPORTED_CROPS)}")
    return SUPPORTED_CROPS[key]


def _as_probability(value: Any) -> Optional[float]:
    if value is None:
        return None
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"Probability out of bounds: {value}")
    return value


def _date_from(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()


def _date_in_range(value: date, start: tuple[int, int], end: tuple[int, int]) -> bool:
    marker = (value.month, value.day)
    return start <= marker <= end


def _profile_window_state(reference_date: date, profile: CropProfile) -> str:
    if _date_in_range(reference_date, profile.earliest_sowing, profile.latest_sowing):
        return "WITHIN_WINDOW"
    return "OUTSIDE_WINDOW"


def _outlook_event(outlook: Mapping[str, Any], horizon: str, event: str) -> Optional[float]:
    values = outlook.get(horizon) or {}
    applicability = values.get(f"{event}_applicability")
    probability = _as_probability(values.get(f"{event}_probability"))
    if applicability == "OUT_OF_SEASON":
        return None
    return probability


def _result(
    *,
    action: str,
    rule_id: str,
    profile: Optional[CropProfile],
    reasons: List[str],
    reason_keys: List[str],
    risk_factors: Dict[str, Optional[float]],
    validity: str,
    headline: str,
    recommended_action: str,
) -> Dict[str, Any]:
    return {
        "action": action,
        "rule_id": rule_id,
        "crop": profile.key if profile else None,
        "crop_name": profile.display_name if profile else None,
        "headline": headline,
        "recommended_action": recommended_action,
        "headline_key": f"advisory.{action.lower()}",
        "reason_keys": reason_keys,
        "reasons": reasons,
        "risk_factors": risk_factors,
        "validity": validity,
        "thresholds": dict(RULE_THRESHOLDS),
    }


def evaluate_advisory(context: Mapping[str, Any] | AdvisoryInput) -> Dict[str, Any]:
    """Evaluate a crop advisory deterministically from supplied forecast data."""
    inputs = context if isinstance(context, AdvisoryInput) else AdvisoryInput.from_mapping(context)
    crop = inputs.crop
    profile = get_crop_profile(str(crop)) if crop else None
    reference_date = _date_from(inputs.reference_date)
    probabilities = inputs.probabilities or {}
    p_onset = _as_probability(probabilities.get("onset_probability"))
    p_false = _as_probability(probabilities.get("false_onset_probability"))
    p_dry = _as_probability(probabilities.get("dry_spell_5d_probability"))
    p_severe = _as_probability(probabilities.get("severe_break_7d_probability"))
    p_heavy = _as_probability(probabilities.get("heavy_rain_probability"))
    p_revival = _as_probability(probabilities.get("revival_probability"))
    risk_factors = {
        "onset_probability": p_onset,
        "false_onset_probability": p_false,
        "dry_spell_5d_probability": p_dry,
        "severe_break_7d_probability": p_severe,
        "heavy_rain_probability": p_heavy,
        "revival_probability": p_revival,
    }

    if profile is None:
        return _result(
            action=ACTION_WAIT,
            rule_id="AGRI-WAIT-CROP-CONTEXT-001",
            profile=None,
            reasons=["Select a supported crop before requesting a crop-specific sowing decision."],
            reason_keys=["reason.crop_context_required"],
            risk_factors=risk_factors,
            validity="CROP_CONTEXT_REQUIRED",
            headline="Crop context required",
            recommended_action="WAIT for a crop-specific decision until the crop and sowing context are supplied.",
        )

    window_state = _profile_window_state(reference_date, profile)
    if window_state == "OUTSIDE_WINDOW":
        return _result(
            action=ACTION_WAIT,
            rule_id="AGRI-WAIT-WINDOW-001",
            profile=profile,
            reasons=["The reference date is outside the sourced Aman rice sowing window."],
            reason_keys=["reason.outside_sowing_window"],
            risk_factors=risk_factors,
            validity="VALID_FOR_CROP_WINDOW_ONLY",
            headline="Wait: outside the sourced sowing window",
            recommended_action="Do not use this result to start sowing outside the documented crop window; confirm the local crop calendar with extension staff.",
        )

    outlook = inputs.statistical_7_30_day_outlook or {}
    horizon_dry = _outlook_event(outlook, "7_14d", "dry_spell")
    horizon_severe = _outlook_event(outlook, "7_14d", "severe_break")
    if horizon_dry is None or horizon_severe is None:
        return _result(
            action=ACTION_WAIT,
            rule_id="AGRI-WAIT-APPLICABILITY-001",
            profile=profile,
            reasons=["A required 7–14 day monsoon risk input is not applicable or unavailable for this date."],
            reason_keys=["reason.forecast_not_applicable"],
            risk_factors=risk_factors,
            validity="INSUFFICIENT_APPLICABLE_FORECAST",
            headline="Wait: forecast applicability is insufficient",
            recommended_action="Wait for an applicable forecast state and confirm conditions locally before sowing.",
        )

    if p_heavy is None or p_onset is None or p_false is None or p_dry is None:
        return _result(
            action=ACTION_WAIT,
            rule_id="AGRI-WAIT-APPLICABILITY-002",
            profile=profile,
            reasons=["One or more required current event probabilities are unavailable."],
            reason_keys=["reason.current_forecast_missing"],
            risk_factors=risk_factors,
            validity="INSUFFICIENT_CURRENT_FORECAST",
            headline="Wait: current forecast is incomplete",
            recommended_action="Do not infer a sowing decision from missing probabilities; reassess when the forecast is complete.",
        )

    if p_heavy >= RULE_THRESHOLDS["heavy_rain_elevated_min"]:
        return _result(
            action=ACTION_WAIT,
            rule_id="AGRI-DRAINAGE-001",
            profile=profile,
            reasons=["Heavy-rain risk is elevated; water excess and drainage risk take priority over sowing."],
            reason_keys=["reason.heavy_rain_elevated", "reason.drainage_priority"],
            risk_factors=risk_factors,
            validity="VALID_FOR_CROP_WINDOW_ONLY",
            headline="Wait and prepare drainage",
            recommended_action="Do not sow solely on the onset signal; inspect drainage and protect nursery or low-lying fields from waterlogging.",
        )

    if p_false >= RULE_THRESHOLDS["false_onset_high_min"]:
        return _result(
            action=ACTION_WAIT,
            rule_id="AGRI-WAIT-FALSE-ONSET-001",
            profile=profile,
            reasons=["False-onset risk is at or above the existing high-risk boundary."],
            reason_keys=["reason.false_onset_elevated"],
            risk_factors=risk_factors,
            validity="VALID_FOR_CROP_WINDOW_ONLY",
            headline="Wait: false-onset risk is elevated",
            recommended_action="Wait before sowing and reassess when the onset signal becomes more reliable.",
        )

    if p_onset < RULE_THRESHOLDS["onset_favorable_min"]:
        return _result(
            action=ACTION_WAIT,
            rule_id="AGRI-WAIT-ONSET-001",
            profile=profile,
            reasons=["Onset probability is below the existing favorable-onset threshold."],
            reason_keys=["reason.onset_insufficient"],
            risk_factors=risk_factors,
            validity="VALID_FOR_CROP_WINDOW_ONLY",
            headline="Wait: onset is not sufficiently reliable",
            recommended_action="Wait before sowing and reassess as the onset signal strengthens.",
        )

    if p_dry >= RULE_THRESHOLDS["dry_spell_extreme_min"] or horizon_severe >= RULE_THRESHOLDS["dry_spell_extreme_min"]:
        return _result(
            action=ACTION_WAIT,
            rule_id="AGRI-WAIT-DRY-SPELL-001",
            profile=profile,
            reasons=["Dry-spell or severe-break risk is at the existing severe-risk boundary; irrigation preparedness alone is not sufficient to justify sowing."],
            reason_keys=["reason.dry_spell_extreme", "reason.sowing_deferred"],
            risk_factors={**risk_factors, "outlook_7_14d_dry_spell_probability": horizon_dry, "outlook_7_14d_severe_break_probability": horizon_severe},
            validity="VALID_FOR_CROP_WINDOW_ONLY",
            headline="Wait: dry-spell risk is severe",
            recommended_action="Wait before sowing and confirm dependable supplemental water with local extension staff.",
        )

    if p_dry >= RULE_THRESHOLDS["dry_spell_elevated_min"] or horizon_dry >= RULE_THRESHOLDS["dry_spell_elevated_min"] or horizon_severe >= RULE_THRESHOLDS["severe_break_elevated_min"]:
        return _result(
            action=ACTION_PREPARE_IRRIGATION,
            rule_id="AGRI-IRRIGATION-001",
            profile=profile,
            reasons=["Onset is favorable, but near-term or 7–14 day dry/break risk is elevated."],
            reason_keys=["reason.dry_spell_elevated", "reason.irrigation_preparedness"],
            risk_factors={**risk_factors, "outlook_7_14d_dry_spell_probability": horizon_dry, "outlook_7_14d_severe_break_probability": horizon_severe},
            validity="VALID_FOR_CROP_WINDOW_ONLY",
            headline="Prepare irrigation before sowing",
            recommended_action="Sowing conditions are favorable, but arrange supplemental irrigation and conserve soil moisture before proceeding.",
        )

    return _result(
        action=ACTION_SOW,
        rule_id="AGRI-SOW-001",
        profile=profile,
        reasons=["The crop is within its sourced window, onset is favorable, false-onset risk is low, and dry/break risk is acceptable."],
        reason_keys=["reason.sowing_window", "reason.onset_favorable", "reason.risk_acceptable"],
        risk_factors={**risk_factors, "outlook_7_14d_dry_spell_probability": horizon_dry, "outlook_7_14d_severe_break_probability": horizon_severe},
        validity="VALID_FOR_CROP_WINDOW_ONLY",
        headline="Sowing conditions are favorable",
        recommended_action="Proceed with Aman rice sowing/transplanting according to the locally appropriate stage and field conditions.",
    )
