"""Deterministic, source-backed agronomic decision layer."""

from .expert_system import AdvisoryInput, evaluate_advisory, get_crop_profile, supported_crops

__all__ = ["AdvisoryInput", "evaluate_advisory", "get_crop_profile", "supported_crops"]
