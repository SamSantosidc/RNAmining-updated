import pickle

import numpy as np

from rnamining.fasta import FastaRecord
from rnamining.inference import predict_file
from rnamining.training import balance_classes


class SmallModel:
    def predict(self, matrix):
        return np.asarray([1 if row[0] > 0 else 0 for row in matrix])

    def predict_proba(self, matrix):
        return np.asarray([[0.1, 0.9] if row[0] > 0 else [0.8, 0.2] for row in matrix])


def test_default_model_dir_honors_environment_override(monkeypatch, tmp_path):
    monkeypatch.setenv("RNAMINING_MODEL_DIR", str(tmp_path / "models"))
    from rnamining.inference import default_model_dir

    assert default_model_dir() == tmp_path / "models"


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
    assert "coding\tcoding\t0.9" in text
    assert "noncoding\tnon-coding\t0.8" in text
    assert (output / "codings.txt").read_text() == ">coding sequence\nAAA\n"
    assert (output / "noncodings.txt").read_text() == ">noncoding sequence\nCCC\n"
