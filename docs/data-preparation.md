# Data preparation

`S5_File.zip` is a local, ignored input. It must contain CDS and ncRNA FASTA files for all 16 organisms listed by `rnamining.data_preparation.SPECIES`; gzip members inside the ZIP are supported.

```bash
rnamining prepare-data --input S5_File.zip --output data/
```

The command extracts canonical organism FASTAs to `data/raw/`, writes descriptive statistics to `data/reports/organism_sequences_stats.csv`, balances each organism to its smaller class, and performs an 80/20 class-wise split with seed 42. Training/test files go to `data/processed/train_test_split/{coding,noncoding}`. Mixed held-out FASTAs go to `data/evaluation/`, with `class:coding` or `class:noncoding` appended to every header as ground truth.

## Prepare one species

To add one species without changing the established S5 workflow, provide a ZIP
whose root contains exactly one compressed coding FASTA and one compressed
ncRNA FASTA with the same species and assembly:

```text
Anolis_carolinensis.AnoCar2.0v2.cds.all.fa.gz
Anolis_carolinensis.AnoCar2.0v2.ncrna.fa.gz
```

```bash
rnamining prepare-species --input Anolis_carolinensis.zip --output data/
```

For governance and safety, the command accepts only species explicitly listed
in `rnamining.data_preparation.SPECIES`. It writes the same raw, split,
evaluation, and report formats and preserves other species already prepared
under the output directory. Preparing the same species again replaces that
species' artifacts. The species is inferred from the filenames, while the
assembly may contain dots. Both FASTA members must be at the ZIP root, and the
ZIP must not contain additional files.

The generated training inputs retain the established names:

```text
data/processed/train_test_split/coding/Anolis_carolinensis_coding_train.fa
data/processed/train_test_split/noncoding/Anolis_carolinensis_noncoding_train.fa
```

## Approve a new species

Adding a species is a controlled repository change, not an end-user operation.
Before running `prepare-species` or `train-species` for a new species:

1. Add its canonical underscore-separated identifier to `SPECIES` in
   `src/rnamining/data_preparation.py`.
2. Add the same identifier and display name to the organism selector in
   `web/public/analysis.php`.
3. Update the relevant documentation and tests, and submit the change for code
   review.
4. Prepare and validate the dataset, then train and evaluate the new model
   before deploying its `.pkl` artifact.

Both single-species commands reject identifiers absent from `SPECIES`. Access
to the prepared data and model directories must also remain restricted to
authorized operators; the allowlist does not replace filesystem permissions.
