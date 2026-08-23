import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _exact_project_requirement(requirement):
    match = re.fullmatch(r"([A-Za-z0-9_-]+)==(.+)", requirement)
    assert match, f"Project requirement is not exactly pinned: {requirement}"
    return match.groups()


def test_project_and_conda_dependency_versions_are_synchronized():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    environment = (ROOT / "environment.yml").read_text()
    conda_versions = dict(
        re.findall(
            r"^\s*-\s+([a-z][a-z0-9-]*)=([^=\s]+)(?:=.*)?$",
            environment,
            flags=re.MULTILINE,
        )
    )

    assert project["project"]["requires-python"] == "==3.14.6"
    assert conda_versions["python"] == "3.14.6"
    assert conda_versions["pip"] == "26.1.2"

    project_requirements = [
        *project["build-system"]["requires"],
        *project["project"]["dependencies"],
        *project["project"]["optional-dependencies"]["test"],
        *project["project"]["optional-dependencies"].get("notebooks", []),
    ]
    project_versions = dict(map(_exact_project_requirement, project_requirements))

    assert project_versions == {
        "setuptools": "83.0.0",
        "biopython": "1.87",
        "numpy": "2.5.1",
        "pandas": "3.0.3",
        "scikit-learn": "1.9.0",
        "scipy": "1.18.0",
        "xgboost": "3.3.0",
        "pytest": "9.0.3",
    }
    assert {
        dependency: conda_versions[dependency]
        for dependency in project_versions
    } == project_versions
