from pathlib import Path

import pytest

xgboost = pytest.importorskip("xgboost")
pytest.importorskip("sklearn")

from rnamining.inference import predict_file


ROOT = Path(__file__).resolve().parents[1]


def test_reorganized_inference_matches_versioned_example(tmp_path):
    if xgboost.__version__ != "2.0.3":
        pytest.skip("Frozen legacy pickle regression requires XGBoost 2.0.3")
    output = tmp_path / "output"
    try:
        predict_file(ROOT / "tests/fixtures/anolis_regression.fa", "Anolis_carolinensis", output, model_dir=ROOT / "models/coding_prediction")
    except (ImportError, ModuleNotFoundError, AttributeError) as exc:
        pytest.skip(f"Legacy pickle dependencies are unavailable: {exc}")
    observed = (output / "predictions.txt").read_text().splitlines()[5].split("\t")
    assert observed[1] == "non-coding"
    assert float(observed[2]) == pytest.approx(0.99994904, abs=1e-8)
