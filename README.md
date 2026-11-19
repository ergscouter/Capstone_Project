# Capstone_Project

## Campus Buddy (Digital Campus Twin)

A web app that helps UNT students plan their day across campus. Team: DRAM Dredgers (CSCE 4901, Team 1 A).

Team members: Rathnakar Reddy Andem, Ethan Grandfield, Tristan Beha, Carolina Estrada.

## Status

Sprint 1 scaffold. See [docs/sprint1.md](docs/sprint1.md) for progress and the Sprint 2 plan.

What works today:

- Flask API that loads UNT buildings from CSV (`/api/buildings`, `/api/buildings/<code>`, `/api/search?q=`)
- Leaflet map of campus buildings with click-to-view details
- Search by building name or code, with zoom to the building
- Manual class entry and a schedule list, including multiple meeting patterns per course

## Schedule entry

Use **My Schedule** beside the map to add a course code, optional title, meeting
days, start/end times, building, and optional room. Enter the same course code
again to add another meeting pattern for that course, such as a lecture and lab.
Identical meetings are rejected.

This first version supports scheduled, in-person meetings. Classes stay in page
memory and are cleared on refresh; automatic saving and editing are next steps.
Schedule entries are not sent to the server, and no Eagle Eye account is needed.

`frontend/schedule-model.js` defines the shared course format: `id`, `courseCode`,
`title`, and a `meetings` array. Each meeting has `days` (`mon` through `sun`),
`startTime`/`endTime` (24-hour `HH:mm` campus clock times), `buildingCode`, and
`room`. Building codes remain strings so leading zeroes are preserved. The form
uses this model independently of the map code. A future extension or other
importer can convert its output to the same format without replacing the schedule
screen. Importing, online/TBA meetings, and term dates are not implemented yet.

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

## Question parser

`backend/assistant/` turns typed questions into structured intents, such as `route(origin, destination, time)` or `simulate_event(venue, attendance)`. It uses no LLM and has no dependencies beyond Python. Typos are handled with fuzzy matching.

- `catalog.py`: the supported question types, their parameters, and keyword phrases. Add an intent here to support a new question.
- `entities.py`: finds building names (including nicknames like "the union" or "GAB"), times, days, and crowd sizes.
- `POST /api/ask` with `{"text": "..."}` returns the intent. If a required parameter is missing, the response includes a `follow_up` question. Send the response back as `pending` along with the user's answer.
- Try it in a terminal: `python backend/assistant`
- The labeled sample questions are in `tests/test_assistant.py`. Add real questions there as you collect them.

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
