# RNAmining

RNAmining predicts the coding potential of RNA FASTA sequences with trained
XGBoost models. It can be used from the command line or through the Dockerized
web application.

## Predict coding potential

After installing RNAmining, run inference by providing a FASTA file, the model
species, and an output directory:

```bash
rnamining predict \
  --input sequences.fa \
  --organism Homo_sapiens \
  --output outputs/prediction/
```

The selected organism must have a matching model under
`models/coding_prediction/`. The command creates:

```text
outputs/prediction/predictions.txt
outputs/prediction/codings.txt
outputs/prediction/noncodings.txt
outputs/prediction/edited_file.fasta
```

`predictions.txt` contains the predicted class and confidence for each input
sequence. The coding and non-coding FASTA outputs separate the input records by
their predicted class.

## Install the CLI

Development uses the pinned Python 3.14.6 Conda environment:

```bash
conda env create --file environment.yml
conda activate rnamining
python -m pip install -e .
```

If the environment already exists, activate it and reinstall the editable
package after updating the source:

```bash
conda activate rnamining
python -m pip install -e .
```

Inspect the available commands with:

```bash
rnamining --help
rnamining <command> --help
```

The CLI supports full-dataset preparation, single-species preparation,
training, single-species training, prediction, and model evaluation. See the
[complete CLI reference](docs/cli-reference.md) for every command and option.

## Run the web application

Docker provides the web server and all runtime dependencies:

```bash
cp .env.exemple .env
mkdir -p runtime/jobs
sudo chown -R 33:33 runtime
docker compose -f compose.local.yaml up --build -d
```

Open <http://localhost/>. To inspect or stop the application:

```bash
docker compose -f compose.local.yaml logs
docker compose -f compose.local.yaml down
```

## Documentation

- [Complete CLI reference](docs/cli-reference.md)
- [Pipeline workflows](docs/pipeline.md)
- [Data preparation](docs/data-preparation.md)
- [Model training](docs/model-training.md)
- [Model evaluation and metrics API](docs/model-evaluation.md)
- [Web application and Docker deployment](docs/web-application.md)
- [Architecture](docs/architecture.md)
- Evaluation reports: [July 18, 2026](docs/metrics_results_18_07_26.md) and
  [July 22, 2026](docs/metrics_results_22_07_26.md)
- [Modernization plan](docs/MODERNIZATION_PLAN.md)
- [Changelog](CHANGELOG.md)

Please cite the project using its [Zenodo record](https://zenodo.org/badge/latestdoi/359168403).
