"""The installed ``rnamining`` command."""

import argparse
import pickle
from pathlib import Path

from .data_preparation import SPECIES, prepare_data, prepare_single_species
from .evaluation import evaluate_model, export_results, summarize_metrics
from .fasta import read_fasta
from .features import feature_matrix
from .inference import predict_file
from .metadata import get_species_metadata, select_species
from .training import train_models, train_single_species
from . import __version__


def _train_ratio(value):
    ratio = float(value)
    if not 0 < ratio < 1:
        raise argparse.ArgumentTypeError("train ratio must be greater than 0 and less than 1")
    return ratio


def _ground_truth(records):
    labels = []
    for record in records:
        tokens = record.header.lower().split()
        coding = "class:coding" in tokens or "cds" in tokens
        noncoding = "class:noncoding" in tokens or "ncrna" in tokens
        if coding == noncoding:
            raise ValueError(f"Missing or ambiguous class in FASTA header: {record.header!r}")
        labels.append(1 if coding else 0)
    return labels


def _evaluate_species_models(
    models_dir,
    tests_dir,
    output_dir,
    *,
    seed,
    repetition,
    species=None,
    evolutionary_group=None,
    distance_group=None,
):
    models = Path(models_dir)
    tests = Path(tests_dir)
    if species is None and evolutionary_group is None and distance_group is None:
        selected_species = tuple(SPECIES)
    else:
        selected_species = select_species(
            species,
            evolutionary_group=evolutionary_group,
            distance_group=distance_group,
        )
    missing = []
    for species_name in selected_species:
        for path in (
            models / f"{species_name}.pkl",
            tests / f"{species_name}_test.fa",
        ):
            if not path.is_file():
                missing.append(str(path))
    if missing:
        raise FileNotFoundError("Missing evaluation file(s): " + ", ".join(missing))

    rows = []
    for species_name in selected_species:
        records = read_fasta(tests / f"{species_name}_test.fa")
        truth = _ground_truth(records)
        with (models / f"{species_name}.pkl").open("rb") as handle:
            model = pickle.load(handle)
        metrics = evaluate_model(model, feature_matrix(records), truth)
        row = {
            "experiment": "current_species_models",
            "model_scope": "species_specific",
            "test_species": species_name,
            "seed": seed,
            "repetition": repetition,
            "n_test": len(truth),
            "n_test_coding": truth.count(1),
            "n_test_noncoding": truth.count(0),
            **metrics,
        }
        try:
            metadata = get_species_metadata(species_name)
        except ValueError:
            metadata = None
        row.update({
            "evolutionary_group": metadata.evolutionary_group if metadata else None,
            "evolutionary_distance_group": (
                metadata.evolutionary_distance_group if metadata else None
            ),
        })
        rows.append(row)

    output = Path(output_dir)
    result_path = export_results(rows, output / "metrics_current_models.csv")
    summary = {
        "experiment": "current_species_models",
        "model_scope": "species_specific",
        "n_models": len(rows),
        **summarize_metrics(rows),
    }
    summary_path = export_results(
        [summary], output / "metrics_current_models_summary.csv"
    )

    metric_names = ("accuracy", "precision", "recall", "f1", "mcc", "auroc", "auprc")
    print("species\t" + "\t".join(metric_names))
    for row in rows:
        values = [
            "unavailable" if row[name] is None else f"{row[name]:.6f}"
            for name in metric_names
        ]
        print(row["test_species"] + "\t" + "\t".join(values))
    print(f"Results: {result_path}")
    print(f"Summary: {summary_path}")
    return result_path, summary_path


def build_parser():
    parser = argparse.ArgumentParser(prog="rnamining")
    parser.add_argument(
        "--version",
        action="version",
        version=f"rnamining {__version__}",
    )

    # This is the public interface used by PULPOSEQ.  Keep it at the root so
    # that `rnamining -f ...` does not require a compatibility subcommand.
    parser.add_argument("-f", dest="legacy_input", default=None, metavar="FASTA")
    parser.add_argument(
        "-organism_name",
        dest="legacy_organism",
        default=None,
        metavar="ORGANISM",
    )
    parser.add_argument(
        "-prediction_type",
        dest="legacy_prediction_type",
        default="coding_prediction",
        metavar="TYPE",
    )
    parser.add_argument(
        "-output_folder",
        dest="legacy_output",
        default=None,
        metavar="DIRECTORY",
    )

    commands = parser.add_subparsers(dest="command")

    prepare = commands.add_parser("prepare-data", help="extract and prepare an S5 dataset")
    prepare.add_argument("--input", required=True)
    prepare.add_argument("--output", required=True)
    prepare.add_argument("--seed", type=int, default=42)
    prepare.add_argument("--train-ratio", type=_train_ratio, default=0.8)

    prepare_species = commands.add_parser(
        "prepare-species",
        help="extract and prepare one species",
    )
    prepare_species.add_argument("--input", required=True)
    prepare_species.add_argument("--output", required=True)
    prepare_species.add_argument("--seed", type=int, default=42)
    prepare_species.add_argument("--train-ratio", type=_train_ratio, default=0.8)

    train = commands.add_parser("train", help="train one model per organism")
    train.add_argument("--data", required=True)
    train.add_argument("--output", required=True)
    train.add_argument("--seed", type=int, default=42)

    train_species = commands.add_parser(
        "train-species",
        help="train one explicitly selected species",
    )
    train_species.add_argument("--data", required=True)
    train_species.add_argument("--species", required=True)
    train_species.add_argument("--output", required=True)
    train_species.add_argument("--seed", type=int, default=42)

    predict = commands.add_parser("predict", help="predict RNA coding potential")
    predict.add_argument("--input", required=True)
    predict.add_argument("--organism", required=True)
    predict.add_argument("--output", required=True)
    predict.add_argument(
        "--models",
        default=None,
        help="directory containing <organism>.pkl (default: repository models directory)",
    )
    predict.add_argument("--prediction-type", default="coding_prediction")

    evaluate = commands.add_parser(
        "evaluate",
        help="evaluate the current species-specific models",
    )
    evaluate.add_argument("--models", default="models/coding_prediction")
    evaluate.add_argument("--tests", default="data/evaluation")
    evaluate.add_argument("--output", required=True)
    evaluate.add_argument("--seed", type=int, default=42)
    evaluate.add_argument("--repetition", type=int, default=1)
    evaluate.add_argument("--species", action="append", default=None)
    evaluate.add_argument("--evolutionary-group", default=None)
    evaluate.add_argument("--distance-group", default=None)

    return parser


def _validate_prediction_type(prediction_type):
    if prediction_type != "coding_prediction":
        raise ValueError(
            "Unsupported prediction type: "
            f"{prediction_type!r}; only 'coding_prediction' is supported"
        )



def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.command is None:
        legacy_values = (args.legacy_input, args.legacy_organism, args.legacy_output)
        if not any(value is not None for value in legacy_values):
            raise SystemExit("a command or the PULPOSEQ compatibility arguments are required")
        if any(value is None for value in legacy_values):
            raise SystemExit("-f, -organism_name, and -output_folder are required together")
        _validate_prediction_type(args.legacy_prediction_type)
        predict_file(
            args.legacy_input,
            args.legacy_organism,
            args.legacy_output,
            prediction_type=args.legacy_prediction_type,
        )

    elif args.command == "prepare-data":
        prepare_data(
            args.input,
            args.output,
            seed=args.seed,
            train_ratio=args.train_ratio,
        )

    elif args.command == "prepare-species":
        prepare_single_species(
            args.input,
            args.output,
            seed=args.seed,
            train_ratio=args.train_ratio,
        )

    elif args.command == "train":
        train_models(args.data, args.output, seed=args.seed)

    elif args.command == "train-species":
        train_single_species(args.data, args.species, args.output, seed=args.seed)

    elif args.command == "predict":
        _validate_prediction_type(args.prediction_type)
        predict_file(
            args.input,
            args.organism,
            args.output,
            model_dir=args.models,
            prediction_type=args.prediction_type,
        )

    elif args.command == "evaluate":
        _evaluate_species_models(
            args.models,
            args.tests,
            args.output,
            seed=args.seed,
            repetition=args.repetition,
            species=args.species,
            evolutionary_group=args.evolutionary_group,
            distance_group=args.distance_group,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
