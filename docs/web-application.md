# Web application

The document root is `web/public/`; runtime jobs are not public. The browser posts uploads to `api/upload.php`, then synchronously starts `api/predict.php`. Successful jobs redirect to `results.php?id=<execution-id>`. Result files are served by `api/download.php`, which accepts only a 32-character hexadecimal job ID and a fixed result filename.

## Local Docker deployment

Docker supplies PHP, Nginx, Conda, Python, and all scientific dependencies; no host Conda environment is required. Create the local configuration and writable job directory, then build and start the application:

```bash
cp .env.exemple .env
mkdir -p runtime/jobs
sudo chown -R 33:33 runtime
docker compose -f compose.local.yaml config
docker compose -f compose.local.yaml up --build -d
docker compose -f compose.local.yaml ps
```

Open <http://localhost/>, upload a FASTA on `/analysis`, select an organism, and confirm that results and all three downloads are available. Logs are available through `docker compose -f compose.local.yaml logs`; stop the deployment with `docker compose -f compose.local.yaml down`.

After installing the test extra in the local Conda environment, the same end-to-end workflow can be checked automatically against the running containers:

```bash
RNAMINING_WEB_URL=http://localhost pytest tests/test_web_live.py -v
```

Configure PHP with `RNAMINING_PROJECT_DIR`, `RNAMINING_RUNTIME_DIR`, and `RNAMINING_PYTHON`. Compose sets these to `/opt/rnamining`, `/opt/rnamining/runtime`, and `/opt/conda/envs/rnamining/bin/python`. The PHP image uses PHP 8.5.8-FPM and checksum-verified Miniforge 26.3.2-2; the Python environment is built from the repository's shared `environment.yml`. Nginx uses the pinned stable 1.30.4 image. The pinned Miniforge installer preserves the existing Linux x86-64 runtime scope. PHP-FPM uses UID/GID 33, so the ownership command above is required for writable job storage on Linux bind mounts.

If WSL reports that `docker` is unavailable, enable Docker Desktop integration for the active WSL distribution and rerun `docker compose version` before building.

## Proxy deployment

`compose.proxy.yaml` does not publish port 80 directly. It expects an existing external Docker network named `gatewayapps_proxy`:

```bash
docker network inspect gatewayapps_proxy
docker compose -f compose.proxy.yaml config
docker compose -f compose.proxy.yaml up --build -d
```

The external reverse proxy must route requests to `rnamining_webserver` on port 80.

Public examples are under `/examples/`. The friendly application pages remain `/analysis`, `/about`, `/tutorial`, `/download`, and `/contact` through the existing Nginx rewrite behavior.
