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

