# Python 3.14 Dependency Upgrade

## Summary

This modernization is limited to updating the existing Python dependency declarations and the documentation needed to use them. It does not change RNAmining's scientific pipeline, models, output formats, CLI behavior, web application, or Docker configuration.

## Target environment

`environment.yml` remains the shared, exact Conda specification and retains its declared `rnamining` name. For local modernization work, create it with the `rnamining-py314` override so it can coexist with an existing Python 3.8 environment:

```bash
conda env create --name rnamining-py314 --file environment.yml
conda activate rnamining-py314
python -m pip install -e '.[test,notebooks]'
```

| Dependency | Version |
|---|---:|
| Python | 3.14.6 |
| pip | 26.1.2 |
| setuptools | 83.0.0 |
| NumPy | 2.5.1 |
| pandas | 3.0.3 |
| SciPy | 1.18.0 |
| scikit-learn | 1.9.0 |
| XGBoost CPU | 3.3.0 |
| Biopython | 1.87 |
| pytest | 9.0.3 |
| ipykernel | 7.3.0 |
| JupyterLab | 4.6.2 |

Applicable versions are pinned exactly in both `pyproject.toml` and `environment.yml`. Pip is environment tooling rather than an application dependency, so it is pinned only in the Conda specification. XGBoost uses the CPU builds of the Conda `xgboost`, `py-xgboost`, and `libxgboost` packages.

## Validation

- Create the isolated local environment and install RNAmining in editable mode with its test and notebook extras.
- Verify the resolved Python and dependency versions.
- Run `pytest` under Python 3.14.6.
- Keep the automated metadata consistency test passing so direct pins cannot drift between project metadata and the Conda specification.

## Excluded work

This issue does not add lockfiles, prepare data, retrain or convert models, regenerate predictions or metrics, execute notebooks, introduce provenance manifests, restructure the package or pipeline, or modify Docker, Compose, PHP, or other web-runtime files. The Python 3.8 metrics report remains the unchanged scientific baseline.
