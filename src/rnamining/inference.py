"""Model selection, prediction, and output files."""

import os
import pickle
import zipfile
from pathlib import Path

from .fasta import canonicalize_fasta, read_fasta, write_fasta
from .features import feature_matrix


def default_model_dir() -> Path:
    configured = os.environ.get("RNAMINING_MODEL_DIR")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "models" / "coding_prediction"


def _binary_prediction_label(prediction) -> int:
    """Validate the binary label convention used by RNAmining models."""
    try:
        label = int(prediction)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Model predicted an invalid class: {prediction!r}") from error

    if label not in (0, 1) or label != prediction:
        raise ValueError(
            "Model predictions must use the binary labels 0 (non-coding) "
            f"or 1 (coding), got {prediction!r}."
        )
    return label



def predict_file(input_path, organism, output_dir, *, model_dir=None, prediction_type="coding_prediction"):
    source = Path(input_path)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    edited = output / "edited_file.fasta"
    records = canonicalize_fasta(source, edited)

    model_path = Path(model_dir or default_model_dir()) / f"{organism}.pkl"
    if not model_path.is_file():
        raise FileNotFoundError(f"No model found for organism {organism!r}: {model_path}")
    
    with model_path.open("rb") as handle:
        model = pickle.load(handle)

    matrix = feature_matrix(records)
    predictions = model.predict(matrix)
    probabilities = model.predict_proba(matrix)
    labels = [_binary_prediction_label(prediction) for prediction in predictions]

    prediction_path = output / "predictions.txt"
    with prediction_path.open("w", encoding="utf-8") as result:
        result.write("RNAMining Predictions\n")
        result.write(f"Prediction Type: {prediction_type}\n")
        result.write(f"Name of the Organism: {organism}\n")
        result.write("Sequence ID \t Predictions:\n\n")

        for index, (record, prediction, probability) in enumerate(zip(records, labels, probabilities)):
            label = "non-coding" if prediction == 0 else "coding"
            ending = "\n" if index < len(records) - 1 else ""
            # PULPOSEQ merges this column with the GTF `qry_id`, which is the
            # first token of the FASTA header.  FASTA outputs retain the full
            # header, but the tabular identifier must be unambiguous.
            result.write(f"{record.identifier}\t{label}\t{max(probability)}{ending}")

    coding = [record for record, label in zip(records, labels) if label == 1]
    noncoding = [record for record, label in zip(records, labels) if label == 0]

    write_fasta(coding, output / "codings.txt")
    write_fasta(noncoding, output / "noncodings.txt")

    return prediction_path



def create_result_archive(output_dir) -> Path:
    output = Path(output_dir)

    archive = output / "RNAmining.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zipped:
        for name in ("predictions.txt", "codings.txt", "noncodings.txt"):
            zipped.write(output / name, arcname=name)
            
    return archive
