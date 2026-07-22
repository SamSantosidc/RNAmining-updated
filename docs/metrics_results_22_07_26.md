# RNAmining current metrics

**Report date:** July 22, 2026  
**Evaluation date:** July 22, 2026

## Evaluation summary

This document records the current evaluation baseline for the organism-specific RNAmining models. The evaluation covers 16 organisms and 163,466 test sequences. All 16 executions completed successfully, every prediction was matched to its ground-truth sequence ID, and no predictions were missing.

The detailed source data is generated as `outputs/evaluation/metrics_rnamining.csv`. This file is ignored by Git, so this document is the repository's durable snapshot of its results.

## Current dependencies

The recorded evaluation was produced in the following Python environment:

| Dependency | Version |
|---|---:|
| Python | 3.14.6 |
| NumPy | 2.5.1 |
| pandas | 3.0.3 |
| SciPy | 1.18.0 |
| scikit-learn | 1.9.0 |
| XGBoost | 3.3.0 |
| Biopython | 1.87 |

The web deployment uses the current Compose Specification, PHP 8.5.8-FPM, Nginx 1.30.4, and Miniforge 26.3.2-2. The server images, Miniforge installer, and scientific dependencies are pinned to exact versions; the installer is also verified with its published SHA-256 checksum during the image build.

## Pipeline overview

RNAmining validates an input FASTA file and extracts normalized trinucleotide-frequency features from each sequence. It then loads the serialized XGBoost model for the selected organism, classifies each sequence as coding or non-coding, and writes the predicted class and probability to the result files.

For evaluation, the expected class is read from each test FASTA header (`cds` for coding and `ncrna` for non-coding). Predictions and expected classes are aligned by sequence ID before the confusion counts and classification metrics are calculated independently for each organism.

## Results

| Organism | Evaluated sequences | Accuracy | Precision | Recall | F1 | MCC |
|---|---:|---:|---:|---:|---:|---:|
| *Anolis carolinensis* | 1,904 | 0.9695 | 0.9515 | 0.9895 | 0.9701 | 0.9398 |
| *Chrysemys picta bellii* | 2,816 | 0.9748 | 0.9678 | 0.9822 | 0.9750 | 0.9497 |
| *Crocodylus porosus* | 1,848 | 0.9729 | 0.9669 | 0.9794 | 0.9731 | 0.9460 |
| *Danio rerio* | 3,246 | 0.9800 | 0.9715 | 0.9889 | 0.9802 | 0.9601 |
| *Eptatretus burgeri* | 436 | 0.9771 | 0.9643 | 0.9908 | 0.9774 | 0.9545 |
| *Gallus gallus* | 11,102 | 0.9939 | 0.9928 | 0.9950 | 0.9939 | 0.9878 |
| *Homo sapiens* | 81,500 | 0.9927 | 0.9896 | 0.9958 | 0.9927 | 0.9854 |
| *Latimeria chalumnae* | 1,168 | 0.9949 | 0.9966 | 0.9932 | 0.9949 | 0.9897 |
| *Monodelphis domestica* | 8,584 | 0.9887 | 0.9863 | 0.9911 | 0.9887 | 0.9774 |
| *Mus musculus* | 26,668 | 0.9888 | 0.9841 | 0.9937 | 0.9889 | 0.9777 |
| *Notechis scutatus* | 678 | 0.9631 | 0.9618 | 0.9646 | 0.9632 | 0.9263 |
| *Ornithorhynchus anatinus* | 3,900 | 0.9931 | 0.9928 | 0.9933 | 0.9931 | 0.9862 |
| *Petromyzon marinus* | 1,062 | 0.9896 | 0.9981 | 0.9812 | 0.9896 | 0.9794 |
| *Rattus norvegicus* | 17,380 | 0.9953 | 0.9931 | 0.9976 | 0.9953 | 0.9907 |
| *Sphenodon punctatus* | 364 | 0.9835 | 0.9835 | 0.9835 | 0.9835 | 0.9670 |
| *Xenopus tropicalis* | 810 | 0.9864 | 0.9925 | 0.9802 | 0.9863 | 0.9729 |
| **Overall (micro-aggregated)** | **163,466** | **0.9909** | **0.9877** | **0.9943** | **0.9910** | **0.9819** |

The overall row is calculated from the combined confusion counts of all organisms: 81,267 true positives, 80,718 true negatives, 1,015 false positives, and 466 false negatives.

In simple terms, micro-aggregation treats the 16 test sets as if all 163,466 sequences were placed in one large test set, and then calculates the metrics once from that combined set. It is not the average of the 16 rows. An organism with more test sequences therefore has more influence on the overall result than an organism with fewer sequences. For example, the 81,500 *Homo sapiens* sequences influence the overall row much more than the 364 *Sphenodon punctatus* sequences.

Accuracy is the fraction of all correctly classified sequences. Precision measures how often a coding prediction is correct, while recall measures how many coding sequences are recovered. F1 is the harmonic mean of precision and recall. The Matthews correlation coefficient (MCC) summarizes all four confusion-matrix outcomes and remains informative for binary classification even when class sizes differ.
