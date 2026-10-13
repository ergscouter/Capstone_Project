# Data

The app reads building records from `UNT_buildings.csv` in this folder.

Copy the file from the team's project folder (`UNT_buildings.csv`) into this `data/` folder before running the app. The file is not committed in this scaffold so the team can decide how to manage shared data.

Columns used: `BLDGCODE`, `NAME`, `LAT`, `LON`, `Footprint_sqft`, `Perimeter_ft`.

Known data issues (handled by the loader, reported at startup):

- `0166 Science and Technology` has no coordinates, so it is listed but not shown on the map.
- `0309` and `0326` have a longitude missing its minus sign; the loader corrects these.
- Some names contain extra spaces; the loader trims them.
