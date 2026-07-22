import csv
import zipfile

import pytest

from rnamining.data_preparation import prepare_data
from rnamining.fasta import read_fasta


def make_s5_zip(path, species=("Alpha_beta",), coding_count=6, noncoding_count=4):
    with zipfile.ZipFile(path, "w") as archive:
        for name in species:
            coding = "".join(f">c{i}\nAAACCC\n" for i in range(coding_count))
            noncoding = "".join(f">n{i}\nTTTGGG\n" for i in range(noncoding_count))
            archive.writestr(f"S5/{name}.cds.fa", coding)
            archive.writestr(f"S5/{name}.ncrna.fa", noncoding)


def test_preparation_balances_splits_reports_and_writes_ground_truth(tmp_path):
    archive = tmp_path / "S5_File.zip"
    make_s5_zip(archive)
    prepare_data(archive, tmp_path / "first", expected_species=("Alpha_beta",))
    prepare_data(archive, tmp_path / "second", expected_species=("Alpha_beta",))

    root = tmp_path / "first"
    assert len(read_fasta(root / "processed/train_test_split/coding/Alpha_beta_coding_train.fa")) == 3
    assert len(read_fasta(root / "processed/train_test_split/noncoding/Alpha_beta_noncoding_train.fa")) == 3
    assert len(read_fasta(root / "processed/train_test_split/coding/Alpha_beta_coding_test.fa")) == 1
    mixed = read_fasta(root / "evaluation/Alpha_beta_test.fa")
    assert {record.header.rsplit("class:", 1)[1] for record in mixed} == {"coding", "noncoding"}
    assert (root / "reports/organism_sequences_stats.csv").is_file()
    assert (root / "evaluation/Alpha_beta_test.fa").read_bytes() == (
        tmp_path / "second/evaluation/Alpha_beta_test.fa"
    ).read_bytes()


def test_preparation_validates_complete_species_pairs(tmp_path):
    archive = tmp_path / "S5_File.zip"
    make_s5_zip(archive)
    with pytest.raises(ValueError, match="missing"):
        prepare_data(archive, tmp_path / "data", expected_species=("Alpha_beta", "Missing_species"))


def test_preparation_reports_each_degenerate_iupac_base_occurrence(tmp_path):
    archive = tmp_path / "S5_File.zip"
    with zipfile.ZipFile(archive, "w") as source:
        source.writestr("S5/Alpha_beta.cds.fa", ">c\nRrYySsWwKkMmBbDdHhVvNnUuXx\n")
        source.writestr("S5/Alpha_beta.ncrna.fa", ">n\nACGT\n")

    root = tmp_path / "data"
    prepare_data(archive, root, expected_species=("Alpha_beta",))

    with (root / "reports/organism_sequences_stats.csv").open(newline="", encoding="utf-8") as report:
        rows = list(csv.DictReader(report))

    coding = next(row for row in rows if row["seq_type"] == "cds")
    noncoding = next(row for row in rows if row["seq_type"] == "ncrna")
    for base in "RYSWKMBDHVN":
        assert coding[base] == "2"
        assert noncoding[base] == "0"
