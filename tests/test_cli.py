import pickle
import sys
import types

import numpy as np
import pytest

import rnamining.cli as cli
from rnamining.cli import main
from rnamining.data_preparation import SPECIES
from test_data_preparation import make_s5_zip, make_single_species_zip
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


def test_cli_exposes_reproducibility_and_output_options():
    args = cli.build_parser().parse_args([
        "prepare-data",
        "--input", "input.zip",
        "--output", "data",
        "--seed", "7",
        "--train-ratio", "0.75",
    ])
    assert args.seed == 7
    assert args.train_ratio == 0.75

    args = cli.build_parser().parse_args([
        "predict",
        "--input", "input.fa",
        "--organism", "Homo_sapiens",
        "--output", "output",
        "--models", "models",
        "--prediction-type", "custom_prediction",
    ])
    assert args.models == "models"
    assert args.prediction_type == "custom_prediction"


def test_pulposeq_compatibility_cli_writes_contract_outputs(tmp_path, monkeypatch):
    source = tmp_path / "transcripts.fa"
    source.write_text(
        ">qry001 transcript description\nAAA\n"
        ">qry002 another description\nCCC\n"
    )
    models = tmp_path / "models"
    models.mkdir()
    with (models / "Homo_sapiens.pkl").open("wb") as handle:
        pickle.dump(SmallModel(), handle)
    monkeypatch.setenv("RNAMINING_MODEL_DIR", str(models))

    output = tmp_path / "output"
    assert main([
        "-f", str(source),
        "-organism_name", "Homo_sapiens",
        "-prediction_type", "coding_prediction",
        "-output_folder", str(output),
    ]) == 0

    assert {path.name for path in output.glob("*.txt")} >= {
        "predictions.txt", "codings.txt", "noncodings.txt"
    }
    rows = (output / "predictions.txt").read_text().splitlines()
    assert rows[:5] == [
        "RNAMining Predictions",
        "Prediction Type: coding_prediction",
        "Name of the Organism: Homo_sapiens",
        "Sequence ID \t Predictions:",
        "",
    ]
    assert rows[5].split("\t") == ["qry001", "coding", "0.9"]
    assert rows[6].split("\t") == ["qry002", "non-coding", "0.8"]
    assert (output / "codings.txt").read_text() == ">qry001 transcript description\nAAA\n"
    assert (output / "noncodings.txt").read_text() == ">qry002 another description\nCCC\n"


def test_version_flag_reports_package_version(capsys):
    with pytest.raises(SystemExit) as error:
        main(["--version"])
    assert error.value.code == 0
    assert capsys.readouterr().out.strip() == "rnamining 1.1.0"


def test_legacy_cli_rejects_unsupported_prediction_type(tmp_path):
    with pytest.raises(ValueError, match="only 'coding_prediction' is supported"):
        main([
            "-f", str(tmp_path / "input.fa"),
            "-organism_name", "Homo_sapiens",
            "-prediction_type", "other",
            "-output_folder", str(tmp_path / "output"),
        ])


def test_cli_rejects_invalid_train_ratio():
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args([
            "prepare-data",
            "--input", "input.zip",
            "--output", "data",
            "--train-ratio", "1.0",
        ])


def test_prepare_single_species_cli(tmp_path):
    archive = tmp_path / "single.zip"
    make_single_species_zip(archive)
    output = tmp_path / "data"

    assert main([
        "prepare-species",
        "--input",
        str(archive),
        "--output",
        str(output),
    ]) == 0
    assert (output / "evaluation/Anolis_carolinensis_test.fa").is_file()


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


def test_train_single_species_cli_trains_only_requested_species(tmp_path, monkeypatch):
    coding = tmp_path / "data/coding"
    noncoding = tmp_path / "data/noncoding"
    coding.mkdir(parents=True)
    noncoding.mkdir(parents=True)
    for species in ("Anolis_carolinensis", "Homo_sapiens"):
        (coding / f"{species}_coding_train.fa").write_text(">c\nAAA\n")
        (noncoding / f"{species}_noncoding_train.fa").write_text(">n\nCCC\n")

    monkeypatch.setitem(sys.modules, "xgboost", types.SimpleNamespace(XGBClassifier=DummyClassifier))
    output = tmp_path / "models"
    assert main([
        "train-species",
        "--data",
        str(tmp_path / "data"),
        "--species",
        "Anolis_carolinensis",
        "--output",
        str(output),
    ]) == 0
    assert (output / "Anolis_carolinensis.pkl").is_file()
    assert not (output / "Homo_sapiens.pkl").exists()


def test_train_single_species_cli_requires_both_classes(tmp_path):
    coding = tmp_path / "data/coding"
    coding.mkdir(parents=True)
    (coding / "Gallus_gallus_coding_train.fa").write_text(">c\nAAA\n")

    with pytest.raises(FileNotFoundError, match="noncoding"):
        main([
            "train-species",
            "--data",
            str(tmp_path / "data"),
            "--species",
            "Gallus_gallus",
            "--output",
            str(tmp_path / "models"),
        ])


def test_train_single_species_cli_rejects_species_outside_catalog(tmp_path):
    with pytest.raises(ValueError, match=r"data_preparation\.SPECIES"):
        main([
            "train-species",
            "--data",
            str(tmp_path / "data"),
            "--species",
            "Unsupported_species",
            "--output",
            str(tmp_path / "models"),
        ])


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


def test_evaluate_cli_discovers_species_models_and_exports_metrics(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "SPECIES", ("Test_species",))
    models = tmp_path / "models"
    tests = tmp_path / "evaluation"
    models.mkdir()
    tests.mkdir()
    with (models / "Test_species.pkl").open("wb") as handle:
        pickle.dump(SmallModel(), handle)
    (tests / "Test_species_test.fa").write_text(
        ">coding class:coding\nAAA\n>noncoding class:noncoding\nCCC\n"
    )
    output = tmp_path / "results"

    assert main([
        "evaluate",
        "--models", str(models),
        "--tests", str(tests),
        "--output", str(output),
    ]) == 0

    results = (output / "metrics_current_models.csv").read_text()
    assert "species_specific" in results
    assert "Test_species" in results
    assert (output / "metrics_current_models_summary.csv").is_file()


def test_evaluate_cli_reports_all_missing_inputs(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "SPECIES", ("Alpha_beta", "Gamma_delta"))

    with pytest.raises(FileNotFoundError, match="Alpha_beta.pkl") as error:
        main([
            "evaluate",
            "--models", str(tmp_path / "models"),
            "--tests", str(tmp_path / "tests"),
            "--output", str(tmp_path / "output"),
        ])
    assert "Gamma_delta_test.fa" in str(error.value)
