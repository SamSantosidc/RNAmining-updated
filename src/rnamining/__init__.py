"""RNAmining's data preparation, training, inference, and evaluation interfaces."""

from importlib import import_module
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

_LAZY_EXPORTS = {
    "calculate_metrics": ("rnamining.evaluation", "calculate_metrics"),
    "evaluate_model": ("rnamining.evaluation", "evaluate_model"),
    "export_results": ("rnamining.evaluation", "export_results"),
    "summarize_metrics": ("rnamining.evaluation", "summarize_metrics"),
    "DISTANCE_GROUP_CLASSIFICATIONS": (
        "rnamining.metadata",
        "DISTANCE_GROUP_CLASSIFICATIONS",
    ),
    "SPECIES_METADATA": ("rnamining.metadata", "SPECIES_METADATA"),
    "SpeciesMetadata": ("rnamining.metadata", "SpeciesMetadata"),
    "get_species_metadata": ("rnamining.metadata", "get_species_metadata"),
    "normalize_species_name": ("rnamining.metadata", "normalize_species_name"),
    "select_species": ("rnamining.metadata", "select_species"),
    "validate_species_names": ("rnamining.metadata", "validate_species_names"),
}


def __getattr__(name):
    try:
        module_name, attribute = _LAZY_EXPORTS[name]
    except KeyError as error:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from error

    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value


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
