import math

import pytest

from rnamining.fasta import FastaError, FastaRecord, read_fasta
from rnamining.features import TRINUCLEOTIDES, normalized_features, trinucleotide_counts


def test_reads_and_normalizes_multiline_fasta(tmp_path):
    path = tmp_path / "valid.fa"
    path.write_text(">one description\nACG\nTTA\n>two\nCCC\n")
    records = read_fasta(path)
    assert records == [FastaRecord("one description", "ACGTTA"), FastaRecord("two", "CCC")]


@pytest.mark.parametrize("content", ["ACGT\n", ">only-header\n", ""])
def test_rejects_invalid_fasta(tmp_path, content):
    path = tmp_path / "invalid.fa"
    path.write_text(content)
    with pytest.raises(FastaError):
        read_fasta(path)


def test_legacy_trinucleotide_order_and_frame_are_preserved():
    assert len(TRINUCLEOTIDES) == 64
    assert TRINUCLEOTIDES[:5] == ("aaa", "aac", "aat", "aag", "aca")
    counts = trinucleotide_counts("AAACCCGGGTTTAA")
    assert sum(counts) == 4
    assert counts[TRINUCLEOTIDES.index("aaa")] == 1
    assert counts[TRINUCLEOTIDES.index("ccc")] == 1
    assert counts[TRINUCLEOTIDES.index("ggg")] == 1
    assert counts[TRINUCLEOTIDES.index("ttt")] == 1
    features = normalized_features("AAACCC")
    assert sum(features) == pytest.approx(1 / 3)


def test_sequence_without_valid_triplet_matches_legacy_nan_behavior():
    assert all(math.isnan(value) for value in normalized_features("NN"))

