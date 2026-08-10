"""Canonical species metadata shared by preparation and experiments."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping


@dataclass(frozen=True)
class SpeciesMetadata:
    """The two experiment-facing evolutionary classifications of a species."""

    identifier: str
    scientific_name: str
    evolutionary_group: str
    evolutionary_distance_group: str


_CATALOG = (
    SpeciesMetadata(
        "Anolis_carolinensis", "Anolis carolinensis",
        "Répteis — Lepidosauria", "B",
    ),
    SpeciesMetadata(
        "Chrysemys_picta_bellii", "Chrysemys picta bellii",
        "Quelônios", "B",
    ),
    SpeciesMetadata(
        "Crocodylus_porosus", "Crocodylus porosus",
        "Répteis — Archosauria", "B",
    ),
    SpeciesMetadata(
        "Danio_rerio", "Danio rerio",
        "Peixes ósseos — Teleostei", "D",
    ),
    SpeciesMetadata(
        "Eptatretus_burgeri", "Eptatretus burgeri",
        "Ciclóstomos — Agnatha", "E",
    ),
    SpeciesMetadata(
        "Gallus_gallus", "Gallus gallus", "Aves", "B",
    ),
    SpeciesMetadata(
        "Homo_sapiens", "Homo sapiens",
        "Mamíferos placentários — Eutheria", "A",
    ),
    SpeciesMetadata(
        "Latimeria_chalumnae", "Latimeria chalumnae",
        "Peixes de nadadeiras lobadas — Sarcopterygii", "D",
    ),
    SpeciesMetadata(
        "Monodelphis_domestica", "Monodelphis domestica",
        "Mamífero marsupial", "A",
    ),
    SpeciesMetadata(
        "Mus_musculus", "Mus musculus",
        "Mamíferos placentários — Eutheria", "A",
    ),
    SpeciesMetadata(
        "Notechis_scutatus", "Notechis scutatus",
        "Répteis — Lepidosauria", "B",
    ),
    SpeciesMetadata(
        "Ornithorhynchus_anatinus", "Ornithorhynchus anatinus",
        "Mamífero monotremado", "A",
    ),
    SpeciesMetadata(
        "Petromyzon_marinus", "Petromyzon marinus",
        "Ciclóstomos — Agnatha", "E",
    ),
    SpeciesMetadata(
        "Rattus_norvegicus", "Rattus norvegicus",
        "Mamíferos placentários — Eutheria", "A",
    ),
    SpeciesMetadata(
        "Sphenodon_punctatus", "Sphenodon punctatus",
        "Répteis — Lepidosauria", "B",
    ),
    SpeciesMetadata(
        "Xenopus_tropicalis", "Xenopus tropicalis", "Anfíbios", "C",
    ),
)

SPECIES_METADATA: Mapping[str, SpeciesMetadata] = MappingProxyType(
    {item.identifier: item for item in _CATALOG}
)
SPECIES = tuple(item.identifier for item in _CATALOG)

DISTANCE_GROUP_CLASSIFICATIONS: Mapping[str, str] = MappingProxyType({
    "A": "Mamíferos",
    "B": "Sauropsida",
    "C": "Anfíbios",
    "D": "Peixes",
    "E": "Vertebrados basais",
})

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
