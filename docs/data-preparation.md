# Data preparation

`S5_File.zip` is a local, ignored input. It must contain CDS and ncRNA FASTA files for all 16 organisms listed by `rnamining.data_preparation.SPECIES`; gzip members inside the ZIP are supported.

```bash
rnamining prepare-data --input S5_File.zip --output data/
```

The command extracts canonical organism FASTAs to `data/raw/`, writes descriptive statistics to `data/reports/organism_sequences_stats.csv`, balances each organism to its smaller class, and performs an 80/20 class-wise split with seed 42. Training/test files go to `data/processed/train_test_split/{coding,noncoding}`. Mixed held-out FASTAs go to `data/evaluation/`, with `class:coding` or `class:noncoding` appended to every header as ground truth.

