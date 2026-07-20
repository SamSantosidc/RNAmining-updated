# Web application

The document root is `web/public/`; runtime jobs are not public. The browser posts uploads to `api/upload.php`, then synchronously starts `api/predict.php`. Successful jobs redirect to `results.php?id=<execution-id>`. Result files are served by `api/download.php`, which accepts only a 32-character hexadecimal job ID and a fixed result filename.

Configure PHP with `RNAMINING_PROJECT_DIR`, `RNAMINING_RUNTIME_DIR`, and `RNAMINING_PYTHON`. Compose sets these to `/opt/rnamining`, `/opt/rnamining/runtime`, and the container's existing Python 3.8 interpreter. PHP needs write access to the runtime mount.

Public examples are under `/examples/`. The friendly application pages remain `/analysis`, `/about`, `/tutorial`, `/download`, and `/contact` through the existing Nginx rewrite behavior.

