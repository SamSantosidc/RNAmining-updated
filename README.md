# RNAmining

RNAmining predicts the coding potential of RNA FASTA sequences with trained
XGBoost models. It can be used from the command line or through the Dockerized
web application.

## Predict coding potential

After installing RNAmining, run inference by providing a FASTA file, the model
species, and an output directory:

```bash
rnamining \
  -f sequences.fa \
  -organism_name Homo_sapiens \
  -prediction_type coding_prediction \
  -output_folder outputs/prediction/
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

## Run the CLI with Docker

Build the standalone CLI image from the repository root:

```bash
docker build -f docker/cli/Dockerfile -t rnamining:1.1.0 .
```

The image has the Python environment, RNAmining package, and versioned models
inside it. The executable is available on `PATH`, and the image can be used
without an entrypoint override, so a prediction can be run with:

```bash
docker run --rm \
  -v "$PWD:/work" \
  rnamining:1.1.0 \
  rnamining \
  -f /work/sequences.fa \
  -organism_name Homo_sapiens \
  -prediction_type coding_prediction \
  -output_folder /work/outputs/prediction
```

For a local-like experience, use the repository wrapper. It preserves the
same `rnamining` arguments, mounts the current directory as `/work`, uses the
current user's UID/GID, and keeps relative paths working:

```bash
chmod +x bin/rnamining
bin/rnamining predict \
  --input tests/fixtures/anolis_regression.fa \
  --organism Anolis_carolinensis \
  --output outputs/docker-prediction
```

The image tag can be changed without editing the wrapper:

```bash
RNAMINING_DOCKER_IMAGE=rnamining:1.1.0 bin/rnamining --help
```

Preparation, training, and evaluation use the same image. See the
[CLI Docker guide](docs/cli-docker.md) for mounts and the project wrapper.

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

- [Arquitetura](docs/architecture.md)
- [Pipeline do modelo](docs/pipeline.md)
- [CLI](docs/cli-reference.md)
- [CLI Docker](docs/cli-docker.md)
- [Aplicação web](docs/web-application.md)
- Evaluation reports: [July 18, 2026](docs/metrics_results_18_07_26.md) and
  [July 22, 2026](docs/metrics_results_22_07_26.md)

Please cite the project using its [Zenodo record](https://zenodo.org/badge/latestdoi/359168403).
