# Model evaluation

The reusable interface in `rnamining.evaluation` calculates binary metrics from
arrays or directly from any fitted model that provides `predict`. It does not
depend on experiment names, species, evolutionary groups, FASTA files, model
paths, or output layouts.

```python
from rnamining.evaluation import evaluate_model

metrics = evaluate_model(model, X_test, y_true)
```

The result contains Accuracy, Precision, Recall, F1, MCC, AUROC, AUPRC, and the
TN/FP/FN/TP confusion counts. `evaluate_model` uses `predict_proba` when
available, falls back to `decision_function`, and still calculates the basic
metrics when the model provides only hard predictions. Undefined AUROC/AUPRC
values are returned as `None` with an explanatory reason.

Experiment code owns its metadata and combines it with the returned values:

```python
from rnamining.evaluation import export_results

row = {
    "experiment": "current_models",
    "model_scope": "species_specific",
    "test_species": "Homo_sapiens",
    "seed": 42,
    **metrics,
}
export_results([row], "outputs/evaluation/metrics.csv")
```

Use `summarize_metrics(results)` to calculate the mean and sample standard
deviation of repeated result dictionaries.

## Evaluate the current species models

The repository contains 16 model files under `models/coding_prediction/`.
Their ignored held-out FASTAs must first be recreated from the same `S5_File.zip`
used to train the models:

```bash
rnamining prepare-data --input S5_File.zip --output data/
```

Evaluate all 16 models with the default model and test directories:

```bash
rnamining evaluate --output outputs/evaluation/current_models
```

Use `--models` and `--tests` only when those directories are elsewhere. The
command discovers the expected species, displays their metrics, and writes
`metrics_current_models.csv` and `metrics_current_models_summary.csv` under the
selected output directory.

The complete form is:

```bash
rnamining evaluate \
  --models models/coding_prediction \
  --tests data/evaluation \
  --output outputs/evaluation/current_models \
  --seed 42 \
  --repetition 1
```

`--seed` and `--repetition` record execution metadata; they do not change model
predictions. See the [CLI reference](cli-reference.md#evaluate) for all options.

### Distance-group codes

Distance-group filters use the following documented codes:

- `A`: Mammals
- `B`: Sauropsida
- `C`: Amphibians
- `D`: Fish
- `E`: Basal vertebrates

The complete species membership is defined in the data-preparation guide and
in the central `rnamining.metadata` catalog.

## Random Split baseline

The generalist baseline mixes the raw FASTAs from the 16 supported species and
performs a reproducible 80/20 split stratified by class. Each execution trains
one model for one seed and fits a new `StandardScaler` only on that execution's
training partition:

```bash
rnamining random-split \
  --data data \
  --models models/random_split \
  --output outputs/evaluation/random_split_42 \
  --seed 42
```

Run the command once per seed, using a separate evaluation directory (for
example `outputs/evaluation/random_split_123`). The model is saved under
`models/random_split/`, while that run's metrics and held-out FASTA are saved
under its evaluation directory. The workflow delegates metric calculation to
the shared `rnamining.evaluation` module.

## Leave-One-Species-Out

Run the complete 16-fold species generalization experiment with:

```bash
rnamining loso \
  --data data/ \
  --models models/loso/ \
  --seed 42
```

Then extract the metrics:

```bash
rnamining evaluate-loso \
  --data data/ \
  --models models/loso/ \
  --output outputs/evaluation/loso/ \
  --seed 42
```

The detailed per-species results are exported to
`outputs/evaluation/loso/metrics_loso.csv`, and the mean and sample standard
deviation are exported to `metrics_loso_summary.csv`. The test species is
excluded before preprocessing and model fitting in every fold.

```bash
rnamining predict \
  --input outputs/evaluation/random_split_42/random_split_seed_42_test.fa \
  --organism random_split_seed_42 \
  --models models/random_split \
  --output outputs/evaluation/random_split_42/predictions
```
