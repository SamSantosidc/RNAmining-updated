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

The shared specification targets Python 3.14.6 and pins the scientific, test,
and notebook dependencies exactly. The default environment name declared in
`environment.yml` is `rnamining`:

```bash
conda env create --file environment.yml
conda activate rnamining
python -m pip install -e '.[test,notebooks]'
rnamining --help
```

Editable mode imports RNAmining directly from `src/`, so Python source changes
are available without reinstalling. Run the test suite with:

```bash
pytest
```

Start the interactive notebooks from the activated environment with `jupyter lab`. Update or remove the environment with:

```bash
conda env update --name rnamining --file environment.yml --prune
conda env remove --name rnamining
```

## Group ingestion

The established group workflow prepares the complete S5 dataset. The input ZIP
must contain one CDS FASTA and one ncRNA FASTA for every organism listed in
`rnamining.data_preparation.SPECIES`. Gzip-compressed FASTA members are
supported.

```bash
rnamining prepare-data --input S5_File.zip --output data/
```

Preparation validates that every approved species pair is present, balances
each species to its smaller class, creates deterministic 80/20 training and
test splits, and writes evaluation FASTAs and a statistics report. Train one
model for every prepared species with:

```bash
rnamining train --data data/processed/train_test_split --output models/coding_prediction/
```

## Single-species ingestion

The controlled single-species workflow accepts a ZIP containing exactly two
gzip-compressed FASTA files at the ZIP root, with no additional files:

```text
<species>.<assembly>.cds.all.fa.gz
<species>.<assembly>.ncrna.fa.gz
```

Both filenames must use the same species and assembly. The species must already
be approved in `rnamining.data_preparation.SPECIES`; adding a new entry requires
a reviewed repository change as described in the
[data preparation guide](docs/data-preparation.md#approve-a-new-species).

Prepare only that species:

```bash
rnamining prepare-species \
  --input Anolis_carolinensis.zip \
  --output data/
```

Then train only its model:

```bash
rnamining train-species \
  --data data/processed/train_test_split \
  --species Anolis_carolinensis \
  --output models/coding_prediction/
```

Both workflows use the same data layout and write models to
`models/coding_prediction/<species>.pkl`.

## Prediction

Run prediction with the model for an already trained species:

```bash
rnamining predict \
  --input sequences.fa \
  --organism Homo_sapiens \
  --output outputs/example/
```

See [architecture](docs/architecture.md), [data preparation](docs/data-preparation.md), [model training](docs/model-training.md), and [model evaluation](docs/model-evaluation.md) for details.

Please cite the project using its [Zenodo record](https://zenodo.org/badge/latestdoi/359168403).
