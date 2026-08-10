"""Global, stratified random-split experiment for the S5 dataset."""

from __future__ import annotations

import json
import pickle
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from .data_preparation import SPECIES
from .evaluation import evaluate_model, export_results, summarize_metrics
from .fasta import FastaRecord, iter_fasta, write_fasta
from .features import normalized_features

def _load_samples(data_dir, species):
    root = Path(data_dir)
    missing = []
    sources = []
    n_samples = 0
    for species_id, name in enumerate(species):
        paths = ((root / "raw" / f"{name}.cds.fa", 1),
                 (root / "raw" / f"{name}.ncrna.fa", 0))
        if any(not path.is_file() for path, _ in paths):
            missing.extend(str(path) for path, _ in paths if not path.is_file())
            continue
        for path, label in paths:
            count = sum(1 for _ in iter_fasta(path))
            sources.append((path, count, label, species_id))
            n_samples += count
    if missing:
        raise FileNotFoundError("Missing raw FASTA file(s): " + ", ".join(missing))
    if not n_samples or {label for _, _, label, _ in sources} != {0, 1}:
        raise ValueError("Random Split requires non-empty coding and noncoding samples.")
    return sources, n_samples


def _load_features(sources, n_samples):
    import numpy as np

    features = np.empty((n_samples, 64), dtype=np.float32)
    labels = np.empty(n_samples, dtype=np.int8)
    species_ids = np.empty(n_samples, dtype=np.int16)
    sample_index = 0
    for path, _, label, species_id in sources:
        for record in iter_fasta(path):
            features[sample_index] = normalized_features(record.sequence)
            labels[sample_index] = label
            species_ids[sample_index] = species_id
            sample_index += 1
    return features, labels, species_ids


def _distribution(labels, species_ids, indices, split_name, seed, species):
    rows = []
    for species_name in sorted(species):
        for label, class_name in ((1, "coding"), (0, "noncoding")):
            count = sum(
                labels[index] == label and species_ids[index] == species.index(species_name)
                for index in indices
            )
            rows.append({"seed": seed, "split": split_name, "species": species_name,
                         "class": class_name, "count": count})
    return rows


def train_random_split(features, labels, *, seed, test_size):
    """Fit one generalist model and return its split and preprocessing state."""
    import numpy as np
    from xgboost import XGBClassifier

    indices = np.arange(len(labels))
    train_indices, test_indices = train_test_split(
        indices, test_size=test_size, random_state=seed, stratify=labels
    )
    scaler = StandardScaler()
    train_features = scaler.fit_transform(features[train_indices])
    test_features = scaler.transform(features[test_indices])
    model = XGBClassifier(random_state=seed, n_jobs=1)
    model.fit(train_features, labels[train_indices])
    return model, scaler, train_indices, test_indices, test_features


def run_random_split(data_dir, output_dir, *, seeds=(42,), expected_species=SPECIES,
                     test_size=0.2, model_dir=None):
    """Train generalist model(s) and evaluate them through the shared metrics module.

    ``output_dir`` is the evaluation directory. ``model_dir`` is separate so the
    CLI follows the project's models/evaluation directory convention. If omitted,
    the legacy output/models location is retained for direct Python callers.
    """
    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1.")
    seeds = tuple(int(seed) for seed in seeds)
    if not seeds:
        raise ValueError("At least one seed is required.")
    species = tuple(expected_species)
    if not species:
        raise ValueError("At least one species is required.")

    sources, n_samples = _load_samples(data_dir, species)
    features, labels, species_ids = _load_features(sources, n_samples)
    output = Path(output_dir)
    if model_dir is None:
        models = output / "models"
        evaluation = output / "evaluation"
    else:
        models = Path(model_dir)
        evaluation = output
    models.mkdir(parents=True, exist_ok=True)
    evaluation.mkdir(parents=True, exist_ok=True)

    metrics_rows = []
    distribution_rows = []
    for seed in seeds:
        model, scaler, train_indices, test_indices, test_features = train_random_split(
            features, labels, seed=seed, test_size=test_size
        )
        metrics = evaluate_model(model, test_features, labels[test_indices])
        metrics_rows.append({"experiment": "random_split", "model_scope": "generalist",
                             "seed": seed, "repetition": 1, "n_train": len(train_indices),
                             "n_test": len(test_indices), **metrics})
        distribution_rows.extend(_distribution(labels, species_ids, train_indices, "train", seed, species))
        distribution_rows.extend(_distribution(labels, species_ids, test_indices, "test", seed, species))
        test_set = set(int(index) for index in test_indices)

        def test_records():
            offset = 0
            for path, _, _, _ in sources:
                for record in iter_fasta(path):
                    if offset in test_set:
                        yield FastaRecord(
                            record.header + " class:" + ("coding" if labels[offset] else "noncoding"),
                            record.sequence,
                        )
                    offset += 1

        write_fasta(test_records(), evaluation / f"random_split_seed_{seed}_test.fa")
        with (models / f"random_split_seed_{seed}.pkl").open("wb") as handle:
            pickle.dump({"model": model, "scaler": scaler, "seed": seed}, handle, protocol=-1)

    export_results(metrics_rows, output / "metrics.csv")
    export_results(distribution_rows, output / "distribution.csv")
    summary = summarize_metrics(metrics_rows)
    export_results([{"experiment": "random_split", "model_scope": "generalist", **summary}],
                   output / "metrics_summary.csv")
    config = {
        "scenario": "random_split", "species": list(species), "n_species": len(species),
        "seeds": list(seeds), "test_size": test_size, "train_size": 1 - test_size,
        "stratified_by": "class", "feature_extraction": "normalized_trinucleotide_counts",
        "preprocessing": "StandardScaler fitted on train split per seed",
        "model": "XGBClassifier", "model_parameters": {"random_state": "seed", "n_jobs": 1},
        "n_samples": n_samples,
    }
    (output / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return {"metrics": metrics_rows, "summary": summary, "config": config}
