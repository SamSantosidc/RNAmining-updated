"""RNAmining's data preparation, training, inference, and evaluation interfaces."""

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

__version__ = "1.0.4"
