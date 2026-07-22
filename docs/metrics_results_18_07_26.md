# RNAmining current metrics

**Report date:** July 19, 2026  
**Evaluation date:** July 16, 2026

## Evaluation summary

This document records the current evaluation baseline for the organism-specific RNAmining models. The evaluation covers 16 organisms and 163,466 test sequences. All 16 executions completed successfully, every prediction was matched to its ground-truth sequence ID, and no predictions were missing.

The detailed source data is generated as `outputs/evaluation/metrics_rnamining.csv`, while `outputs/evaluation/execucao_rnamining.csv` records execution status. These files are ignored by Git, so this document is the repository's durable snapshot of their results.

## Current dependencies

The recorded evaluation was produced in the following Python environment:

| Dependency | Version |
|---|---:|
| Python | 3.8.20 |
| NumPy | 1.24.4 |
| pandas | 2.0.3 |
| SciPy | 1.10.1 |
| scikit-learn | 1.3.2 |
| XGBoost | 2.0.3 |
| Biopython | 1.83 |
| python-dotenv | 1.0.1 |

The web deployment uses Docker Compose file format 3.4, PHP 7.2.2-FPM, Nginx, R, and Anaconda 2020.07. The Nginx image and the Conda-installed XGBoost and Biopython packages are not pinned to exact versions in the current Dockerfiles; therefore, rebuilding the container may resolve versions different from the evaluation environment above.

## Pipeline overview

RNAmining validates an input FASTA file and extracts normalized trinucleotide-frequency features from each sequence. It then loads the serialized XGBoost model for the selected organism, classifies each sequence as coding or non-coding, and writes the predicted class and probability to the result files.

For evaluation, the expected class is read from each test FASTA header (`cds` for coding and `ncrna` for non-coding). Predictions and expected classes are aligned by sequence ID before the confusion counts and classification metrics are calculated independently for each organism.

## Results

| Organism | Evaluated sequences | Accuracy | Precision | Recall | F1 | MCC |
|---|---:|---:|---:|---:|---:|---:|
| *Anolis carolinensis* | 1,904 | 0.9606 | 0.9452 | 0.9779 | 0.9613 | 0.9218 |
| *Chrysemys picta bellii* | 2,816 | 0.9773 | 0.9739 | 0.9808 | 0.9774 | 0.9546 |
| *Crocodylus porosus* | 1,848 | 0.9789 | 0.9763 | 0.9816 | 0.9790 | 0.9578 |
| *Danio rerio* | 3,246 | 0.9778 | 0.9686 | 0.9877 | 0.9780 | 0.9558 |
| *Eptatretus burgeri* | 436 | 0.9771 | 0.9643 | 0.9908 | 0.9774 | 0.9545 |
| *Gallus gallus* | 11,102 | 0.9932 | 0.9919 | 0.9946 | 0.9933 | 0.9865 |
| *Homo sapiens* | 81,500 | 0.9925 | 0.9896 | 0.9954 | 0.9925 | 0.9849 |
| *Latimeria chalumnae* | 1,168 | 0.9940 | 0.9983 | 0.9897 | 0.9940 | 0.9880 |
| *Monodelphis domestica* | 8,584 | 0.9886 | 0.9843 | 0.9930 | 0.9886 | 0.9772 |
| *Mus musculus* | 26,668 | 0.9904 | 0.9858 | 0.9951 | 0.9904 | 0.9808 |
| *Notechis scutatus* | 678 | 0.9646 | 0.9592 | 0.9705 | 0.9648 | 0.9293 |
| *Ornithorhynchus anatinus* | 3,900 | 0.9887 | 0.9912 | 0.9862 | 0.9887 | 0.9774 |
| *Petromyzon marinus* | 1,062 | 0.9896 | 0.9962 | 0.9831 | 0.9896 | 0.9794 |
| *Rattus norvegicus* | 17,380 | 0.9953 | 0.9932 | 0.9974 | 0.9953 | 0.9906 |
| *Sphenodon punctatus* | 364 | 0.9835 | 0.9889 | 0.9780 | 0.9834 | 0.9671 |
| *Xenopus tropicalis* | 810 | 0.9914 | 1.0000 | 0.9827 | 0.9913 | 0.9829 |
| **Overall (micro-aggregated)** | **163,466** | **0.9909** | **0.9879** | **0.9940** | **0.9909** | **0.9819** |

The overall row is calculated from the combined confusion counts of all organisms: 81,246 true positives, 80,735 true negatives, 998 false positives, and 487 false negatives. It is micro-aggregated, so organisms with larger test sets contribute proportionally more to the result.

Accuracy is the fraction of all correctly classified sequences. Precision measures how often a coding prediction is correct, while recall measures how many coding sequences are recovered. F1 is the harmonic mean of precision and recall. The Matthews correlation coefficient (MCC) summarizes all four confusion-matrix outcomes and remains informative for binary classification even when class sizes differ.
