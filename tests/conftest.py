import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from buildings import BuildingIndex  # noqa: E402

# Small fixture so tests do not depend on the real data file.
SAMPLE_CSV = """BLDGCODE,NAME,LAT,LON,Footprint_sqft,Perimeter_ft
0101,Hurley Administration Bldg,33.21114542,-97.14846448,19305,764
0114,Science Research Bldg Storage        ,33.21450289,-97.14893818,390,79
0155,Student Union,33.21075917,-97.14728228,112450,3003
0166,Science and Technology,,,26504,710
0309,Lovelace & McNatt Families Practice Facility,33.2017347,97.1592642,89704,1430
"""


@pytest.fixture
def sample_index(tmp_path) -> BuildingIndex:
    csv_path = tmp_path / "buildings.csv"
    csv_path.write_text(SAMPLE_CSV, encoding="utf-8")
    return BuildingIndex.from_csv(csv_path)
