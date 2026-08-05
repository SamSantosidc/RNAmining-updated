# Pipeline commands

Activate an isolated Python 3.14.6 environment and install RNAmining before
running the pipeline commands. Development uses the project's pinned Conda
environment:

```bash
conda env create --file environment.yml
conda activate rnamining
```

After activating the environment, install the project:

```bash
python -m pip install -e .
```

Use `rnamining --help` or `rnamining <command> --help` to inspect the available
options.

## Complete dataset pipeline

The input ZIP must contain one CDS FASTA and one ncRNA FASTA for every organism
listed in `rnamining.data_preparation.SPECIES`. Gzip-compressed FASTA files are
supported.

Prepare the dataset:

```bash
rnamining prepare-data --input S5_File.zip --output data/
```

This validates the species pairs, balances each species, creates deterministic
80/20 training and test splits, and writes evaluation FASTAs and a statistics
report.

Train one model for every prepared species:

```bash
rnamining train \
  --data data/processed/train_test_split \
  --output models/coding_prediction/
```

## Single-species pipeline

The input ZIP must contain exactly two gzip-compressed FASTA files at its root:

```text
<species>.<assembly>.cds.all.fa.gz
<species>.<assembly>.ncrna.fa.gz
```

Both files must use the same species and assembly. The species must be listed
in `rnamining.data_preparation.SPECIES`.

Prepare one species:

```bash
rnamining prepare-species \
  --input Anolis_carolinensis.zip \
  --output data/
```

Train its model:

```bash
rnamining train-species \
  --data data/processed/train_test_split \
  --species Anolis_carolinensis \
  --output models/coding_prediction/
```

The model is written to
`models/coding_prediction/Anolis_carolinensis.pkl`. See
[Data preparation](data-preparation.md#approve-a-new-species) before approving
a species that is not already supported.

## Prediction

Run a prediction with the model for a trained species:

```bash
rnamining predict \
  --input sequences.fa \
  --organism Homo_sapiens \
  --output outputs/example/
```

Prediction produces `predictions.txt`, `codings.txt`, `noncodings.txt`, and
`edited_file.fasta` in the output directory.

For implementation and workflow details, see [Data preparation](data-preparation.md),
[Model training](model-training.md), and [Model evaluation](model-evaluation.md).
