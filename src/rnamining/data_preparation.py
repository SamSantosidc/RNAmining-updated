"""Reproducible extraction and preparation of the 16-species S5 dataset."""

from __future__ import annotations

import csv
import gzip
import random
import statistics
import zipfile
from pathlib import Path
from typing import Iterable, Optional

from .fasta import FastaRecord, read_fasta, write_fasta

SPECIES = (
    "Anolis_carolinensis", "Chrysemys_picta_bellii", "Crocodylus_porosus",
    "Danio_rerio", "Eptatretus_burgeri", "Gallus_gallus", "Homo_sapiens",
    "Latimeria_chalumnae", "Monodelphis_domestica", "Mus_musculus",
    "Notechis_scutatus", "Ornithorhynchus_anatinus", "Petromyzon_marinus",
    "Rattus_norvegicus", "Sphenodon_punctatus", "Xenopus_tropicalis",
)


def _classify_name(name: str) -> Optional[tuple[str, str]]:
    base = Path(name).name
    lower = base.lower()
    kind = "cds" if "cds" in lower else "ncrna" if "ncrna" in lower else None

    if kind is None:
        return None
    
    species = base.split(".")[0]
    return species, kind



def _extract_zip(source: Path, raw_dir: Path) -> None:
    with zipfile.ZipFile(source) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue

            classified = _classify_name(info.filename)
            if classified is None:
                continue

            species, kind = classified
            payload = archive.read(info)
            if info.filename.lower().endswith(".gz"):
                payload = gzip.decompress(payload)

            (raw_dir / f"{species}.{kind}.fa").write_bytes(payload)



def dataset_statistics(files: dict[str, dict[str, Path]]) -> list[dict]:
    rows = []
    for species in sorted(files):
        pair = files[species]

        for kind in ("cds", "ncrna"):
            path = pair.get(kind)
            lengths = [len(record.sequence) for record in read_fasta(path)] if path else []
            rows.append({
                "species": species,
                "seq_type": kind,
                "has_cds": "cds" in pair,
                "has_ncrna": "ncrna" in pair,
                "file_name": path.name if path else None,
                "n_sequences": len(lengths) if path else None,
                "min_len": min(lengths) if lengths else None,
                "max_len": max(lengths) if lengths else None,
                "mean_len": statistics.mean(lengths) if lengths else None,
                "median_len": statistics.median(lengths) if lengths else None,
            })

    return rows



def prepare_data(
    input_zip,
    output_dir,
    *,
    expected_species: Iterable[str] = SPECIES,
    seed: int = 42,
    train_ratio: float = 0.8,
    ) -> list[str]:
    
    output = Path(output_dir)
    raw = output / "raw"
    split = output / "processed" / "train_test_split"
    coding = split / "coding"
    noncoding = split / "noncoding"
    evaluation = output / "evaluation"
    reports = output / "reports"

    for directory in (raw, coding, noncoding, evaluation, reports):
        directory.mkdir(parents=True, exist_ok=True)

    _extract_zip(Path(input_zip), raw)

    files: dict[str, dict[str, Path]] = {}
    for path in raw.glob("*.fa"):
        classified = _classify_name(path.name)

        if classified:
            species, kind = classified
            files.setdefault(species, {})[kind] = path

    expected = set(expected_species)
    complete = {species for species, pair in files.items() if {"cds", "ncrna"} <= pair.keys()}

    missing = sorted(expected - complete)
    unexpected = sorted(complete - expected)
    if missing or unexpected:
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))

        if unexpected:
            details.append("unexpected: " + ", ".join(unexpected))

        raise ValueError("S5 dataset must contain the expected species pairs (" + "; ".join(details) + ")")

    rows = dataset_statistics({species: files[species] for species in expected})
    report_path = reports / "organism_sequences_stats.csv"

    with report_path.open("w", newline="", encoding="utf-8") as report:
        writer = csv.DictWriter(report, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    rng = random.Random(seed)
    for species in sorted(expected):
        cds = read_fasta(files[species]["cds"])
        ncrna = read_fasta(files[species]["ncrna"])
        count = min(len(cds), len(ncrna))

        if len(cds) > count:
            cds = rng.sample(cds, count)

        if len(ncrna) > count:
            ncrna = rng.sample(ncrna, count)

        rng.shuffle(cds)
        rng.shuffle(ncrna)
        boundary = int(count * train_ratio)
        cds_train, cds_test = cds[:boundary], cds[boundary:]
        ncrna_train, ncrna_test = ncrna[:boundary], ncrna[boundary:]
        write_fasta(cds_train, coding / f"{species}_coding_train.fa")
        write_fasta(cds_test, coding / f"{species}_coding_test.fa")
        write_fasta(ncrna_train, noncoding / f"{species}_noncoding_train.fa")
        write_fasta(ncrna_test, noncoding / f"{species}_noncoding_test.fa")

        mixed = [FastaRecord(r.header + " class:coding", r.sequence) for r in cds_test]
        mixed += [FastaRecord(r.header + " class:noncoding", r.sequence) for r in ncrna_test]
        rng.shuffle(mixed)
        write_fasta(mixed, evaluation / f"{species}_test.fa")
        
    return sorted(expected)
