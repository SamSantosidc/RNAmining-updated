"""The installed ``rnamining`` command."""

import argparse

from .data_preparation import prepare_data, prepare_single_species
from .inference import predict_file
from .random_split import run_random_split
from .training import train_models, train_single_species


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

    predict = commands.add_parser("predict", help="predict RNA coding potential")
    predict.add_argument("--input", required=True)
    predict.add_argument("--organism", required=True)
    predict.add_argument("--output", required=True)
    predict.add_argument("--models", default=None, help=argparse.SUPPRESS)

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

    elif args.command == "predict":
        predict_file(args.input, args.organism, args.output, model_dir=args.models)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
