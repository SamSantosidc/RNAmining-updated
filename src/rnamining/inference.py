"""Model selection, prediction, and legacy-compatible output files."""

import pickle
import zipfile
from pathlib import Path

from .fasta import canonicalize_fasta, read_fasta, write_fasta
from .features import feature_matrix


def default_model_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "models" / "coding_prediction"



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
        artifact = pickle.load(handle)

    # New experiment artifacts contain the fitted preprocessing step together
    # with the model. Historical organism models remain plain estimators.
    if isinstance(artifact, dict) and "model" in artifact:
        model = artifact["model"]
        scaler = artifact.get("scaler")
    else:
        model = artifact
        scaler = None

    matrix = feature_matrix(records)
    if scaler is not None:
        matrix = scaler.transform(matrix)
    predictions = model.predict(matrix)
    probabilities = model.predict_proba(matrix)

    prediction_path = output / "predictions.txt"
    with prediction_path.open("w", encoding="utf-8") as result:
        result.write("RNAMining Predictions\n")
        result.write(f"Prediction Type: {prediction_type}\n")
        result.write(f"Name of the Organism: {organism}\n")
        result.write("Sequence ID \t Predictions:\n\n")

        for index, (record, prediction, probability) in enumerate(zip(records, predictions, probabilities)):
            label = "non-coding" if int(prediction) == 0 else "coding"
            ending = "\n" if index < len(records) - 1 else ""
            result.write(f"{record.header}\t{label}\t{max(probability)}{ending}")

    coding = [record for record, value in zip(records, predictions) if int(value) != 0]
    noncoding = [record for record, value in zip(records, predictions) if int(value) == 0]

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
