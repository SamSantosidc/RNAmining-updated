"""Legacy-compatible RNAmining trinucleotide feature extraction."""

from __future__ import annotations

from itertools import product
from typing import Iterable, Sequence

from .fasta import FastaRecord

# This is the effective order produced by the legacy counter's A/C/T/G index map.
TRINUCLEOTIDES = tuple("".join(parts) for parts in product("actg", repeat=3))



def trinucleotide_counts(sequence: str) -> list[int]:
    counts = {triplet: 0 for triplet in TRINUCLEOTIDES}
    sequence = sequence.lower()

    for offset in range(0, len(sequence) - 2, 3):
        triplet = sequence[offset : offset + 3]
        if triplet in counts:
            counts[triplet] += 1

    return [counts[triplet] for triplet in TRINUCLEOTIDES]



def normalized_features(sequence: str) -> list[float]:
    counts = trinucleotide_counts(sequence)
    nucleotide_count = sum(counts) * 3

    if nucleotide_count == 0:
        # NumPy produced NaN for this case in the original implementation.
        return [float("nan")] * len(counts)
    
    return [count / nucleotide_count for count in counts]



def feature_matrix(records: Iterable[FastaRecord]):
    """Return the 64-column NumPy matrix expected by the versioned models."""
    import numpy as np

    return np.asarray([normalized_features(record.sequence) for record in records], dtype=float)
