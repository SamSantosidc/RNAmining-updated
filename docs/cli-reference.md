# CLI reference

Install the project in the active environment before using the CLI:

```bash
python -m pip install -e .
```

Use `rnamining --help` to list commands and
`rnamining <command> --help` to inspect a command. All paths are interpreted
relative to the current working directory unless an absolute path is supplied.

## `predict`

Predict the coding potential of sequences in a FASTA file:

```bash
rnamining predict \
  --input sequences.fa \
  --organism Homo_sapiens \
  --output outputs/prediction/
```

| Option | Required | Description |
|---|---:|---|
| `--input` | Yes | Input FASTA file. |
| `--organism` | Yes | Species identifier used to select `<organism>.pkl`. |
| `--output` | Yes | Directory for prediction files. |

Models are read from `models/coding_prediction/`. The output directory receives
`predictions.txt`, `codings.txt`, `noncodings.txt`, and `edited_file.fasta`.

## `evaluate`

Evaluate the 16 current species-specific models against their held-out FASTAs:

```bash
rnamining evaluate --output outputs/evaluation/current_models
```

| Option | Required | Default | Description |
|---|---:|---|---|
| `--models` | No | `models/coding_prediction` | Directory containing one `<species>.pkl` per supported species. |
| `--tests` | No | `data/evaluation` | Directory containing one `<species>_test.fa` per supported species. |
| `--output` | Yes | — | Directory for the metrics CSV files. |
| `--seed` | No | `42` | Seed recorded as execution metadata; evaluation itself is deterministic. |
| `--repetition` | No | `1` | Repetition number recorded as execution metadata. |

The command requires a model and test FASTA for every species in
`rnamining.data_preparation.SPECIES`. It displays the metrics and writes:

```text
metrics_current_models.csv
metrics_current_models_summary.csv
```

The detailed CSV contains Accuracy, Precision, Recall, F1, MCC, AUROC, AUPRC,
TN, FP, FN, TP, score type, test counts, species, seed, and repetition. The
summary contains the mean and sample standard deviation across models.

## `prepare-data`

Prepare the complete 16-species S5 dataset:

```bash
rnamining prepare-data \
  --input S5_File.zip \
  --output data/
```

| Option | Required | Description |
|---|---:|---|
| `--input` | Yes | ZIP containing the expected CDS and ncRNA species pairs. |
| `--output` | Yes | Root directory for raw, processed, evaluation, and report files. |

The command validates the species pairs, balances both classes, performs the
deterministic 80/20 split, and creates `raw/`, `processed/train_test_split/`,
`evaluation/`, and `reports/organism_sequences_stats.csv` below the output.

## `prepare-species`

Prepare one approved species without rebuilding the complete dataset:

```bash
rnamining prepare-species \
  --input Anolis_carolinensis.zip \
  --output data/
```

| Option | Required | Description |
|---|---:|---|
| `--input` | Yes | ZIP containing exactly one compressed CDS FASTA and one compressed ncRNA FASTA. |
| `--output` | Yes | Existing or new dataset root. |

The archive members must be at the ZIP root and use these names:

```text
<species>.<assembly>.cds.all.fa.gz
<species>.<assembly>.ncrna.fa.gz
```

The species must already be present in `rnamining.data_preparation.SPECIES`.

## `train`

Train a model for every coding/non-coding training pair:

```bash
rnamining train \
  --data data/processed/train_test_split \
  --output models/coding_prediction/
```

| Option | Required | Description |
|---|---:|---|
| `--data` | Yes | Directory containing the prepared `coding/` and `noncoding/` subdirectories. |
| `--output` | Yes | Directory where `<species>.pkl` models are written. |

Existing model files with matching names are overwritten.

## `train-species`

Train only one approved species:

```bash
rnamining train-species \
  --data data/processed/train_test_split \
  --species Anolis_carolinensis \
  --output models/coding_prediction/
```

| Option | Required | Description |
|---|---:|---|
| `--data` | Yes | Directory containing the prepared `coding/` and `noncoding/` subdirectories. |
| `--species` | Yes | Approved underscore-separated species identifier. |
| `--output` | Yes | Directory where the species model is written. |

Only `<output>/<species>.pkl` is created or replaced.

## Complete workflows

Inference with an existing model requires only `predict`. To recreate, train,
and evaluate all current species models:

```bash
rnamining prepare-data --input S5_File.zip --output data/
rnamining train \
  --data data/processed/train_test_split \
  --output models/coding_prediction/
rnamining evaluate --output outputs/evaluation/current_models
```

To add or replace one approved species model:

```bash
rnamining prepare-species --input Anolis_carolinensis.zip --output data/
rnamining train-species \
  --data data/processed/train_test_split \
  --species Anolis_carolinensis \
  --output models/coding_prediction/
```
