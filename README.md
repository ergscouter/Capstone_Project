# Campus Buddy (Digital Campus Twin)

A web app that helps UNT students plan their day across campus. Team: DRAM Dredgers (CSCE 4901, Team 1 A).

Team members: Rathnakar Reddy Andem, Ethan Grandfield, Tristan Beha, Carolina Estrada.

## Status

Sprint 1 scaffold. See [docs/sprint1.md](docs/sprint1.md) for progress and the Sprint 2 plan.

What works today:

- Flask API that loads UNT buildings from CSV (`/api/buildings`, `/api/buildings/<code>`, `/api/search?q=`)
- Leaflet map of campus buildings with click-to-view details
- Search by building name or code, with zoom to the building

## Project layout

```
backend/    Flask app and data loading
frontend/   HTML, CSS, and JavaScript for the map page
tests/      pytest tests for the loader and API
data/       Place UNT_buildings.csv here (see data/README.md)
docs/       Sprint notes
```

## Running it in VS Code

1. Open the `campus-buddy` folder in VS Code.
2. Copy `UNT_buildings.csv` from the project into `data/`.
3. In the VS Code terminal:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python backend/app.py
```

4. Open http://localhost:5000 in a browser.

## Running the tests

```bash
pytest
```

The tests use a small built-in sample, so they run without the CSV.

## Git workflow

```bash
git checkout -b sprint-1
git add .
git commit -m "Describe the change"
git push -u origin sprint-1
```

Open a pull request into `main` on GitHub so a teammate can review it.
