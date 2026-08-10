import pickle
import csv

import numpy as np

from rnamining.fasta import FastaRecord
from rnamining.inference import predict_file
from rnamining.random_split import run_random_split
from rnamining.training import balance_classes


class SmallModel:
    def predict(self, matrix):
        return np.asarray([1 if row[0] > 0 else 0 for row in matrix])

    def predict_proba(self, matrix):
        return np.asarray([[0.1, 0.9] if row[0] > 0 else [0.8, 0.2] for row in matrix])


class IdentityScaler:
    def transform(self, matrix):
        return matrix


def test_balancing_is_equal_and_deterministic():
    coding = [FastaRecord(f"c{i}", "AAA") for i in range(7)]
    noncoding = [FastaRecord(f"n{i}", "CCC") for i in range(3)]
    first = balance_classes(coding, noncoding)
    second = balance_classes(coding, noncoding)
    assert first == second
    assert [label for _, label in first].count(1) == 3
    assert [label for _, label in first].count(0) == 3


def test_inference_labels_probabilities_and_fasta_outputs(tmp_path):
    source = tmp_path / "sequences.fa"
    source.write_text(">coding sequence\nAAA\n>noncoding sequence\nCCC\n")
    models = tmp_path / "models"
    models.mkdir()
    with (models / "Test_species.pkl").open("wb") as handle:
        pickle.dump(SmallModel(), handle)
    output = tmp_path / "output"
    predict_file(source, "Test_species", output, model_dir=models)
    text = (output / "predictions.txt").read_text()
    assert "coding sequence\tcoding\t0.9" in text
    assert "noncoding sequence\tnon-coding\t0.8" in text
    assert (output / "codings.txt").read_text() == ">coding sequence\nAAA\n"
    assert (output / "noncodings.txt").read_text() == ">noncoding sequence\nCCC\n"


def test_inference_supports_random_split_model_artifact(tmp_path):
    source = tmp_path / "sequences.fa"
    source.write_text(">coding sequence\nAAA\n>noncoding sequence\nCCC\n")
    models = tmp_path / "models"
    models.mkdir()

    with (models / "random_split_seed_42.pkl").open("wb") as handle:
        pickle.dump({"model": SmallModel(), "scaler": IdentityScaler(), "seed": 42}, handle)

    output = tmp_path / "output"
    predict_file(
        source,
        "random_split_seed_42",
        output,
        model_dir=models,
    )
    assert "coding sequence\tcoding\t0.9" in (output / "predictions.txt").read_text()


def test_random_split_writes_seeded_runs_and_train_only_scalers(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    species = ("Alpha_beta", "Beta_gamma")
    for name in species:
        (raw / f"{name}.cds.fa").write_text(">c0\nAAA\n>c1\nAAT\n")
        (raw / f"{name}.ncrna.fa").write_text(">n0\nCCC\n>n1\nCCT\n")

    output = tmp_path / "random"
    result = run_random_split(
        tmp_path,
        output,
        seeds=(7, 11),
        expected_species=species,
    )

    assert [row["n_train"] for row in result["metrics"]] == [6, 6]
    assert [row["n_test"] for row in result["metrics"]] == [2, 2]
    assert (output / "models/random_split_seed_7.pkl").is_file()
    assert (output / "models/random_split_seed_11.pkl").is_file()
    assert (output / "config.json").is_file()
    with (output / "models/random_split_seed_7.pkl").open("rb") as handle:
        artifact = pickle.load(handle)
    assert artifact["scaler"].n_samples_seen_ == 6
    with (output / "distribution.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["species"] for row in rows} == set(species)
    assert {row["split"] for row in rows} == {"train", "test"}
