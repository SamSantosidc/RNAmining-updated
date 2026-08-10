import csv
import math

import numpy as np
import pytest

from rnamining.evaluation import (
    calculate_metrics,
    evaluate_model,
    export_results,
    summarize_metrics,
)


class ProbabilityModel:
    classes_ = np.asarray([0, 1])

    def predict(self, matrix):
        return np.asarray([0, 1, 1, 1])

    def predict_proba(self, matrix):
        return np.asarray([
            [0.9, 0.1],
            [0.2, 0.8],
            [0.1, 0.9],
            [0.3, 0.7],
        ])


class DecisionModel:
    classes_ = np.asarray([1, 0])

    def predict(self, matrix):
        return np.asarray([1, 0])

    def decision_function(self, matrix):
        return np.asarray([-0.8, 0.8])


class LabelOnlyModel:
    def predict(self, matrix):
        return np.asarray([1, 0])


def test_calculate_metrics_returns_standard_values_and_confusion_counts():
    result = calculate_metrics(
        [0, 0, 1, 1],
        [0, 1, 1, 1],
        [0.1, 0.8, 0.9, 0.7],
    )

    assert result["accuracy"] == 0.75
    assert result["precision"] == pytest.approx(2 / 3)
    assert result["recall"] == 1.0
    assert result["f1"] == 0.8
    assert result["mcc"] == pytest.approx(1 / math.sqrt(3))
    assert result["auroc"] == 0.75
    assert result["auprc"] == pytest.approx(5 / 6)
    assert {name: result[name] for name in ("tn", "fp", "fn", "tp")} == {
        "tn": 1,
        "fp": 1,
        "fn": 0,
        "tp": 2,
    }


def test_evaluate_model_uses_positive_class_probability():
    result = evaluate_model(
        ProbabilityModel(),
        np.zeros((4, 1)),
        [0, 0, 1, 1],
    )
    assert result["score_type"] == "probability"
    assert result["auroc"] == 0.75


def test_evaluate_model_falls_back_to_oriented_decision_scores():
    result = evaluate_model(
        DecisionModel(),
        np.zeros((2, 1)),
        [1, 0],
    )
    assert result["score_type"] == "decision"
    assert result["auroc"] == 1.0
    assert result["auprc"] == 1.0


def test_basic_metrics_work_when_model_has_no_scores():
    result = evaluate_model(
        LabelOnlyModel(),
        np.zeros((2, 1)),
        [1, 0],
    )
    assert result["accuracy"] == 1.0
    assert result["mcc"] == 1.0
    assert result["auroc"] is None
    assert result["auprc"] is None
    assert result["score_type"] == "unavailable"
    assert "not provided" in result["auroc_reason"]


def test_single_class_and_zero_predicted_positives_do_not_fail():
    single_class = calculate_metrics([1, 1], [1, 1], [0.8, 0.9])
    assert single_class["accuracy"] == 1.0
    assert single_class["auroc"] is None
    assert "one class" in single_class["auroc_reason"]

    no_positives = calculate_metrics([0, 1], [0, 0])
    assert no_positives["precision"] == 0.0
    assert no_positives["recall"] == 0.0
    assert no_positives["f1"] == 0.0


def test_invalid_labels_and_incompatible_lengths_are_rejected():
    with pytest.raises(ValueError, match="only binary"):
        calculate_metrics([0, 2], [0, 1])
    with pytest.raises(ValueError, match="same length"):
        calculate_metrics([0, 1], [0])
    with pytest.raises(ValueError, match="match y_true"):
        calculate_metrics([0, 1], [0, 1], [0.1])


def test_summarize_metrics_calculates_mean_sample_std_and_available_count():
    first = calculate_metrics([0, 1], [0, 1], [0.1, 0.9])
    second = calculate_metrics([0, 1], [1, 0])
    summary = summarize_metrics([first, second])

    assert summary["accuracy_mean"] == 0.5
    assert summary["accuracy_std"] == pytest.approx(math.sqrt(0.5))
    assert summary["accuracy_n"] == 2
    assert summary["auroc_mean"] == 1.0
    assert summary["auroc_std"] == 0.0
    assert summary["auroc_n"] == 1


def test_export_results_keeps_caller_metadata_and_metric_columns(tmp_path):
    metrics = calculate_metrics([0, 1], [0, 1])
    row = {
        "experiment": "current_models",
        "model_scope": "species_specific",
        "test_species": "Alpha_beta",
        **metrics,
    }
    path = export_results([row], tmp_path / "nested" / "metrics.csv")

    with path.open(newline="", encoding="utf-8") as handle:
        exported = list(csv.DictReader(handle))
    assert exported[0]["model_scope"] == "species_specific"
    assert exported[0]["test_species"] == "Alpha_beta"
    assert exported[0]["accuracy"] == "1.0"
