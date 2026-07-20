"""Small FASTA helpers shared by preparation, training, and inference."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Union

PathLike = Union[str, Path]


class FastaError(ValueError):
    """Raised when an input does not have the FASTA structure RNAmining expects."""




@dataclass(frozen=True)
class FastaRecord:
    header: str
    sequence: str

    @property
    def identifier(self) -> str:
        return self.header.split()[0]



def read_fasta(path: PathLike, *, validate: bool = True) -> list[FastaRecord]:
    path = Path(path)
    lines = path.read_text(encoding="utf-8").splitlines()

    if validate and (not lines or not lines[0].startswith(">") or lines[-1].startswith(">")):
        raise FastaError(
            "The inserted file does not match FASTA format: check its headers and sequences."
        )

    records: list[FastaRecord] = []
    header = None
    sequence: list[str] = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line.startswith(">"):
            if header is not None:
                records.append(FastaRecord(header, "".join(sequence)))

            header = line[1:]
            sequence = []

        elif header is None:
            if validate:
                raise FastaError("Sequence data appears before the first FASTA header.")
            
        else:
            sequence.append(line)

    if header is not None:
        records.append(FastaRecord(header, "".join(sequence)))

    if validate and (not records or any(not record.sequence for record in records)):
        raise FastaError("Every FASTA header must be followed by a sequence.")
    
    return records



def write_fasta(records: Iterable[FastaRecord], path: PathLike) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as output:
        for record in records:
            output.write(f">{record.header}\n{record.sequence}\n")
            
    return path



def canonicalize_fasta(source: PathLike, destination: PathLike) -> list[FastaRecord]:
    records = read_fasta(source)
    write_fasta(records, destination)
    return records
