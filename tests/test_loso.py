import pickle
import sys
import types

import numpy as np
import pytest

from rnamining.loso import run_loso, train_loso_fold
from rnamining.loso_evaluation import evaluate_loso


class DummyClassifier:
    def __init__(self, random_state=None, n_jobs=None):
        self.random_state = random_state
        self.n_jobs = n_jobs

    def fit(self, matrix, labels):
        self.n_fit = len(matrix)
        self.classes_ = np.asarray([0, 1])
        return self

    def predict(self, matrix):
        return np.asarray([0 if row[0] < 0 else 1 for row in matrix])

    def predict_proba(self, matrix):
        return np.asarray([[0.8, 0.2] if value == 0 else [0.2, 0.8]
                           for value in self.predict(matrix)])


def _write_raw_dataset(root, species):
    raw = root / "raw"
    raw.mkdir()
    for name in species:
        (raw / f"{name}.cds.fa").write_text(
            f">{name}_coding_0\nAAA\n>{name}_coding_1\nAAT\n"
        )
        (raw / f"{name}.ncrna.fa").write_text(
            f">{name}_noncoding_0\nCCC\n>{name}_noncoding_1\nCCT\n"
        )


def test_train_loso_fold_excludes_held_out_species_and_fits_scaler_on_train_only(monkeypatch):
    monkeypatch.setitem(sys.modules, "xgboost", types.SimpleNamespace(XGBClassifier=DummyClassifier))
    features = np.asarray([[0.0], [1.0], [10.0], [11.0], [20.0], [21.0]])
    labels = np.asarray([0, 1, 0, 1, 0, 1])
    species_ids = np.asarray([0, 0, 1, 1, 2, 2])

    model, scaler, train, test = train_loso_fold(
        features, labels, species_ids, held_out_species_id=1, seed=42
    )

    assert set(species_ids[train]) == {0, 2}
    assert set(species_ids[test]) == {1}
    assert set(train).isdisjoint(test)
    assert scaler.n_samples_seen_ == len(train)
    assert model.n_fit == len(train)


def test_run_loso_writes_one_model_per_species_without_metrics(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "xgboost", types.SimpleNamespace(XGBClassifier=DummyClassifier))
    species = ("Anolis_carolinensis", "Homo_sapiens", "Mus_musculus")
    _write_raw_dataset(tmp_path / "data", species)
    models = tmp_path / "models/loso"

    trained = run_loso(tmp_path / "data", models, expected_species=species)

    assert len(trained) == len(species)
    assert len(list(models.glob("*_loso.pkl"))) == len(species)
    assert (models / "config.json").is_file()

    with (models / "Anolis_carolinensis_loso.pkl").open("rb") as handle:
        artifact = pickle.load(handle)
    assert artifact["test_species"] == "Anolis_carolinensis"
    assert set(artifact["train_species"]) == set(species) - {"Anolis_carolinensis"}


def test_evaluate_loso_exports_metrics_separately(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "xgboost", types.SimpleNamespace(XGBClassifier=DummyClassifier))
    species = ("Anolis_carolinensis", "Homo_sapiens", "Mus_musculus")
    _write_raw_dataset(tmp_path / "data", species)
    models = tmp_path / "models/loso"
    run_loso(tmp_path / "data", models, expected_species=species)

    output = tmp_path / "outputs/evaluation/loso"
    result_path, summary_path = evaluate_loso(
        tmp_path / "data", models, output, expected_species=species
    )

    assert result_path == output / "metrics_loso.csv"
    assert summary_path == output / "metrics_loso_summary.csv"
    assert len((output / "metrics_loso.csv").read_text().splitlines()) == 4
    assert (output / "distribution.csv").is_file()


def test_run_loso_reports_all_missing_raw_inputs(tmp_path):
    with pytest.raises(FileNotFoundError) as error:
        run_loso(
            tmp_path / "data",
            tmp_path / "outputs",
            expected_species=("Anolis_carolinensis", "Homo_sapiens"),
        )

    message = str(error.value)
    assert "Anolis_carolinensis.cds.fa" in message
    assert "Homo_sapiens.ncrna.fa" in message
