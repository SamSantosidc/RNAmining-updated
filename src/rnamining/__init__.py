"""RNAmining's data preparation, training, inference, and evaluation interfaces."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import tomllib


def _package_version() -> str:
    """Return the project version, falling back to installed metadata."""
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if pyproject.is_file():
        with pyproject.open("rb") as handle:
            return tomllib.load(handle)["project"]["version"]
    try:
        return version("rnamining")
    except PackageNotFoundError:
        return "unknown"

from .evaluation import (
    calculate_metrics,
    evaluate_model,
    export_results,
    summarize_metrics,
)
from .metadata import (
    DISTANCE_GROUP_CLASSIFICATIONS,
    SPECIES_METADATA,
    SpeciesMetadata,
    get_species_metadata,
    normalize_species_name,
    select_species,
    validate_species_names,
)

__all__ = (
    "calculate_metrics",
    "evaluate_model",
    "export_results",
    "summarize_metrics",
    "DISTANCE_GROUP_CLASSIFICATIONS",
    "SPECIES_METADATA",
    "SpeciesMetadata",
    "get_species_metadata",
    "normalize_species_name",
    "select_species",
    "validate_species_names",
)

__version__ = _package_version()
