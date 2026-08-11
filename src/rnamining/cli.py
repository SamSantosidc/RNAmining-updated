"""The installed ``rnamining`` command."""

import argparse
import pickle
from pathlib import Path

from .data_preparation import SPECIES, prepare_data, prepare_single_species
from .evaluation import evaluate_model, export_results, summarize_metrics
from .fasta import read_fasta
from .features import feature_matrix
from .inference import predict_file
from .loso import run_loso
from .loso_evaluation import evaluate_loso
from .metadata import get_species_metadata, select_species
from .random_split import run_random_split
from .training import train_models, train_single_species


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

    commands = parser.add_subparsers(dest="command", required=True)

    prepare = commands.add_parser("prepare-data", help="extract and prepare an S5 dataset")
    prepare.add_argument("--input", required=True)
    prepare.add_argument("--output", required=True)

    prepare_species = commands.add_parser(
        "prepare-species",
        help="extract and prepare one species",
    )
    prepare_species.add_argument("--input", required=True)
    prepare_species.add_argument("--output", required=True)

    train = commands.add_parser("train", help="train one model per organism")
    train.add_argument("--data", required=True)
    train.add_argument("--output", required=True)

    train_species = commands.add_parser(
        "train-species",
        help="train one explicitly selected species",
    )
    train_species.add_argument("--data", required=True)
    train_species.add_argument("--species", required=True)
    train_species.add_argument("--output", required=True)

    random_split = commands.add_parser(
        "random-split",
        help="train and evaluate a generalist model with a stratified random split",
    )
    random_split.add_argument("--data", required=True)
    random_split.add_argument("--output", required=True)
    random_split.add_argument("--models", default="models/random_split")
    random_split.add_argument("--seed", type=int, default=42)
    random_split.add_argument("--test-size", type=float, default=0.2)

    loso = commands.add_parser(
        "loso",
        help="train one model per held-out species",
    )
    loso.add_argument("--data", required=True)
    loso.add_argument("--models", default="models/loso")
    loso.add_argument("--seed", type=int, default=42)

    evaluate_loso_parser = commands.add_parser(
        "evaluate-loso",
        help="extract metrics from saved LOSO models",
    )
    evaluate_loso_parser.add_argument("--data", required=True)
    evaluate_loso_parser.add_argument("--models", default="models/loso")
    evaluate_loso_parser.add_argument("--output", required=True)
    evaluate_loso_parser.add_argument("--seed", type=int, default=42)

    predict = commands.add_parser("predict", help="predict RNA coding potential")
    predict.add_argument("--input", required=True)
    predict.add_argument("--organism", required=True)
    predict.add_argument("--output", required=True)
    predict.add_argument("--models", default=None, help=argparse.SUPPRESS)

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



def main(argv=None):
    args = build_parser().parse_args(argv)
    
    if args.command == "prepare-data":
        prepare_data(args.input, args.output)

    elif args.command == "prepare-species":
        prepare_single_species(args.input, args.output)

    elif args.command == "train":
        train_models(args.data, args.output)

    elif args.command == "train-species":
        train_single_species(args.data, args.species, args.output)

    elif args.command == "random-split":
        run_random_split(args.data, args.output, model_dir=args.models,
                         seeds=(args.seed,), test_size=args.test_size)

    elif args.command == "loso":
        run_loso(args.data, args.models, seed=args.seed)

    elif args.command == "evaluate-loso":
        evaluate_loso(
            args.data,
            args.models,
            args.output,
            seed=args.seed,
            expected_species=SPECIES,
        )

    elif args.command == "predict":
        predict_file(args.input, args.organism, args.output, model_dir=args.models)

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
