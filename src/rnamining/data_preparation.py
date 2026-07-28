"""Reproducible extraction and preparation of the 16-species S5 dataset."""

from __future__ import annotations

import csv
import gzip
import random
import statistics
import tempfile
import zipfile
from collections import Counter
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

DEGENERATE_BASES = tuple("RYSWKMBDHVN")
SINGLE_SPECIES_CODING_SUFFIX = ".cds.all.fa.gz"
SINGLE_SPECIES_NONCODING_SUFFIX = ".ncrna.fa.gz"


def validate_supported_species(species: str) -> str:
    """Require a species to be explicitly approved in the project catalog."""
    if species not in SPECIES:
        raise ValueError(
            f"Unsupported species {species!r}. Add it to "
            "rnamining.data_preparation.SPECIES before preparing or training it."
        )

    return species


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


def _read_fasta_payload(payload: bytes, filename: str) -> list[FastaRecord]:
    with tempfile.TemporaryDirectory() as temporary_dir:
        path = Path(temporary_dir) / filename
        path.write_bytes(payload)
        return read_fasta(path)


def _single_species_archive(input_zip) -> tuple[str, list[FastaRecord], list[FastaRecord]]:
    with zipfile.ZipFile(input_zip) as archive:
        members = [info for info in archive.infolist() if not info.is_dir()]

        if len(members) != 2:
            raise ValueError("Single-species ZIP must contain exactly two files.")

        if any(Path(info.filename).name != info.filename for info in members):
            raise ValueError("Single-species ZIP files must be at the archive root.")

        by_kind = {}
        for info in members:
            if info.filename.endswith(SINGLE_SPECIES_CODING_SUFFIX):
                kind = "cds"
                suffix = SINGLE_SPECIES_CODING_SUFFIX
            elif info.filename.endswith(SINGLE_SPECIES_NONCODING_SUFFIX):
                kind = "ncrna"
                suffix = SINGLE_SPECIES_NONCODING_SUFFIX
            else:
                raise ValueError(
                    "Single-species ZIP files must use the required compressed FASTA names."
                )

            if kind in by_kind:
                raise ValueError("Single-species ZIP must contain one coding and one ncRNA file.")

            by_kind[kind] = (info, info.filename[: -len(suffix)])

        if set(by_kind) != {"cds", "ncrna"}:
            raise ValueError("Single-species ZIP must contain one coding and one ncRNA file.")

        coding_info, coding_prefix = by_kind["cds"]
        noncoding_info, noncoding_prefix = by_kind["ncrna"]
        if coding_prefix != noncoding_prefix:
            raise ValueError("Coding and ncRNA files must use the same species and assembly.")

        try:
            species, assembly = coding_prefix.split(".", 1)
        except ValueError as error:
            raise ValueError(
                "Single-species filenames must include both species and assembly."
            ) from error

        if not species or not assembly:
            raise ValueError("Single-species filenames must include both species and assembly.")

        validate_supported_species(species)
        coding_payload = gzip.decompress(archive.read(coding_info))
        noncoding_payload = gzip.decompress(archive.read(noncoding_info))

    coding_records = _read_fasta_payload(coding_payload, f"{species}.cds.fa")
    noncoding_records = _read_fasta_payload(noncoding_payload, f"{species}.ncrna.fa")
    return species, coding_records, noncoding_records



def dataset_statistics(files: dict[str, dict[str, Path]]) -> list[dict]:
    rows = []
    for species in sorted(files):
        pair = files[species]

        for kind in ("cds", "ncrna"):
            path = pair.get(kind)
            records = read_fasta(path) if path else []
            lengths = [len(record.sequence) for record in records]
            base_counts = Counter(
                base
                for record in records
                for base in record.sequence.upper()
                if base in DEGENERATE_BASES
            )
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
                **{base: base_counts[base] for base in DEGENERATE_BASES},
            })

    return rows


def _write_species_splits(
    species: str,
    cds: list[FastaRecord],
    ncrna: list[FastaRecord],
    coding_dir: Path,
    noncoding_dir: Path,
    evaluation_dir: Path,
    *,
    rng: random.Random,
    train_ratio: float,
) -> None:
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
    write_fasta(cds_train, coding_dir / f"{species}_coding_train.fa")
    write_fasta(cds_test, coding_dir / f"{species}_coding_test.fa")
    write_fasta(ncrna_train, noncoding_dir / f"{species}_noncoding_train.fa")
    write_fasta(ncrna_test, noncoding_dir / f"{species}_noncoding_test.fa")

    mixed = [FastaRecord(r.header + " class:coding", r.sequence) for r in cds_test]
    mixed += [FastaRecord(r.header + " class:noncoding", r.sequence) for r in ncrna_test]
    rng.shuffle(mixed)
    write_fasta(mixed, evaluation_dir / f"{species}_test.fa")


def _write_statistics_report(files: dict[str, dict[str, Path]], report_path: Path) -> None:
    rows = dataset_statistics(files)
    with report_path.open("w", newline="", encoding="utf-8") as report:
        writer = csv.DictWriter(report, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def prepare_single_species(
    input_zip,
    output_dir,
    *,
    seed: int = 42,
    train_ratio: float = 0.8,
) -> str:
    """Prepare one species from a strict two-member compressed FASTA archive."""
    species, cds, ncrna = _single_species_archive(input_zip)

    output = Path(output_dir)
    raw = output / "raw"
    split = output / "processed" / "train_test_split"
    coding = split / "coding"
    noncoding = split / "noncoding"
    evaluation = output / "evaluation"
    reports = output / "reports"

    for directory in (raw, coding, noncoding, evaluation, reports):
        directory.mkdir(parents=True, exist_ok=True)

    cds_path = raw / f"{species}.cds.fa"
    ncrna_path = raw / f"{species}.ncrna.fa"
    write_fasta(cds, cds_path)
    write_fasta(ncrna, ncrna_path)

    rng = random.Random(seed)
    _write_species_splits(
        species,
        cds,
        ncrna,
        coding,
        noncoding,
        evaluation,
        rng=rng,
        train_ratio=train_ratio,
    )

    files: dict[str, dict[str, Path]] = {}
    for path in raw.glob("*.fa"):
        classified = _classify_name(path.name)
        if classified:
            raw_species, kind = classified
            files.setdefault(raw_species, {})[kind] = path

    complete_files = {
        raw_species: pair
        for raw_species, pair in files.items()
        if {"cds", "ncrna"} <= pair.keys()
    }
    _write_statistics_report(
        complete_files,
        reports / "organism_sequences_stats.csv",
    )
    return species



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

    report_path = reports / "organism_sequences_stats.csv"
    _write_statistics_report(
        {species: files[species] for species in expected},
        report_path,
    )

    rng = random.Random(seed)
    for species in sorted(expected):
        cds = read_fasta(files[species]["cds"])
        ncrna = read_fasta(files[species]["ncrna"])
        _write_species_splits(
            species,
            cds,
            ncrna,
            coding,
            noncoding,
            evaluation,
            rng=rng,
            train_ratio=train_ratio,
        )
        
    return sorted(expected)
