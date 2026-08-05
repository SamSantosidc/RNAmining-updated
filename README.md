# RNAmining

RNAmining predicts the coding potential of RNA FASTA sequences with trained
XGBoost models. Run it through the web application with Docker or from the
command line in an isolated Python environment.

## Run locally with Docker

```bash
cp .env.exemple .env
mkdir -p runtime/jobs
sudo chown -R 33:33 runtime
docker compose -f compose.local.yaml up --build -d
```

Open <http://localhost/>. To stop the application, run:

```bash
docker compose -f compose.local.yaml down
```

## Run locally from the CLI

RNAmining can run in any isolated environment with Python 3.14.6 and the
project dependencies installed. Development uses Conda and the pinned
`environment.yml` configuration:

```bash
conda env create --file environment.yml
conda activate rnamining
```

After activating your environment, install the project and check the CLI:

```bash
python -m pip install -e .
rnamining --help
```

For example, predict the coding potential of sequences in a FASTA file:

```bash
rnamining predict \
  --input sequences.fa \
  --organism Homo_sapiens \
  --output outputs/example/
```

## Documentation

- [Pipeline commands](docs/pipeline.md)
- [Web application and Docker deployment](docs/web-application.md)
- [Architecture](docs/architecture.md)
- [Data preparation](docs/data-preparation.md)
- [Model training](docs/model-training.md)
- [Model evaluation](docs/model-evaluation.md)
- Evaluation reports: [July 18, 2026](docs/metrics_results_18_07_26.md) and
  [July 22, 2026](docs/metrics_results_22_07_26.md)
- [Modernization plan](docs/MODERNIZATION_PLAN.md)
- [Changelog](CHANGELOG.md)

Please cite the project using its [Zenodo record](https://zenodo.org/badge/latestdoi/359168403).
