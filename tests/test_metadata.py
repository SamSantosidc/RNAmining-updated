import csv

import pytest

from rnamining.data_preparation import prepare_single_species
from rnamining.metadata import (
    DISTANCE_GROUP_CLASSIFICATIONS,
    SPECIES,
    SPECIES_METADATA,
    get_species_metadata,
    normalize_species_name,
    select_species,
    validate_species_names,
)
from test_data_preparation import make_single_species_zip


def test_catalog_contains_all_sixteen_species_and_two_classifications():
    assert len(SPECIES) == 16
    assert set(SPECIES) == set(SPECIES_METADATA)
    assert {item.evolutionary_distance_group for item in SPECIES_METADATA.values()} == {
        "A", "B", "C", "D", "E"
    }
    assert len({item.evolutionary_group for item in SPECIES_METADATA.values()}) == 11


def test_catalog_has_explicit_sarcopterygii_and_agnatha_groups():
    assert get_species_metadata("Latimeria chalumnae").evolutionary_group == (
        "Peixes de nadadeiras lobadas — Sarcopterygii"
    )
    assert get_species_metadata("Petromyzon_marinus").evolutionary_group == (
        "Ciclóstomos — Agnatha"
    )
    assert get_species_metadata("Eptatretus_burgeri").evolutionary_group == (
        "Ciclóstomos — Agnatha"
    )


def test_normalization_accepts_scientific_and_canonical_names():
    assert normalize_species_name(" Homo   sapiens ") == "Homo_sapiens"
    assert normalize_species_name("Latimeria_chalumnae") == "Latimeria_chalumnae"


def test_unknown_and_duplicate_species_are_rejected():
    with pytest.raises(ValueError, match="Unknown species"):
        normalize_species_name("Unknown species")
    with pytest.raises(ValueError, match="duplicates"):
        validate_species_names(("Homo_sapiens", "Homo sapiens"))


def test_species_filters_can_combine_group_dimensions():
    assert set(select_species(distance_group="A")) == {
        "Homo_sapiens", "Mus_musculus", "Rattus_norvegicus",
        "Monodelphis_domestica", "Ornithorhynchus_anatinus",
    }
    assert select_species(evolutionary_group="Ciclóstomos — Agnatha") == (
        "Eptatretus_burgeri", "Petromyzon_marinus"
    )
    assert select_species(
        evolutionary_group="Peixes de nadadeiras lobadas — Sarcopterygii",
        distance_group="D",
    ) == ("Latimeria_chalumnae",)
    assert DISTANCE_GROUP_CLASSIFICATIONS["E"] == "Vertebrados basais"


def test_single_species_reports_include_metadata_and_group_counts(tmp_path):
    archive = tmp_path / "single.zip"
    make_single_species_zip(
        archive,
        species="Latimeria_chalumnae",
        coding_count=3,
        noncoding_count=2,
    )
    root = tmp_path / "data"
    prepare_single_species(archive, root)

    with (root / "reports/organism_sequences_stats.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert {row["evolutionary_group"] for row in rows} == {
        "Peixes de nadadeiras lobadas — Sarcopterygii"
    }
    assert {row["evolutionary_distance_group"] for row in rows} == {"D"}

    with (root / "reports/evolutionary_distance_group_stats.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        distance_rows = list(csv.DictReader(handle))
    assert distance_rows == [{
        "evolutionary_distance_group": "D",
        "n_samples": "5",
        "n_coding": "3",
        "n_noncoding": "2",
    }]
