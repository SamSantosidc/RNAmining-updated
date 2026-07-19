# RNAmining Modernization Plan

## Summary

The modernization will separate the application into two responsibility-focused images:

1. A Python image responsible for FASTA processing, feature extraction, model loading, and inference.
2. A PHP image responsible for the web interface, uploads, result presentation, and communication with the Python service.

The existing Nginx image remains a separate infrastructure image and continues to act as the public reverse proxy. The Python service will be private to the Docker network.

Model compatibility remains the first priority. The existing predictions must be captured, the pickle models must be converted and verified, and only then may Python, XGBoost, or the other runtime dependencies be upgraded.

## Target architecture

```text
Browser
   │
   ▼
Nginx 1.30.4
   │ FastCGI
   ▼
PHP 8.5.8-FPM image
   │ private synchronous HTTP
   ▼
Python 3.14.6 inference image
   │
   ├── FASTA validation
   ├── 64-feature extraction
   ├── UBJSON model loading
   └── XGBoost prediction
```

### Python model image

The Python image will own:

- FASTA parsing and validation.
- Exact reproduction of the current 64 normalized trinucleotide features.
- Loading and validating the 16 converted XGBoost models.
- Model caching and organism allowlisting.
- Prediction and probability calculation.
- A synchronous, private JSON API.
- Health and readiness checks.

It will not contain PHP, Nginx, R, Anaconda, training notebooks, training datasets, model-training code, or unnecessary scientific libraries.

### PHP web image

The PHP image will own:

- PHP-FPM and the current web interface.
- Upload validation and request identifiers.
- Sending uploaded FASTA data to the Python service.
- Handling service errors and presenting results.
- Temporarily generating the current downloadable result files from authoritative JSON where the existing interface still requires them.

It will no longer invoke Python with `shell_exec()` or contain XGBoost and scientific dependencies.

### Nginx image

Nginx remains a third infrastructure image instead of being combined with PHP. It will expose the public port and forward PHP requests to PHP-FPM. The Python inference service must not be published to the host or public network.

## Dependency targets

Versions must be locked with hashes, and container base images must be pinned by digest. The versions below were the latest stable, non-yanked releases identified on July 19, 2026.

### Final Python production image

| Dependency | Current | Target | Purpose |
|---|---:|---:|---|
| Python | 3.8.20 | [3.14.6](https://www.python.org/downloads/release/python-3146/) | Runtime |
| XGBoost | 2.0.3 | [`xgboost-cpu` 3.3.0](https://pypi.org/project/xgboost-cpu/3.3.0/) | CPU-only model inference |
| NumPy | 1.24.4 | [2.5.1](https://pypi.org/project/numpy/) | Feature matrices |
| SciPy | 1.10.1 | [1.18.0](https://pypi.org/project/scipy/) | Runtime dependency of XGBoost |
| Biopython | 1.83 | [1.87](https://pypi.org/project/biopython/) | FASTA parsing |
| FastAPI | Not present | [0.139.2](https://pypi.org/project/fastapi/) | Synchronous HTTP API |
| Uvicorn | Not present | [0.51.0](https://pypi.org/project/uvicorn/) | ASGI server |
| python-multipart | Not present | [0.0.32](https://pypi.org/project/python-multipart/) | Streaming FASTA uploads |
| Pydantic | Not present | [2.13.4](https://pypi.org/project/pydantic/) | Request and response schemas |

Use `xgboost-cpu` because inference does not require GPU or federated functionality and its Linux wheel is substantially smaller than the full XGBoost distribution.

Pandas, scikit-learn, and direct ARFF processing must not be included in the final image. They may remain in migration and test environments until feature and prediction equivalence is demonstrated. SciPy remains because XGBoost 3.3.0 declares it as a runtime dependency.

### Migration-only scientific dependencies

| Dependency | Migration target | Disposition |
|---|---:|---|
| pandas | [3.0.3](https://pypi.org/project/pandas/) | Use only for comparison with the legacy pipeline; exclude from the final inference image. Version 3.0.4 is yanked. |
| scikit-learn | [1.9.0](https://pypi.org/project/scikit-learn/) | Keep in the training and test dependency group only. |
| SciPy ARFF API | 1.18.0 | Use temporarily for legacy comparison, then stop importing `scipy.io.arff`. |

### Web infrastructure

| Component | Current | Target |
|---|---:|---:|
| PHP-FPM | 7.2.2 | [8.5.8](https://www.php.net/) |
| Nginx | Unpinned | [1.30.4 stable](https://nginx.org/en/download.html) |
| Docker Compose | File format 3.4 | Current Compose Specification |

Before implementation begins, verify that each target still resolves to the same stable release. If a newer stable patch exists, update this table and the lockfile in the dependency pull request. Do not select preview, release-candidate, alpha, or yanked releases.

## Changes required for the model image

### 1. Preserve the existing model baseline

- Reconstruct the recorded Python 3.8.20 and XGBoost 2.0.3 environment.
- Capture per-sequence features, labels, and unrounded probabilities for all 16 organisms.
- Record model hashes, dependency versions, and the existing aggregate metrics.
- Do not begin the new production image until this baseline is reproducible.

This must happen first because the current Dockerfile does not pin the packages installed from Conda. Without a reproducible baseline, dependency, serialization, and feature-extraction changes cannot be distinguished from one another.

### 2. Convert the model artifacts

- Load each trusted `.pkl` under XGBoost 2.0.3.
- Extract the native booster and save it as UBJSON.
- Create a manifest containing model ID, organism, source and target hashes, feature count and order, objective, class labels, decision threshold, and conversion version.
- Require identical labels and probability differences no greater than `1e-7` before accepting a converted artifact.
- Keep the pickle files available as rollback artifacts until the new image is validated.

Conversion must occur before upgrading XGBoost. Pickle captures Python object internals and is not a stable interchange format, while the native XGBoost model format is intended for cross-version model loading.

### 3. Create a standalone inference package

- Place production code under `services/inference/`.
- Separate configuration, FASTA parsing, feature extraction, model registry, inference, API schemas, and API routes.
- Keep training and notebook code outside the production package.
- Replace the current import-time call to `main()` with explicit API and CLI entrypoints.
- Make the CLI a thin adapter over the same inference core used by the API.

The inference core must accept parsed sequence records and an allowlisted organism ID, then return a structured prediction batch. It must not know about PHP directories or generate web-specific files.

### 4. Replace ARFF-based feature extraction

- Parse FASTA records with Biopython.
- Produce the 64-element NumPy matrix directly, without temporary `.arff` or edited FASTA files.
- Preserve the current trinucleotide ordering, reading-frame stepping, ambiguous-base behavior, and normalization until equivalence is proven.
- Reject records that cannot produce a valid normalized vector with a stable validation error instead of allowing `NaN` or division-by-zero behavior.

The legacy and direct extractors must initially run against the same fixtures. Direct extraction may replace ARFF only after the matrices match exactly.

### 5. Load models through a registry

- Read the model manifest during service startup.
- Validate every UBJSON checksum and the expected 64-feature schema.
- Load immutable boosters once and cache them by allowlisted organism ID.
- Fail readiness if any required model is absent, corrupt, or incompatible.
- Never construct an unrestricted filesystem path from an organism supplied by the client.
- Configure an explicit XGBoost thread limit to avoid consuming every host CPU.

### 6. Expose a synchronous API

The initial interface will be:

- `POST /v1/predictions`: multipart FASTA plus `organism` and `prediction_type=coding_prediction`.
- `GET /v1/models`: supported model IDs and versions.
- `GET /healthz`: confirms that the process is alive.
- `GET /readyz`: confirms that the manifest and every required model are loaded.

A successful prediction response will contain:

- `schema_version`
- `request_id`
- `model_id`
- `organism`
- Ordered predictions containing `sequence_id`, `label`, `coding_probability`, and `predicted_probability`

Errors will use stable HTTP status codes and contain `code`, `message`, and `request_id`, without internal paths or stack traces. Structured JSON is the authoritative integration contract.

### 7. Create the Python Docker image

- Base it on `python:3.14.6-slim`, pinned by digest.
- Install the locked CPU-only production dependencies with hashes.
- Copy only the inference package, dependency lockfile, manifest, and UBJSON models.
- Run as a non-root user with a read-only root filesystem and an explicit writable temporary directory.
- Start Uvicorn without development reload.
- Add a readiness health check and explicit worker, request-size, memory, and thread limits.
- Expose the API port only to the private Compose network.
- Build and test the image without access to the legacy pickle files to prove that they are no longer a runtime dependency.

### 8. Update Docker Compose and PHP integration

- Add an `inference_rnamining` service built from the Python image.
- Make PHP depend on Python readiness and configure the internal service URL through an environment variable.
- Replace `executionR.php` process creation, `ps`, log polling, and direct Python invocation with an HTTP request.
- Stream the uploaded FASTA instead of sharing application source directories.
- Validate organism values in PHP and again in Python.
- Retain the current downloadable files as a PHP adapter over JSON until the web interface no longer requires them.
- Keep the existing Nginx-to-PHP routing while pinning the Nginx image.

### 9. Reduce and update the PHP image

- Upgrade to `php:8.5.8-fpm`, pinned by digest.
- Keep only extensions required for uploads, HTTP communication, and ZIP generation.
- Remove Anaconda, Python, XGBoost, Biopython, R, `procps`, and Python process-management utilities.
- Resolve PHP 8.5 compatibility problems separately from prediction changes.
- Rerun upload, API, results-page, and download integration tests.

PHP is updated after the model image is stable so PHP runtime failures cannot be confused with model, feature, or XGBoost changes.

## Validation and rollout

- Feature matrices from legacy ARFF processing and direct NumPy extraction must match exactly.
- Converted UBJSON and pickle models must produce identical labels with probability drift at or below `1e-7`.
- XGBoost 3.3.0 under Python 3.14.6 must preserve every baseline label; probability drift must remain at or below `1e-6`.
- API, CLI, and legacy `develop` runs must return the same ordered sequence IDs and predictions.
- Container tests must cover all 16 models, malformed FASTA, ambiguous and short sequences, unsupported organisms, upload limits, service unavailability, concurrent requests, and restart readiness.
- The final model image must be inspected to confirm that it excludes pandas, scikit-learn, Anaconda, training data, notebooks, and pickle artifacts. SciPy may remain only as an XGBoost runtime dependency.
- Keep a legacy Compose profile and the original pickle-compatible image available during the cutover window.
- Remove the legacy execution path and migration-only dependencies only after the separated stack passes the full evaluation dataset and end-to-end PHP flow.

## Main risks and rollback

| Risk | Mitigation and rollback |
|---|---|
| Pickle cannot be loaded after an upgrade | Convert it only in the reconstructed XGBoost 2.0.3 environment and retain the legacy image. |
| Predictions change silently | Compare raw per-sequence probabilities and exact labels before accepting each migration stage. |
| Direct NumPy extraction changes features | Require exact feature-matrix equality before removing ARFF processing. |
| Latest dependencies are incompatible | Keep conversion, dependency upgrade, and refactoring in separate pull requests; roll back the failing stage only. |
| CPU-only XGBoost behaves differently | Run the complete 16-model baseline and pin thread counts and package hashes. |
| PHP loses current downloads | Generate them from authoritative JSON until usage review allows their removal. |
| Python service is unavailable | Return a controlled PHP error and retain the legacy Compose profile during cutover. |
| Large or concurrent uploads exhaust resources | Stream uploads and enforce limits in Nginx, PHP, Python, and Docker. |

## Proposed issues and pull-request order

Create `develop-v2` from `develop` after this plan is approved. Treat `develop-v2` as the temporary integration branch for the complete modernization:

- Do not implement modernization changes directly on `develop-v2`.
- Create one issue branch from the latest `develop-v2` for each item below.
- Open each issue pull request against `develop-v2`, not `develop`.
- Keep `develop-v2` synchronized with necessary fixes from `develop`, resolving integration conflicts there rather than in individual completed branches.
- Protect `develop-v2` with the same review and required-check rules as `develop`.
- After the complete modernized stack passes model equivalence, container, PHP integration, and rollback testing, open one final pull request from `develop-v2` into `develop`.
- Keep normal maintenance and emergency fixes targeting `develop`; selectively merge those commits into `develop-v2` when they affect the modernization.

Use one branch and pull request per issue, and merge them into `develop-v2` in this order:

| Order | Issue | Branch |
|---:|---|---|
| 1 | Capture the reproducible model baseline | `modernize/model-baseline` |
| 2 | Convert and verify the models as UBJSON | `modernize/model-ubjson` |
| 3 | Create the standalone inference package | `modernize/inference-package` |
| 4 | Replace ARFF with equivalent direct feature extraction | `modernize/direct-feature-extraction` |
| 5 | Upgrade and lock the Python inference dependencies | `modernize/latest-python-dependencies` |
| 6 | Add the synchronous prediction API | `modernize/prediction-api` |
| 7 | Build and validate the Python model image | `modernize/python-model-image` |
| 8 | Add the separated services to Docker Compose | `modernize/docker-separation` |
| 9 | Replace PHP process execution with the API client | `modernize/php-api-client` |
| 10 | Upgrade and reduce the PHP image | `modernize/php-8-5` |
| 11 | Remove validated legacy runtime paths | `modernize/legacy-cleanup` |

The baseline and conversion pull requests must merge before any runtime update. The Python image must pass independently before PHP integration. PHP modernization and legacy removal remain last. Do not merge `develop-v2` into `develop` until all eleven issues are complete and the final acceptance suite passes.
