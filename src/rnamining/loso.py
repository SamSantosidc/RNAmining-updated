"""Leave-One-Species-Out model training workflow."""

from __future__ import annotations

import gc
import json
import pickle
from pathlib import Path

from sklearn.preprocessing import StandardScaler

from .data_preparation import SPECIES
from .fasta import iter_fasta
from .features import normalized_features


def _load_samples(data_dir, species):
    """Load all raw records and labels for LOSO training/evaluation."""
    import numpy as np

    root = Path(data_dir) / "raw"
    missing = []
    records = []
    labels = []
    species_ids = []
    sources = []

    for species_id, species_name in enumerate(species):
        for path, label in (
            (root / f"{species_name}.cds.fa", 1),
            (root / f"{species_name}.ncrna.fa", 0),
        ):
            if not path.is_file():
                missing.append(str(path))
                continue
            species_records = list(iter_fasta(path))
            if not species_records:
                raise ValueError(f"Raw FASTA file is empty: {path}")
            sources.append((path, len(species_records), label, species_id))
            records.extend(species_records)
            labels.extend([label] * len(species_records))
            species_ids.extend([species_id] * len(species_records))

    if missing:
        raise FileNotFoundError("Missing raw FASTA file(s): " + ", ".join(missing))
    if not records or set(labels) != {0, 1}:
        raise ValueError("LOSO requires non-empty coding and noncoding samples.")

    features = np.asarray(
        [normalized_features(record.sequence) for record in records],
        dtype=np.float32,
    )
    return (
        features,
        np.asarray(labels, dtype=np.int8),
        np.asarray(species_ids, dtype=np.int16),
        records,
        sources,
    )


def _raw_sources(data_dir, species):
    """Return and validate the raw FASTA paths without loading their contents."""
    root = Path(data_dir) / "raw"
    missing = []
    sources = []
    for species_id, species_name in enumerate(species):
        for path, label in (
            (root / f"{species_name}.cds.fa", 1),
            (root / f"{species_name}.ncrna.fa", 0),
        ):
            if not path.is_file():
                missing.append(str(path))
            else:
                sources.append((path, label, species_id))
    if missing:
        raise FileNotFoundError("Missing raw FASTA file(s): " + ", ".join(missing))
    return sources


def _load_fold_samples(data_dir, species, held_out_species_id):
    """Load only one fold's training features and held-out sample count."""
    import numpy as np

    sources = _raw_sources(data_dir, species)
    train_feature_blocks = []
    train_label_blocks = []
    n_test = 0
    n_total = 0

    for path, label, species_id in sources:
        # Convert bounded batches immediately; do not retain FASTA strings or records.
        feature_blocks = []
        batch = []
        file_count = 0
        for record in iter_fasta(path):
            batch.append(normalized_features(record.sequence))
            file_count += 1
            if len(batch) == 8192:
                feature_blocks.append(np.asarray(batch, dtype=np.float32))
                batch = []
        if batch:
            feature_blocks.append(np.asarray(batch, dtype=np.float32))
        if not file_count:
            raise ValueError(f"Raw FASTA file is empty: {path}")
        n_total += file_count
        if species_id == held_out_species_id:
            n_test += file_count
            continue
        train_feature_blocks.extend(feature_blocks)
        train_label_blocks.append(np.full(file_count, label, dtype=np.int8))

    if not train_feature_blocks or set(np.concatenate(train_label_blocks)) != {0, 1} or not n_test:
        raise ValueError("LOSO folds require non-empty training and test samples.")

    return (
        np.concatenate(train_feature_blocks),
        np.concatenate(train_label_blocks),
        n_test,
        n_total,
        sources,
    )


def _fit_model(train_features, train_labels, *, seed):
    """Fit one scaler/model pair from an already isolated fold."""
    from xgboost import XGBClassifier

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(train_features)
    model = XGBClassifier(random_state=seed, n_jobs=1)
    model.fit(scaled_features, train_labels)
    return model, scaler


def train_loso_fold(features, labels, species_ids, *, held_out_species_id, seed):
    """Train one fold and return its model, scaler, and train/test indices."""
    import numpy as np

    test_indices = np.flatnonzero(species_ids == held_out_species_id)
    train_indices = np.flatnonzero(species_ids != held_out_species_id)
    if not len(train_indices) or not len(test_indices):
        raise ValueError("LOSO folds require non-empty training and test species.")
    if set(labels[train_indices]) != {0, 1}:
        raise ValueError("LOSO training data must contain both coding classes.")

    model, scaler = _fit_model(features[train_indices], labels[train_indices], seed=seed)
    return model, scaler, train_indices, test_indices


def run_loso(data_dir, model_dir, *, seed=42, expected_species=SPECIES):
    """Train and save one independent model for each held-out species."""
    species = tuple(expected_species)
    if not species:
        raise ValueError("At least one species is required.")

    sources = _raw_sources(data_dir, species)
    models = Path(model_dir)
    models.mkdir(parents=True, exist_ok=True)

    trained = []
    n_samples = None
    for held_out_id, held_out_species in enumerate(species):
        print(f"Training LOSO fold {held_out_id + 1}/{len(species)}: {held_out_species}")
        features, labels, n_test, fold_n_samples, _ = _load_fold_samples(
            data_dir, species, held_out_id
        )
        model, scaler = _fit_model(features, labels, seed=seed)
        train_species = [name for name in species if name != held_out_species]
        model_path = models / f"{held_out_species}_loso.pkl"
        artifact = {
            "model": model,
            "scaler": scaler,
            "seed": seed,
            "test_species": held_out_species,
            "train_species": train_species,
            "n_train": int(len(labels)),
            "n_test": int(n_test),
            "feature_extraction": "normalized_trinucleotide_counts",
        }
        with model_path.open("wb") as handle:
            pickle.dump(artifact, handle, protocol=-1)
        trained.append(model_path)

        # Release Python and XGBoost allocations before reading the next fold.
        del artifact, model, scaler, features, labels
        gc.collect()
        if n_samples is None:
            n_samples = fold_n_samples

    config = {
        "scenario": "loso",
        "species": list(species),
        "n_species": len(species),
        "seed": seed,
        "test_definition": "all raw samples from the held-out species",
        "training_definition": "all raw samples from the other species",
        "preprocessing": "StandardScaler fitted independently on each training fold",
        "feature_extraction": "normalized_trinucleotide_counts",
        "model": "XGBClassifier",
        "model_parameters": {"random_state": seed, "n_jobs": 1},
        "n_samples": int(n_samples),
        "sources": [str(path) for path, _, _ in sources],
    }
    (models / "config.json").write_text(
        json.dumps(config, indent=2) + "\n", encoding="utf-8"
    )
    return trained
