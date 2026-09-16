"""Canonical species metadata shared by preparation and experiments."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from types import MappingProxyType
from typing import Iterable, Mapping

import yaml


@dataclass(frozen=True)
class SpeciesMetadata:
    """The two experiment-facing evolutionary classifications of a species."""

    identifier: str
    scientific_name: str
    evolutionary_group: str
    evolutionary_distance_group: str


def _load_metadata() -> dict:
    resource = files("rnamining").joinpath("resources/species.yaml")
    with resource.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


_METADATA = _load_metadata()
_CATALOG = tuple(SpeciesMetadata(**entry) for entry in _METADATA["species"])

SPECIES_METADATA: Mapping[str, SpeciesMetadata] = MappingProxyType(
    {item.identifier: item for item in _CATALOG}
)
SPECIES = tuple(item.identifier for item in _CATALOG)

DISTANCE_GROUP_CLASSIFICATIONS: Mapping[str, str] = MappingProxyType(
    _METADATA["distance_group_classifications"]
)

_LOOKUP = {
    " ".join(value.replace("_", " ").split()).casefold(): identifier
    for identifier, item in SPECIES_METADATA.items()
    for value in (identifier, item.scientific_name)
}


def normalize_species_name(value: str) -> str:
    """Return the canonical underscore-separated identifier for a species."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Species name must be a non-empty string.")

    key = " ".join(value.replace("_", " ").split()).casefold()
    try:
        return _LOOKUP[key]
    except KeyError as error:
        raise ValueError(f"Unknown species name: {value!r}.") from error


def get_species_metadata(species: str) -> SpeciesMetadata:
    """Return metadata for a canonical identifier or scientific name."""
    return SPECIES_METADATA[normalize_species_name(species)]


def validate_species_names(names: Iterable[str], *, require_all: bool = False) -> tuple[str, ...]:
    """Normalize names and optionally require the complete 16-species catalog."""
    normalized = tuple(normalize_species_name(name) for name in names)
    if len(set(normalized)) != len(normalized):
        raise ValueError("Species list contains duplicates after normalization.")

    if require_all:
        found = set(normalized)
        missing = sorted(set(SPECIES) - found)
        unexpected = sorted(found - set(SPECIES))
        if missing or unexpected:
            details = []
            if missing:
                details.append("missing: " + ", ".join(missing))
            if unexpected:
                details.append("unexpected: " + ", ".join(unexpected))
            raise ValueError("Species catalog is incomplete (" + "; ".join(details) + ")")

    return normalized


def select_species(
    species: Iterable[str] | str | None = None,
    *,
    evolutionary_group: str | None = None,
    distance_group: str | None = None,
) -> tuple[str, ...]:
    """Select catalog species using reusable experiment filters."""
    selected = set(SPECIES if species is None else (
        (species,) if isinstance(species, str) else validate_species_names(species)
    ))

    if evolutionary_group is not None:
        known_groups = {
            item.evolutionary_group for item in SPECIES_METADATA.values()
        }
        if evolutionary_group not in known_groups:
            raise ValueError(f"Unknown evolutionary group: {evolutionary_group!r}.")
        selected &= {
            item.identifier for item in SPECIES_METADATA.values()
            if item.evolutionary_group == evolutionary_group
        }

    if distance_group is not None:
        group = distance_group.upper()
        if group not in DISTANCE_GROUP_CLASSIFICATIONS:
            raise ValueError(f"Unknown evolutionary distance group: {distance_group!r}.")
        selected &= {
            item.identifier for item in SPECIES_METADATA.values()
            if item.evolutionary_distance_group == group
        }

    return tuple(identifier for identifier in SPECIES if identifier in selected)
