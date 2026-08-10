# Model evaluation

Held-out inputs are stored under `data/evaluation/`. Run predictions into the ignored evaluation tree, for example:

```bash
rnamining predict --input data/evaluation/Homo_sapiens_test.fa \
  --organism Homo_sapiens --output outputs/evaluation/homo
```

The command preserves the historical `predictions.txt`, `codings.txt`, `noncodings.txt`, and `edited_file.fasta` formats. Ground truth remains in each evaluation FASTA header. Interactive evaluation is demonstrated by `notebooks/run_rnamining.ipynb` and generated metrics belong under `outputs/evaluation/`.

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

```bash
rnamining predict \
  --input outputs/evaluation/random_split_42/random_split_seed_42_test.fa \
  --organism random_split_seed_42 \
  --models models/random_split \
  --output outputs/evaluation/random_split_42/predictions
```
