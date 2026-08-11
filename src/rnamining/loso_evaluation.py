"""Evaluation workflow for saved Leave-One-Species-Out models."""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np

from .data_preparation import SPECIES
from .evaluation import calculate_metrics, export_results, summarize_metrics
from .fasta import iter_fasta
from .features import normalized_features
from .metadata import get_species_metadata


def _evaluate_species_in_batches(model, scaler, data_dir, species_name, *, batch_size=8192):
    """Evaluate one species without retaining the complete raw dataset in memory."""
    root = Path(data_dir) / "raw"
    predictions = []
    scores = []
    labels = []
    counts = {1: 0, 0: 0}

    for filename, label in (
        (f"{species_name}.cds.fa", 1),
        (f"{species_name}.ncrna.fa", 0),
    ):
        batch = []
        for record in iter_fasta(root / filename):
            batch.append(normalized_features(record.sequence))
            if len(batch) == batch_size:
                matrix = scaler.transform(np.asarray(batch, dtype=np.float32))
                predictions.append(np.asarray(model.predict(matrix), dtype=np.int8))
                probabilities = model.predict_proba(matrix)
                classes = np.asarray(getattr(model, "classes_", []))
                positive_index = int(np.flatnonzero(classes == 1)[0]) if classes.size else 1
                scores.append(np.asarray(probabilities[:, positive_index], dtype=float))
                labels.append(np.full(len(batch), label, dtype=np.int8))
                counts[label] += len(batch)
                batch = []
        if batch:
            matrix = scaler.transform(np.asarray(batch, dtype=np.float32))
            predictions.append(np.asarray(model.predict(matrix), dtype=np.int8))
            probabilities = model.predict_proba(matrix)
            classes = np.asarray(getattr(model, "classes_", []))
            positive_index = int(np.flatnonzero(classes == 1)[0]) if classes.size else 1
            scores.append(np.asarray(probabilities[:, positive_index], dtype=float))
            labels.append(np.full(len(batch), label, dtype=np.int8))
            counts[label] += len(batch)

    if not labels:
        raise ValueError(f"Raw FASTA files are empty for {species_name}")
    return calculate_metrics(
        np.concatenate(labels), np.concatenate(predictions), np.concatenate(scores)
    ), counts


def _raw_species_counts(data_dir, species):
    """Count class samples once, without loading sequence contents."""
    root = Path(data_dir) / "raw"
    counts = {}
    missing = []
    for species_name in species:
        counts[species_name] = {}
        for filename, label in (
            (f"{species_name}.cds.fa", 1),
            (f"{species_name}.ncrna.fa", 0),
        ):
            path = root / filename
            if not path.is_file():
                missing.append(str(path))
                continue
            counts[species_name][label] = sum(1 for record in iter_fasta(path))
    if missing:
        raise FileNotFoundError("Missing raw FASTA file(s): " + ", ".join(missing))
    return counts


def evaluate_loso(data_dir, model_dir, output_dir, *, seed=42, expected_species=SPECIES):
    """Evaluate saved LOSO models and export detailed and summary metrics."""
    species = tuple(expected_species)
    species_counts = _raw_species_counts(data_dir, species)
    models = Path(model_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    missing = [
        str(models / f"{species_name}_loso.pkl")
        for species_name in species
        if not (models / f"{species_name}_loso.pkl").is_file()
    ]
    if missing:
        raise FileNotFoundError("Missing LOSO model file(s): " + ", ".join(missing))

    rows = []
    distribution = []
    for held_out_id, held_out_species in enumerate(species):
        with (models / f"{held_out_species}_loso.pkl").open("rb") as handle:
            artifact = pickle.load(handle)
        model = artifact["model"]
        scaler = artifact["scaler"]
        if artifact.get("test_species") != held_out_species:
            raise ValueError(
                f"Model artifact has the wrong held-out species: {held_out_species}"
            )
        metrics, test_counts = _evaluate_species_in_batches(
            model, scaler, data_dir, held_out_species
        )
        if test_counts != species_counts[held_out_species]:
            raise ValueError(f"Raw FASTA counts changed while evaluating {held_out_species}")
        n_train = sum(
            sum(counts.values())
            for name, counts in species_counts.items()
            if name != held_out_species
        )
        metadata = get_species_metadata(held_out_species)
        rows.append({
            "experiment": "loso",
            "model_scope": "leave_one_species_out",
            "test_species": held_out_species,
            "train_species": ";".join(name for name in species if name != held_out_species),
            "n_train_species": len(species) - 1,
            "n_train": int(n_train),
            "n_test": int(sum(test_counts.values())),
            "n_test_coding": int(test_counts[1]),
            "n_test_noncoding": int(test_counts[0]),
            "seed": seed,
            "evolutionary_group": metadata.evolutionary_group,
            "evolutionary_distance_group": metadata.evolutionary_distance_group,
            **metrics,
        })
        for split in ("train", "test"):
            for species_name in species:
                for label, class_name in ((1, "coding"), (0, "noncoding")):
                    count = species_counts[species_name][label]
                    if split == "train" and species_name == held_out_species:
                        count = 0
                    elif split == "test" and species_name != held_out_species:
                        count = 0
                    distribution.append({
                        "experiment": "loso",
                        "held_out_species": held_out_species,
                        "split": split,
                        "species": species_name,
                        "class": class_name,
                        "count": int(count),
                    })

        # Keep a usable checkpoint if a later fold exhausts the environment.
        export_results(rows, output / "metrics_loso.csv")
        export_results(distribution, output / "distribution.csv")

    result_path = export_results(rows, output / "metrics_loso.csv")
    summary_path = export_results([{
        "experiment": "loso",
        "model_scope": "leave_one_species_out",
        "n_models": len(rows),
        **summarize_metrics(rows),
    }], output / "metrics_loso_summary.csv")
    export_results(distribution, output / "distribution.csv")
    return result_path, summary_path
