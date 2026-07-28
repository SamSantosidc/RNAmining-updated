import csv
import gzip
import zipfile

import pytest

from rnamining.data_preparation import prepare_data, prepare_single_species
from rnamining.fasta import read_fasta


def make_s5_zip(path, species=("Alpha_beta",), coding_count=6, noncoding_count=4):
    with zipfile.ZipFile(path, "w") as archive:
        for name in species:
            coding = "".join(f">c{i}\nAAACCC\n" for i in range(coding_count))
            noncoding = "".join(f">n{i}\nTTTGGG\n" for i in range(noncoding_count))
            archive.writestr(f"S5/{name}.cds.fa", coding)
            archive.writestr(f"S5/{name}.ncrna.fa", noncoding)


def make_single_species_zip(
    path,
    species="Anolis_carolinensis",
    assembly="AnoCar2.0v2",
    coding_count=6,
    noncoding_count=4,
):
    coding = "".join(f">c{i}\nAAACCC\n" for i in range(coding_count)).encode()
    noncoding = "".join(f">n{i}\nTTTGGG\n" for i in range(noncoding_count)).encode()
    prefix = f"{species}.{assembly}"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(f"{prefix}.cds.all.fa.gz", gzip.compress(coding))
        archive.writestr(f"{prefix}.ncrna.fa.gz", gzip.compress(noncoding))


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


def test_single_species_preparation_accepts_dotted_assembly_and_reuses_outputs(tmp_path):
    archive = tmp_path / "Anolis_carolinensis.zip"
    make_single_species_zip(archive)

    root = tmp_path / "data"
    assert prepare_single_species(archive, root) == "Anolis_carolinensis"

    assert len(read_fasta(root / "raw/Anolis_carolinensis.cds.fa")) == 6
    assert len(read_fasta(root / "raw/Anolis_carolinensis.ncrna.fa")) == 4
    assert len(read_fasta(
        root / "processed/train_test_split/coding/Anolis_carolinensis_coding_train.fa"
    )) == 3
    assert len(read_fasta(
        root / "processed/train_test_split/noncoding/Anolis_carolinensis_noncoding_test.fa"
    )) == 1
    mixed = read_fasta(root / "evaluation/Anolis_carolinensis_test.fa")
    assert {record.header.rsplit("class:", 1)[1] for record in mixed} == {
        "coding",
        "noncoding",
    }


def test_single_species_preparation_accumulates_and_replaces_report_rows(tmp_path):
    root = tmp_path / "data"
    alpha = tmp_path / "alpha.zip"
    beta = tmp_path / "beta.zip"
    make_single_species_zip(alpha, species="Alpha_beta", assembly="Alpha1")
    make_single_species_zip(beta, species="Beta_gamma", assembly="Beta1")

    prepare_single_species(alpha, root)
    prepare_single_species(beta, root)
    make_single_species_zip(alpha, species="Alpha_beta", assembly="Alpha2", coding_count=2, noncoding_count=2)
    prepare_single_species(alpha, root)

    with (root / "reports/organism_sequences_stats.csv").open(
        newline="",
        encoding="utf-8",
    ) as report:
        rows = list(csv.DictReader(report))

    assert {row["species"] for row in rows} == {"Alpha_beta", "Beta_gamma"}
    assert len([row for row in rows if row["species"] == "Alpha_beta"]) == 2
    assert {
        row["n_sequences"] for row in rows if row["species"] == "Alpha_beta"
    } == {"2"}
    assert (root / "raw/Beta_gamma.cds.fa").is_file()


@pytest.mark.parametrize(
    "members,match",
    [
        (
            {
                "Species.Assembly.cds.all.fa.gz": gzip.compress(b">c\nAAA\n"),
            },
            "exactly two",
        ),
        (
            {
                "Species.Assembly.cds.all.fa.gz": gzip.compress(b">c\nAAA\n"),
                "Species.Assembly.ncrna.fa.gz": gzip.compress(b">n\nCCC\n"),
                "README.txt": b"extra",
            },
            "exactly two",
        ),
        (
            {
                "nested/Species.Assembly.cds.all.fa.gz": gzip.compress(b">c\nAAA\n"),
                "nested/Species.Assembly.ncrna.fa.gz": gzip.compress(b">n\nCCC\n"),
            },
            "archive root",
        ),
        (
            {
                "Species.Assembly1.cds.all.fa.gz": gzip.compress(b">c\nAAA\n"),
                "Species.Assembly2.ncrna.fa.gz": gzip.compress(b">n\nCCC\n"),
            },
            "same species and assembly",
        ),
        (
            {
                "Species.Assembly.cds.all.fa": b">c\nAAA\n",
                "Species.Assembly.ncrna.fa.gz": gzip.compress(b">n\nCCC\n"),
            },
            "required compressed FASTA names",
        ),
    ],
)
def test_single_species_preparation_rejects_invalid_archives_without_outputs(
    tmp_path,
    members,
    match,
):
    archive = tmp_path / "invalid.zip"
    with zipfile.ZipFile(archive, "w") as source:
        for name, payload in members.items():
            source.writestr(name, payload)

    output = tmp_path / "data"
    with pytest.raises(ValueError, match=match):
        prepare_single_species(archive, output)

    assert not output.exists()


def test_single_species_preparation_validates_compression_and_fasta_before_writing(tmp_path):
    archive = tmp_path / "invalid.zip"
    with zipfile.ZipFile(archive, "w") as source:
        source.writestr("Species.Assembly.cds.all.fa.gz", b"not gzip")
        source.writestr(
            "Species.Assembly.ncrna.fa.gz",
            gzip.compress(b">n\nCCC\n"),
        )

    output = tmp_path / "data"
    with pytest.raises(gzip.BadGzipFile):
        prepare_single_species(archive, output)

    assert not output.exists()

    archive = tmp_path / "invalid-fasta.zip"
    with zipfile.ZipFile(archive, "w") as source:
        source.writestr(
            "Species.Assembly.cds.all.fa.gz",
            gzip.compress(b"not fasta\n"),
        )
        source.writestr(
            "Species.Assembly.ncrna.fa.gz",
            gzip.compress(b">n\nCCC\n"),
        )

    with pytest.raises(ValueError, match="FASTA format"):
        prepare_single_species(archive, output)

    assert not output.exists()
