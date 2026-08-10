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


def _binary_vector(values, name: str) -> np.ndarray:
    array = np.asarray(values)

    if array.ndim != 1 or not len(array):
        raise ValueError(f"{name} must be a non-empty one-dimensional sequence.")
    try:
        unique = set(np.unique(array))
    except TypeError as error:
        raise ValueError(f"{name} must contain binary labels 0 and 1.") from error
    
    if not unique.issubset({0, 1}):
        raise ValueError(f"{name} must contain only binary labels 0 and 1.")
    
    return array.astype(int)


def calculate_metrics(y_true, y_pred, y_score=None) -> dict:
    """Calculate standard binary metrics from labels and optional ranking scores."""
    truth = _binary_vector(y_true, "y_true")
    predicted = _binary_vector(y_pred, "y_pred")

    if len(truth) != len(predicted):
        raise ValueError("y_true and y_pred must have the same length.")

    scores = None
    if y_score is not None:
        scores = np.asarray(y_score, dtype=float)

        if scores.ndim != 1 or len(scores) != len(truth):
            raise ValueError("y_score must be one-dimensional and match y_true.")
        
        if not np.all(np.isfinite(scores)):
            raise ValueError("y_score must contain only finite values.")

    tn, fp, fn, tp = (
        int(value)
        for value in confusion_matrix(truth, predicted, labels=[0, 1]).ravel()
    )

    result = {
        "accuracy": float(accuracy_score(truth, predicted)),
        "precision": float(precision_score(truth, predicted, zero_division=0)),
        "recall": float(recall_score(truth, predicted, zero_division=0)),
        "f1": float(f1_score(truth, predicted, zero_division=0)),
        "mcc": (
            float(matthews_corrcoef(truth, predicted))
            if len(np.unique(np.concatenate((truth, predicted)))) > 1
            else 0.0
        ),
        "auroc": None,
        "auprc": None,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
        "auroc_reason": "",
        "auprc_reason": "",
    }

    if scores is None:
        reason = "ranking scores were not provided"
        result["auroc_reason"] = reason
        result["auprc_reason"] = reason

    elif len(np.unique(truth)) < 2:
        reason = "ground truth contains only one class"
        result["auroc_reason"] = reason
        result["auprc_reason"] = reason

    else:
        result["auroc"] = float(roc_auc_score(truth, scores))
        result["auprc"] = float(average_precision_score(truth, scores))

    return result


def _model_scores(model, matrix):
    classes = np.asarray(getattr(model, "classes_", []))
    predict_proba = getattr(model, "predict_proba", None)

    if callable(predict_proba):
        probabilities = np.asarray(predict_proba(matrix), dtype=float)

        if probabilities.ndim != 2:
            raise ValueError("predict_proba must return a two-dimensional array.")
        
        if classes.size:
            matches = np.flatnonzero(classes == 1)

            if len(matches) != 1:
                raise ValueError("Model classes_ does not identify positive class 1.")
            
            positive_index = int(matches[0])

        elif probabilities.shape[1] == 2:
            positive_index = 1

        else:
            raise ValueError("Cannot identify the positive-class probability.")
        return probabilities[:, positive_index], "probability"

    decision_function = getattr(model, "decision_function", None)
    if callable(decision_function):
        decisions = np.asarray(decision_function(matrix), dtype=float)

        if decisions.ndim == 2 and decisions.shape[1] == 1:
            decisions = decisions[:, 0]

        if decisions.ndim != 1:
            raise ValueError("decision_function must return one score per sample.")
        
        if classes.size == 2 and classes[1] != 1:
            if classes[0] != 1:
                raise ValueError("Model classes_ does not identify positive class 1.")
            
            decisions = -decisions

        return decisions, "decision"

    return None, "unavailable"


def evaluate_model(model, X_test, y_true) -> dict:
    """Run a fitted binary model and calculate metrics without experiment metadata."""
    predictions = model.predict(X_test)
    scores, score_type = _model_scores(model, X_test)

    result = calculate_metrics(y_true, predictions, scores)
    result["score_type"] = score_type

    return result


def summarize_metrics(results) -> dict:
    """Return the mean, sample standard deviation, and count for each metric."""
    rows = list(results)
    summary = {}

    for metric in METRICS:
        values = [row[metric] for row in rows if row.get(metric) is not None]

        summary[f"{metric}_mean"] = statistics.mean(values) if values else None
        summary[f"{metric}_std"] = (
            statistics.stdev(values)
            if len(values) > 1
            else 0.0 if values else None
        )

        summary[f"{metric}_n"] = len(values)

    return summary


def export_results(rows, path) -> Path:
    """Export result dictionaries, including any caller-provided metadata, to CSV."""
    records = list(rows)

    if not records:
        raise ValueError("At least one result row is required for export.")

    fieldnames = []
    for record in records:
        for field in record:
            if field not in fieldnames:
                fieldnames.append(field)

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
        
    return output
