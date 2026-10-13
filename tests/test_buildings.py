from buildings import BuildingIndex


def test_loads_every_row(sample_index):
    assert len(sample_index) == 5


def test_missing_coordinates_are_flagged(sample_index):
    building = sample_index.get("0166")
    assert building is not None
    assert not building.has_location
    assert "0166: no coordinates" in sample_index.warnings


def test_positive_longitude_is_repaired(sample_index):
    building = sample_index.get("0309")
    assert building.lon < 0
    assert "0309: longitude sign corrected" in sample_index.warnings


def test_names_are_whitespace_cleaned(sample_index):
    assert sample_index.get("0114").name == "Science Research Bldg Storage"


def test_code_lookup_accepts_unpadded_codes(sample_index):
    assert sample_index.get("101") is not None
    assert sample_index.get(" 0101 ") is not None


def test_unknown_code_returns_none(sample_index):
    assert sample_index.get("9999") is None


def test_search_is_case_insensitive_on_name(sample_index):
    assert [b.code for b in sample_index.search("student")] == ["0155"]


def test_search_matches_building_code(sample_index):
    assert [b.code for b in sample_index.search("0101")] == ["0101"]


def test_search_returns_all_name_matches(sample_index):
    codes = sorted(b.code for b in sample_index.search("science"))
    assert codes == ["0114", "0166"]


def test_blank_search_returns_nothing(sample_index):
    assert sample_index.search("   ") == []


def test_row_without_code_is_skipped(tmp_path):
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text(
        "BLDGCODE,NAME,LAT,LON,Footprint_sqft,Perimeter_ft\n,No Code,33.21,-97.14,1,1\n",
        encoding="utf-8",
    )
    index = BuildingIndex.from_csv(csv_path)
    assert len(index) == 0
    assert "row without a building code skipped" in index.warnings
