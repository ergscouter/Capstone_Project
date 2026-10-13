# Sprint 1 Progress Report

Sprints are progress check-ins with the TA. Each one covers what we built, what is in progress, and what the next sprint will deliver.

## Project

Campus Buddy is a web application that combines campus navigation resources (maps, parking, building info, class schedules) into one tool for planning a day on campus. Our Sprint 1 focus is the base map and building information (requirement R7 in the product requirements), since every later feature depends on it.

## Done in Sprint 1

- Project skeleton: Flask backend, Leaflet map frontend, pytest test suite, `.gitignore`, README with VS Code setup steps.
- Loader for the UNT building list (about 250 records). It trims whitespace, handles missing coordinates, and fixes a sign error in some longitudes. It reports each problem at startup so the data can be corrected at the source.
- API endpoints: list buildings, get one building, and search by name or code.
- Map page showing buildings as points, with click-to-view details (name, code, footprint, perimeter, coordinates) and a search box that zooms to a building.
- Tests for the loader and the API.

## Known issues and risks

- One building (Science and Technology, 0166) has no coordinates, so it cannot be shown on the map yet.
- Two longitudes (0309 and 0326) are missing their minus sign. The loader corrects them, but the team should confirm against the UNT source.
- The building file does not yet include classrooms, hours, or categories. These are required for R7 and need a second data source.
- The map uses OpenStreetMap tiles. Our requirements mention Google Maps as a possible later integration. We have not decided this yet.

## In progress

- Confirming the shape of the campus path data (sidewalks, pedestrian paths, driveways, parking areas, exit doors, buildings in GeoJSON-style JSON). These files are not used by the app yet.

## Sprint 2 plan

1. Import the campus path layers into a walkable graph so routes follow sidewalks and paths instead of straight lines.
2. Compute walking time between two buildings (R1, R6 basics) and show the route as text.
3. Draw the route on the map (R2).
4. Add building categories and hours to the data, and confirm the source (R7 complete).
5. Write the test plan for the route calculation, since accuracy matters (NF3).

## Questions for the TA

- Is the building list from the UNT open data source acceptable, or do we need the UNT database connection described in the ideas document?
- Should we use Google Maps for the base map, or stay with OpenStreetMap?
