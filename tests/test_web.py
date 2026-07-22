import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_nginx_exposes_only_public_document_root():
    config = (ROOT / "docker/nginx/config/rnamining.conf").read_text()
    assert "root $droot" in config
    for compose in ("compose.local.yaml", "compose.proxy.yaml"):
        text = (ROOT / compose).read_text()
        nginx = text.split("php_rnamining:", 1)[0]
        assert "./web/public:" in nginx
        assert "./runtime" not in nginx
        assert "./models" not in nginx


def test_docker_and_local_workflows_share_conda_specification():
    environment = (ROOT / "environment.yml").read_text()
    dockerfile = (ROOT / "docker/php/Dockerfile").read_text()
    nginx_dockerfile = (ROOT / "docker/nginx/Dockerfile").read_text()
    assert "name: rnamining" in environment
    assert "python=3.14.6" in environment
    assert "libxgboost=3.3.0=cpu*" in environment
    assert "nodefaults" in environment
    assert "FROM php:8.5.8-fpm-trixie" in dockerfile
    assert "MINIFORGE_VERSION=26.3.2-2" in dockerfile
    assert "42260ffe3830fb953d5eee1bbb32229ff06aa7c3833c1ed7a9a0420a95685d94" in dockerfile
    assert "Miniforge3-${MINIFORGE_VERSION}-Linux-x86_64.sh" in dockerfile
    assert "sha256sum --check --strict" in dockerfile
    assert "COPY environment.yml" in dockerfile
    assert "conda env create" in dockerfile
    assert "envs/rnamining/bin" in dockerfile
    assert "FROM nginx:1.30.4-trixie" in nginx_dockerfile
    for compose in ("compose.local.yaml", "compose.proxy.yaml"):
        text = (ROOT / compose).read_text()
        assert not text.startswith("version:")
        assert "dockerfile: docker/php/Dockerfile" in text
        assert "/opt/conda/envs/rnamining/bin/python" in text


def test_root_docker_context_excludes_scientific_and_runtime_data():
    dockerignore = (ROOT / ".dockerignore").read_text().splitlines()
    assert dockerignore[0] == "*"
    assert "!environment.yml" in dockerignore
    assert "!docker/" in dockerignore
    assert "!docker/**" in dockerignore


def test_handlers_control_job_ids_files_and_rendering():
    upload = (ROOT / "web/public/api/upload.php").read_text()
    predict = (ROOT / "web/public/api/predict.php").read_text()
    download = (ROOT / "web/public/api/download.php").read_text()
    results = (ROOT / "web/public/results.php").read_text()
    config = (ROOT / "web/config.php").read_text()
    assert "runtime" in config and "jobs" in config
    assert "rnamining_job_id" in upload and "input/sequences.fasta" in upload
    assert "rnamining_job_id" in predict and "'/output'" in predict and "'/logs'" in predict
    assert "rnamining_job_id" in download and "basename" in download
    assert "RNAmining.zip" in download and "File not found" in download
    assert "htmlspecialchars" in results and "api/download.php" in results
    assert re.search(r"\^\[a-f0-9\]\{32\}\$", config)
