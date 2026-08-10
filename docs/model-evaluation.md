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

Legacy prediction files remain available through `rnamining predict` and are
unchanged by the metrics module.
