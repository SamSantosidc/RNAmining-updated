import pickle
import sys
import types

import numpy as np

from rnamining.cli import main
from rnamining.data_preparation import SPECIES
from test_data_preparation import make_s5_zip
from test_training_inference import SmallModel


class DummyClassifier:
    def fit(self, matrix, labels):
        self.rows = len(matrix)
        return self


def test_prepare_data_cli(tmp_path):
    archive = tmp_path / "S5_File.zip"
    make_s5_zip(archive, SPECIES, coding_count=2, noncoding_count=2)
    assert main(["prepare-data", "--input", str(archive), "--output", str(tmp_path / "data")]) == 0
    assert len(list((tmp_path / "data/evaluation").glob("*_test.fa"))) == 16


def test_train_cli(tmp_path, monkeypatch):
    coding = tmp_path / "data/coding"
    noncoding = tmp_path / "data/noncoding"
    coding.mkdir(parents=True)
    noncoding.mkdir(parents=True)
    (coding / "Test_species_coding_train.fa").write_text(">c\nAAA\n")
    (noncoding / "Test_species_noncoding_train.fa").write_text(">n\nCCC\n")
    monkeypatch.setitem(sys.modules, "xgboost", types.SimpleNamespace(XGBClassifier=DummyClassifier))
    output = tmp_path / "models"
    assert main(["train", "--data", str(tmp_path / "data"), "--output", str(output)]) == 0
    assert (output / "Test_species.pkl").is_file()


def test_predict_cli(tmp_path):
    source = tmp_path / "input.fa"
    source.write_text(">one\nAAA\n")
    models = tmp_path / "models"
    models.mkdir()
    with (models / "Test_species.pkl").open("wb") as handle:
        pickle.dump(SmallModel(), handle)
    output = tmp_path / "result"
    assert main(["predict", "--input", str(source), "--organism", "Test_species", "--output", str(output), "--models", str(models)]) == 0
    assert (output / "predictions.txt").is_file()

