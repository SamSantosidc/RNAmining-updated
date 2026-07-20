# RNAmining

RNAmining predicts coding potential from RNA FASTA sequences using 16 established XGBoost models. This repository keeps the website, implementation, models, scientific data, and generated state separate without changing the model representation or output format.

## Install and run

Python 3.8 or newer is required. Install the package in editable mode:

```bash
pip install -e .
```

Prepare the local S5 archive, train models, or predict sequences:

```bash
rnamining prepare-data --input S5_File.zip --output data/
rnamining train --data data/processed/train_test_split --output models/coding_prediction/
rnamining predict --input sequences.fa --organism Homo_sapiens --output outputs/example/
```

Start the direct local deployment with `docker compose -f compose.local.yaml up --build`; use `compose.proxy.yaml` when attaching to the existing external proxy network.

See [architecture](docs/architecture.md), [data preparation](docs/data-preparation.md), [model training](docs/model-training.md), [model evaluation](docs/model-evaluation.md), and the [web application](docs/web-application.md) for details.

Please cite the project using its [Zenodo record](https://zenodo.org/badge/latestdoi/359168403).
