"""XGBoost training using RNAmining's established feature representation."""

import pickle
import random
from pathlib import Path

from .data_preparation import validate_supported_species
from .fasta import read_fasta
from .features import feature_matrix


def balance_classes(coding, noncoding, *, seed: int = 42):
    rng = random.Random(seed)
    count = min(len(coding), len(noncoding))

    coding = rng.sample(list(coding), count) if len(coding) > count else list(coding)
    noncoding = rng.sample(list(noncoding), count) if len(noncoding) > count else list(noncoding)

    combined = [(record, 1) for record in coding] + [(record, 0) for record in noncoding]
    rng.shuffle(combined)

    return combined


def _train_pair(coding_path: Path, noncoding_path: Path, model_path: Path, *, seed: int):
    import numpy as np
    from xgboost import XGBClassifier

    balanced = balance_classes(read_fasta(coding_path), read_fasta(noncoding_path), seed=seed)
    records = [item[0] for item in balanced]
    labels = np.asarray([item[1] for item in balanced], dtype=int)

    model = XGBClassifier()
    model.fit(feature_matrix(records), labels)

    with model_path.open("wb") as handle:
        pickle.dump(model, handle, protocol=-1)

    return model_path


def train_single_species(data_dir, species: str, output_dir, *, seed: int = 42):
    """Train only the explicitly requested species model."""
    if not species or "/" in species or "\\" in species or species in {".", ".."}:
        raise ValueError("Species must be a filename-safe identifier.")

    validate_supported_species(species)
    data = Path(data_dir)
    coding_path = data / "coding" / f"{species}_coding_train.fa"
    noncoding_path = data / "noncoding" / f"{species}_noncoding_train.fa"

    missing = [str(path) for path in (coding_path, noncoding_path) if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing training FASTA file(s): " + ", ".join(missing))

    coding = read_fasta(coding_path)
    noncoding = read_fasta(noncoding_path)
    if not coding or not noncoding:
        raise ValueError("Coding and noncoding training FASTAs must both contain sequences.")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    return _train_pair(coding_path, noncoding_path, output / f"{species}.pkl", seed=seed)



def train_models(data_dir, output_dir, *, seed: int = 42):
    data = Path(data_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    trained = []
    for coding_path in sorted((data / "coding").glob("*_coding_train.fa")):
        species = coding_path.name[: -len("_coding_train.fa")]
        noncoding_path = data / "noncoding" / f"{species}_noncoding_train.fa"

        if not noncoding_path.exists():
            continue

        model_path = output / f"{species}.pkl"
        _train_pair(coding_path, noncoding_path, model_path, seed=seed)
        trained.append(model_path)
        
    return trained
