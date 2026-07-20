# Model evaluation

Held-out inputs are stored under `data/evaluation/`. Run predictions into the ignored evaluation tree, for example:

```bash
rnamining predict --input data/evaluation/Homo_sapiens_test.fa \
  --organism Homo_sapiens --output outputs/evaluation/homo
```

The command preserves the historical `predictions.txt`, `codings.txt`, `noncodings.txt`, and `edited_file.fasta` formats. Ground truth remains in each evaluation FASTA header. Interactive evaluation is demonstrated by `notebooks/run_rnamining.ipynb` and generated metrics belong under `outputs/evaluation/`.

