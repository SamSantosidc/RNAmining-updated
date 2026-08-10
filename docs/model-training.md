# Model training

```bash
rnamining train --data data/processed/train_test_split --output models/coding_prediction/
```

Each organism pair is balanced and converted to the original 64 trinucleotide features. Counts use non-overlapping triplets in frame zero and the established effective A/C/T/G ordering, then divide each count by three times the number of valid triplets. Training uses `XGBClassifier()` with its established defaults and writes one pickle per organism.

The 16 current pickle files in `models/coding_prediction/` are versioned model artifacts. Retraining overwrites them only when explicitly requested.

## Train the generalist model

The generalist workflow trains one model from the combined raw FASTA files of
the supported species. It performs an 80/20 class-stratified split and must be
run once per seed:

```bash
rnamining random-split \
  --data data/ \
  --models models/random_split/ \
  --output outputs/evaluation/random_split_42/ \
  --seed 42
```

This produces `models/random_split/random_split_seed_42.pkl`. Its scaler is
stored with the model artifact. Metrics and the held-out test FASTA are stored
under `outputs/evaluation/random_split_42/`; metric calculation is provided by
the shared `rnamining.evaluation` module.

## Train one species

To train only one prepared species, select it explicitly:

```bash
rnamining train-species \
  --data data/processed/train_test_split \
  --species Anolis_carolinensis \
  --output models/coding_prediction/
```

This command requires both matching training FASTAs and writes only
`Anolis_carolinensis.pkl`; other prepared species are not trained. The value
passed to `--species` must already be approved in
`rnamining.data_preparation.SPECIES`; see the controlled addition procedure in
the [data preparation guide](data-preparation.md#approve-a-new-species).
