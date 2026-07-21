# RNAmining

RNAmining predicts coding potential from RNA FASTA sequences using 16 established XGBoost models. The web application runs with Docker, while the CLI, notebooks, and development tools can run locally in a Conda environment.

## Web application with Docker

Docker users do not need Python or Conda installed on the host. Copy the environment configuration and start the local deployment:

```bash
cp .env.exemple .env
mkdir -p runtime/jobs
sudo chown -R 33:33 runtime
docker compose -f compose.local.yaml up --build -d
```

Open <http://localhost/> and use the **Run** page to upload a FASTA file. Stop the application with:

```bash
docker compose -f compose.local.yaml down
```

UID/GID 33 is the `www-data` account used by PHP-FPM. The ownership command allows uploaded jobs and result files to be written to the bind-mounted `runtime/` directory.

`compose.proxy.yaml` provides the existing deployment mode for hosts that already have the external `gatewayapps_proxy` Docker network. See the [web application guide](docs/web-application.md) for configuration, verification, and troubleshooting.

## Local CLI and notebooks with Conda

Conda creates the isolated environment; pip then installs the local RNAmining package and its `rnamining` command into that active environment:

```bash
conda env create -f environment.yml
conda activate rnamining
python -m pip install -e .
rnamining --help
```

Editable mode imports RNAmining directly from `src/`, so Python source changes are available without reinstalling. For tests, install the optional test dependency and run the suite:

```bash
python -m pip install -e '.[test]'
pytest
```

Start the interactive notebooks from the activated environment with `jupyter lab`. Update or remove the environment with:

```bash
conda env update --file environment.yml --prune
conda env remove --name rnamining
```

## CLI workflows

```bash
rnamining prepare-data --input S5_File.zip --output data/
rnamining train --data data/processed/train_test_split --output models/coding_prediction/
rnamining predict --input sequences.fa --organism Homo_sapiens --output outputs/example/
```

See [architecture](docs/architecture.md), [data preparation](docs/data-preparation.md), [model training](docs/model-training.md), and [model evaluation](docs/model-evaluation.md) for details.

Please cite the project using its [Zenodo record](https://zenodo.org/badge/latestdoi/359168403).
