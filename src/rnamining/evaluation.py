"""Reusable binary-classification metrics for RNAmining experiments."""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)

METRICS = ("accuracy", "precision", "recall", "f1", "mcc", "auroc", "auprc")


def calculate_metrics(y_true, y_pred, y_score=None) -> dict:
    truth = np.asarray(y_true, dtype=int)
    predicted = np.asarray(y_pred, dtype=int)
    if truth.ndim != 1 or predicted.ndim != 1 or not len(truth):
        raise ValueError("y_true and y_pred must be non-empty one-dimensional sequences.")
    if (
        len(truth) != len(predicted)
        or not set(np.unique(truth)).issubset({0, 1})
        or not set(np.unique(predicted)).issubset({0, 1})
    ):
        raise ValueError("y_true and y_pred must have equal binary labels.")

    tn, fp, fn, tp = (
        int(value) for value in confusion_matrix(truth, predicted, labels=[0, 1]).ravel()
    )
    result = {
        "accuracy": float(accuracy_score(truth, predicted)),
        "precision": float(precision_score(truth, predicted, zero_division=0)),
        "recall": float(recall_score(truth, predicted, zero_division=0)),
        "f1": float(f1_score(truth, predicted, zero_division=0)),
        "mcc": float(matthews_corrcoef(truth, predicted)) if len(set(truth)) > 1 else 0.0,
        "auroc": None,
        "auprc": None,
        "tn": tn, "fp": fp, "fn": fn, "tp": tp,
        "auroc_reason": "", "auprc_reason": "",
    }
    if y_score is None:
        result["auroc_reason"] = result["auprc_reason"] = "ranking scores were not provided"
    elif len(set(truth)) < 2:
        result["auroc_reason"] = result["auprc_reason"] = "ground truth contains only one class"
    else:
        scores = np.asarray(y_score, dtype=float)
        if scores.ndim != 1 or len(scores) != len(truth) or not np.all(np.isfinite(scores)):
            raise ValueError("y_score must be a finite one-dimensional score vector.")
        result["auroc"] = float(roc_auc_score(truth, scores))
        result["auprc"] = float(average_precision_score(truth, scores))
    return result


def evaluate_model(model, X_test, y_true) -> dict:
    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)
    classes = np.asarray(getattr(model, "classes_", []))
    positive_index = int(np.flatnonzero(classes == 1)[0]) if classes.size else 1
    result = calculate_metrics(y_true, predictions, probabilities[:, positive_index])
    result["score_type"] = "probability"
    return result


def summarize_metrics(results) -> dict:
    rows = list(results)
    summary = {}
    for metric in METRICS:
        values = [row[metric] for row in rows if row.get(metric) is not None]
        summary[f"{metric}_mean"] = statistics.mean(values) if values else None
        summary[f"{metric}_std"] = statistics.stdev(values) if len(values) > 1 else 0.0 if values else None
        summary[f"{metric}_n"] = len(values)
    return summary


def export_results(rows, path) -> Path:
    records = list(rows)
    if not records:
        raise ValueError("At least one result row is required for export.")
    fieldnames = list(dict.fromkeys(field for record in records for field in record))
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    return output
