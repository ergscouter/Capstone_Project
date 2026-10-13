"""Load UNT building records from the campus CSV and validate them."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Optional

DEFAULT_CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "UNT_buildings.csv"

# Rough bounding box around the Denton campus. Coordinates outside it are bad data.
CAMPUS_LAT_RANGE = (33.18, 33.27)
CAMPUS_LON_RANGE = (-97.20, -97.11)


@dataclass(frozen=True)
class Building:
    code: str
    name: str
    lat: Optional[float]
    lon: Optional[float]
    footprint_sqft: Optional[int]
    perimeter_ft: Optional[int]

    @property
    def has_location(self) -> bool:
        return self.lat is not None and self.lon is not None

    def to_dict(self) -> dict:
        return asdict(self)


def _clean_text(value: Optional[str]) -> str:
    # The source data has trailing spaces and doubled spaces; collapse them.
    return " ".join((value or "").split())


def _to_float(value: Optional[str]) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Optional[str]) -> Optional[int]:
    number = _to_float(value)
    return int(number) if number is not None else None


def _in_campus(lat: float, lon: float) -> bool:
    lat_min, lat_max = CAMPUS_LAT_RANGE
    lon_min, lon_max = CAMPUS_LON_RANGE
    return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max


def _check_coordinates(
    code: str, lat: Optional[float], lon: Optional[float], warnings: list[str]
) -> tuple[Optional[float], Optional[float]]:
    """Return usable (lat, lon), or (None, None) if the building cannot be placed."""
    if lat is None or lon is None:
        warnings.append(f"{code}: no coordinates")
        return None, None
    if _in_campus(lat, lon):
        return lat, lon
    # Some rows are missing the minus sign on longitude (Texas longitudes are negative).
    if _in_campus(lat, -lon):
        warnings.append(f"{code}: longitude sign corrected")
        return lat, -lon
    warnings.append(f"{code}: coordinates outside campus, ignored")
    return None, None


def parse_row(row: dict, warnings: list[str]) -> Building:
    code = _clean_text(row.get("BLDGCODE"))
    lat, lon = _check_coordinates(
        code, _to_float(row.get("LAT")), _to_float(row.get("LON")), warnings
    )
    return Building(
        code=code,
        name=_clean_text(row.get("NAME")),
        lat=lat,
        lon=lon,
        footprint_sqft=_to_int(row.get("Footprint_sqft")),
        perimeter_ft=_to_int(row.get("Perimeter_ft")),
    )


class BuildingIndex:
    """In-memory collection of buildings with lookup and search."""

    def __init__(self, buildings: Iterable[Building], warnings: Iterable[str] = ()):
        self._buildings = sorted(buildings, key=lambda b: b.code)
        self._by_code = {b.code: b for b in self._buildings}
        self.warnings = list(warnings)

    @classmethod
    def from_csv(cls, path: Path = DEFAULT_CSV_PATH) -> "BuildingIndex":
        warnings: list[str] = []
        buildings: list[Building] = []
        # utf-8-sig drops a byte-order mark if Excel added one.
        with open(path, newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                building = parse_row(row, warnings)
                if building.code:
                    buildings.append(building)
                else:
                    warnings.append("row without a building code skipped")
        return cls(buildings, warnings)

    def __len__(self) -> int:
        return len(self._buildings)

    def all(self) -> list[Building]:
        return list(self._buildings)

    def get(self, code: str) -> Optional[Building]:
        code = code.strip()
        if code.isdigit():
            code = code.zfill(4)  # accept "101" as well as "0101"
        return self._by_code.get(code)

    def search(self, query: str, limit: int = 20) -> list[Building]:
        needle = _clean_text(query).lower()
        if not needle:
            return []
        matches = [
            b for b in self._buildings if needle in b.name.lower() or needle in b.code
        ]
        return matches[:limit]
