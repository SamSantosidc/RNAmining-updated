# Model training

```bash
rnamining train --data data/processed/train_test_split --output models/coding_prediction/
```

Each organism pair is balanced and converted to the original 64 trinucleotide features. Counts use non-overlapping triplets in frame zero and the established effective A/C/T/G ordering, then divide each count by three times the number of valid triplets. Training uses `XGBClassifier()` with its established defaults and writes one pickle per organism.

The 16 current pickle files in `models/coding_prediction/` are versioned model artifacts. Retraining overwrites them only when explicitly requested.

