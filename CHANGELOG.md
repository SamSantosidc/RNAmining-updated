# Changelog

## Standardize experiment evaluation metrics and exports

### Why this changed

Metric calculation previously existed only in the historical evaluation
notebook and generated reports. That implementation calculated Accuracy,
Precision, Recall, F1, MCC, and confusion counts, but it was not a reusable
package interface. A shared numerical function is needed so the current 16
species-specific models and future experiments use the same definitions without
requiring a particular experiment structure.

### Code changes

- `src/rnamining/evaluation.py` adds `calculate_metrics`, which accepts only
  ground-truth labels, predicted labels, and optional scores. It calculates
  Accuracy, Precision, Recall, F1, MCC, AUROC, AUPRC, and TN/FP/FN/TP without
  knowing species, groups, paths, manifests, or model scope.
- `evaluate_model` is a small convenience wrapper for fitted binary models. It
  uses `predict_proba` when available, falls back to `decision_function`, and
  still returns the basic metrics when only `predict` exists. AUROC/AUPRC remain
  `None` with an explanatory reason when scores or both ground-truth classes are
  unavailable.
- `summarize_metrics` calculates the mean, sample standard deviation, and number
  of available values. `export_results` writes result dictionaries to CSV and
  preserves any metadata added by the calling experiment.
- `src/rnamining/cli.py` adds a thin `rnamining evaluate` command that discovers
  the 16 current model/test pairs and calls the same reusable functions. It does
  not introduce manifests or constrain future experiment metadata.
- `src/rnamining/__init__.py` exposes these four functions as the public metrics
  interface. No experiment names or allowed scopes are enforced by the package.

### Documentation and verification

- `README.md` now presents inference as the primary user workflow and links to
  the complete command reference.
- `docs/cli-reference.md` documents every user-facing command, argument,
  default, generated file, and complete workflow in one place.
- `docs/model-evaluation.md` documents direct use of the functions and includes
  the simple CLI command that evaluates all 16 current species-specific models.
- `tests/test_evaluation.py` verifies metric values, confusion counts, model
  score fallbacks, unavailable ranking metrics, edge cases, summaries, and CSV
  export.

The existing `rnamining predict` flow and its `predictions.txt`, `codings.txt`,
`noncodings.txt`, and `edited_file.fasta` outputs were intentionally left
unchanged to preserve compatibility with the web application and historical
workflows.

## Add single-species preparation and training commands

RNAmining can now prepare and train one species without changing the established
16-species S5 workflow. `rnamining prepare-species` accepts a ZIP containing one
matching `<species>.<assembly>.cds.all.fa.gz` and
`<species>.<assembly>.ncrna.fa.gz` pair, then writes the existing raw, split,
evaluation, and statistics formats.

`rnamining train-species` trains only the explicitly selected species from the
prepared training split and writes its existing `<species>.pkl` model format.
Both commands require the species to be approved in
`rnamining.data_preparation.SPECIES`. The original `prepare-data` and `train`
commands remain available unchanged.

## Fix ambiguous nucleotides in trinucleotide feature extraction

The trinucleotide counter could fail with `local variable 'first' referenced before assignment` when a triplet contained an unsupported nucleotide such as `N`. If the variable had been assigned while processing an earlier triplet, its stale value could instead be reused and produce an incorrect count.

The counter now validates all three bases before converting them to array indices. Triplets composed entirely of `A`, `C`, `G`, or `T` continue to be counted normally, while triplets containing ambiguous or unsupported nucleotides are skipped.
