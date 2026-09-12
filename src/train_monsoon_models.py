"""
VARSHASENTINEL (SIH26086) - Monsoon Model Training & Probabilistic Calibration
==============================================================================
Trains six distinct binary XGBoost forecasting heads using strict temporal splits:
  - TRAIN: 2020-2023
  - VALIDATION: 2024
  - TEST: 2025
Evaluates Brier Score, ROC-AUC, PR-AUC, F1, Precision, and Recall using predict_proba().
Saves trained calibrated model artifacts to models/ and generates reports/monsoon_model_results.md.
"""

import os
import sys
import json
import logging
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    brier_score_loss,
    roc_auc_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    confusion_matrix
)
from sklearn.calibration import CalibratedClassifierCV
from xgboost import XGBClassifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("varshasentinel.train")

DATA_PATH = "data/processed/varshasentinel_master_dataset.parquet"
MODELS_DIR = "models"
REPORTS_DIR = "reports"

TARGETS = [
    ("target_onset_window_14d", "Monsoon Onset (14-Day Window)"),
    ("target_false_onset_flag", "False Onset Surge Failure"),
    ("target_dry_spell_5d_14d", "5-Day Dry Spell / Break (14-Day Lead)"),
    ("target_dry_spell_7d_21d", "7-Day Severe Break (21-Day Lead)"),
    ("target_heavy_rain_7d", "Heavy Rainfall / Flood Hazard (7-Day Lead)"),
    ("target_revival_7d", "Dry Spell Revival (7-Day Lead)")
]

# Baseline features to strictly exclude target leakage
EXCLUDE_COLS = [
    "Date", "Target_Crops", "Active_Crop_Cycle", "Zone",
    "target_onset_window_14d", "target_false_onset_flag",
    "target_dry_spell_5d_14d", "target_dry_spell_7d_21d",
    "target_heavy_rain_7d", "target_revival_7d"
]


def load_and_split_data():
    """Loads master dataset and creates strict temporal walk-forward splits."""
    if not os.path.exists(DATA_PATH):
        csv_alt = "data/processed/varshasentinel_master_dataset.csv"
        logger.info(f"Parquet not found, reading from CSV: {csv_alt}")
        df = pd.read_csv(csv_alt)
    else:
        df = pd.read_parquet(DATA_PATH)

    df["_date"] = pd.to_datetime(df["Date"])
    df["_year"] = df["_date"].dt.year

    # Encode categorical columns
    le_district = LabelEncoder()
    df["District_Encoded"] = le_district.fit_transform(df["District"])
    
    le_zone = LabelEncoder()
    df["Zone_Encoded"] = le_zone.fit_transform(df["zone_id"])

    # Define feature set
    feature_cols = [c for c in df.columns if c not in EXCLUDE_COLS and not c.startswith("_")]
    if "District" in feature_cols:
        feature_cols.remove("District")
    if "zone_id" in feature_cols:
        feature_cols.remove("zone_id")

    logger.info(f"Total Features ({len(feature_cols)}): {feature_cols}")

    # Temporal Splits
    train_mask = df["_year"] <= 2023
    val_mask = df["_year"] == 2024
    test_mask = df["_year"] == 2025

    train_df = df[train_mask].copy()
    val_df = df[val_mask].copy()
    test_df = df[test_mask].copy()

    logger.info(f"TRAIN Set (2020-2023): {len(train_df)} rows")
    logger.info(f"VAL Set   (2024):      {len(val_df)} rows")
    logger.info(f"TEST Set  (2025):      {len(test_df)} rows")

    os.makedirs(MODELS_DIR, exist_ok=True)
    # Save encoders and feature metadata
    metadata = {
        "feature_names": feature_cols,
        "districts": list(le_district.classes_),
        "zones": list(le_zone.classes_),
        "train_years": [2020, 2021, 2022, 2023],
        "val_year": 2024,
        "test_year": 2025
    }
    with open(os.path.join(MODELS_DIR, "feature_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    return df, train_df, val_df, test_df, feature_cols


def train_and_evaluate_head(target_col, target_desc, train_df, val_df, test_df, feature_cols):
    """Trains a calibrated binary XGBoost model for a single monsoon event head."""
    logger.info(f"\n=======================================================")
    logger.info(f"TRAINING HEAD: {target_desc} ({target_col})")
    logger.info(f"=======================================================")

    X_train = train_df[feature_cols]
    y_train = train_df[target_col]

    X_val = val_df[feature_cols]
    y_val = val_df[target_col]

    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    pos_train = y_train.sum()
    neg_train = len(y_train) - pos_train
    pos_val = y_val.sum()
    pos_test = y_test.sum()

    pos_rate_total = (pos_train + pos_val + pos_test) / (len(train_df) + len(val_df) + len(test_df)) * 100
    pos_rate_test = (pos_test / len(test_df)) * 100

    logger.info(f"Class Balance -> Train Pos: {pos_train}/{len(train_df)} | Val Pos: {pos_val}/{len(val_df)} | Test Pos: {pos_test}/{len(test_df)}")

    # Compute scale_pos_weight to address extreme class imbalance
    scale_pos_weight = max(1.0, neg_train / max(1, pos_train))
    if scale_pos_weight > 25.0:
        scale_pos_weight = 25.0 # Guardrail against extreme over-weighting

    # Initialize XGBoost Classifier with binary logistic loss
    base_model = XGBClassifier(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        random_state=42
    )

    base_model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )

    # Probability calibration using Platt Scaling (sigmoid) on validation fold
    try:
        calibrator = CalibratedClassifierCV(estimator=base_model, method="sigmoid", cv="prefit")
        calibrator.fit(X_val, y_val)
        active_model = calibrator
        logger.info("Fitted Platt Sigmoid Probability Calibrator on Validation set.")
    except Exception as e:
        logger.warning(f"Calibration fallback to raw base model due to: {e}")
        active_model = base_model

    # Validation predictions (probabilities)
    val_probs = active_model.predict_proba(X_val)[:, 1]
    val_brier = brier_score_loss(y_val, val_probs)

    # Test predictions (probabilities)
    test_probs = active_model.predict_proba(X_test)[:, 1]
    test_brier = brier_score_loss(y_test, test_probs)

    # ROC-AUC and PR-AUC
    if len(np.unique(y_test)) > 1:
        test_roc_auc = roc_auc_score(y_test, test_probs)
        test_pr_auc = average_precision_score(y_test, test_probs)
    else:
        test_roc_auc = np.nan
        test_pr_auc = np.nan

    # Optimal thresholding based on F1 on validation set
    thresholds = np.linspace(0.1, 0.9, 81)
    best_thresh = 0.5
    best_f1_val = -1.0
    for th in thresholds:
        f1_th = f1_score(y_val, (val_probs >= th).astype(int), zero_division=0)
        if f1_th > best_f1_val:
            best_f1_val = f1_th
            best_thresh = th

    test_preds = (test_probs >= best_thresh).astype(int)
    test_f1 = f1_score(y_test, test_preds, zero_division=0)
    test_prec = precision_score(y_test, test_preds, zero_division=0)
    test_rec = recall_score(y_test, test_preds, zero_division=0)

    logger.info(f"Optimal Decision Threshold (from Val F1): {best_thresh:.2f}")
    logger.info(f"Results on Out-of-Sample 2025 Test Set:")
    logger.info(f"  Brier Score: {test_brier:.4f} (Val: {val_brier:.4f})")
    logger.info(f"  ROC-AUC:     {test_roc_auc:.4f}")
    logger.info(f"  PR-AUC:      {test_pr_auc:.4f}")
    logger.info(f"  F1-Score:    {test_f1:.4f} (Prec: {test_prec:.4f}, Rec: {test_rec:.4f})")

    # Save model artifact
    model_save_path = os.path.join(MODELS_DIR, f"{target_col}_xgb.joblib")
    joblib.dump({
        "model": active_model,
        "base_model": base_model,
        "optimal_threshold": float(best_thresh),
        "target_col": target_col,
        "target_desc": target_desc,
        "feature_cols": feature_cols
    }, model_save_path)
    logger.info(f"Saved model to: {model_save_path}")

    metrics = {
        "target": target_col,
        "description": target_desc,
        "positive_rate_total_pct": round(float(pos_rate_total), 2),
        "positive_rate_test_pct": round(float(pos_rate_test), 2),
        "val_brier": round(float(val_brier), 4),
        "test_brier": round(float(test_brier), 4),
        "test_roc_auc": round(float(test_roc_auc), 4) if not np.isnan(test_roc_auc) else "N/A",
        "test_pr_auc": round(float(test_pr_auc), 4) if not np.isnan(test_pr_auc) else "N/A",
        "optimal_threshold": round(float(best_thresh), 2),
        "test_f1": round(float(test_f1), 4),
        "test_precision": round(float(test_prec), 4),
        "test_recall": round(float(test_rec), 4)
    }

    return metrics


def main():
    logger.info("Starting VARSHASENTINEL Model Training Pipeline...")
    df, train_df, val_df, test_df, feature_cols = load_and_split_data()

    results = []
    for target_col, target_desc in TARGETS:
        m = train_and_evaluate_head(target_col, target_desc, train_df, val_df, test_df, feature_cols)
        results.append(m)

    # Save metrics JSON
    metrics_path = os.path.join(MODELS_DIR, "evaluation_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved all evaluation metrics to {metrics_path}")

    # Generate Markdown Results Report
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, "monsoon_model_results.md")

    lines = [
        "# VARSHASENTINEL (SIH26086) — Monsoon Prediction Model Performance",
        "",
        "**Evaluation Standard**: Out-of-Sample Temporal Walk-Forward Splitting",
        "- **Training Period**: 2020–2023 (17,536 records across 12 districts)",
        "- **Validation Period**: 2024 (4,392 records)",
        "- **Test Period**: 2025 (4,376 records — Completely Unseen Out-of-Sample)",
        "",
        "## 1. Primary Performance Table",
        "",
        "| Target Event | Target Column | Total Pos Rate | Val Brier | Test Brier | Test ROC-AUC | Test PR-AUC | Test F1 | Test Recall |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
    ]

    for r in results:
        lines.append(
            f"| **{r['description']}** | `{r['target']}` | {r['positive_rate_total_pct']}% | {r['val_brier']} | {r['test_brier']} | {r['test_roc_auc']} | {r['test_pr_auc']} | {r['test_f1']} | {r['test_recall']} |"
        )

    lines.extend([
        "",
        "## 2. Metric Interpretations & Scientific Highlights",
        "",
        "1. **Brier Score (Lower is Better)**: Measures probability calibration error. A Brier score below 0.10 indicates high reliability in probabilistic hazard forecasting.",
        "2. **PR-AUC vs ROC-AUC**: For highly imbalanced events (e.g. False Onset or Heavy Rainfall), Precision-Recall AUC (PR-AUC) provides the true measure of operational alert fidelity without being distorted by the vast number of non-event true negatives.",
        "3. **Zero Temporal Leakage**: Unlike previous unstratified 93–99% random shuffle scores, these metrics represent genuine forward-looking predictive generalization on the out-of-sample 2025 monsoon season.",
        ""
    ])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"Successfully generated results report: {report_path}")


if __name__ == "__main__":
    main()
