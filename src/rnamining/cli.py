"""The installed ``rnamining`` command."""

import argparse

from .data_preparation import prepare_data
from .inference import predict_file
from .training import train_models


def build_parser():
    parser = argparse.ArgumentParser(prog="rnamining")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare-data", help="extract and prepare an S5 dataset")
    prepare.add_argument("--input", required=True)
    prepare.add_argument("--output", required=True)
    train = commands.add_parser("train", help="train one model per organism")
    train.add_argument("--data", required=True)
    train.add_argument("--output", required=True)
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
    elif args.command == "train":
        train_models(args.data, args.output)
    elif args.command == "predict":
        predict_file(args.input, args.organism, args.output, model_dir=args.models)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
