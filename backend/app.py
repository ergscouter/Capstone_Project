"""Flask server for Campus Buddy: serves the map page and the building data API."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory

from assistant import Parser
from buildings import DEFAULT_CSV_PATH, BuildingIndex

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
MAX_QUERY_LENGTH = 100
MAX_QUESTION_LENGTH = 300


def create_app(index: BuildingIndex | None = None) -> Flask:
    app = Flask(__name__)
    buildings = index if index is not None else BuildingIndex.from_csv()
    parser = Parser(buildings.all())

    @app.get("/")
    def home():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.get("/api/health")
    def health():
        return jsonify(status="ok", buildings_loaded=len(buildings))

    @app.get("/api/buildings")
    def list_buildings():
        return jsonify([b.to_dict() for b in buildings.all()])

    @app.get("/api/buildings/<code>")
    def get_building(code: str):
        building = buildings.get(code)
        if building is None:
            abort(404, description=f"No building with code {code}")
        return jsonify(building.to_dict())

    @app.get("/api/search")
    def search_buildings():
        query = request.args.get("q", "")
        if len(query) > MAX_QUERY_LENGTH:
            abort(400, description="Search text is too long")
        return jsonify([b.to_dict() for b in buildings.search(query)])

    @app.post("/api/ask")
    def ask():
        """Parse a typed question into an intent. Body: {"text": ..., "pending": <previous result>}."""
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            abort(400, description='Send a JSON object like {"text": "..."}')
        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            abort(400, description="Send the question as 'text'")
        if len(text) > MAX_QUESTION_LENGTH:
            abort(400, description="Question is too long")
        result = parser.parse(text, pending=payload.get("pending"))
        return jsonify(result.to_dict())

    @app.get("/<path:filename>")
    def static_files(filename: str):
        return send_from_directory(FRONTEND_DIR, filename)

    return app


if __name__ == "__main__":
    if not DEFAULT_CSV_PATH.exists():
        raise SystemExit(
            f"Missing {DEFAULT_CSV_PATH}. Copy UNT_buildings.csv from the project into data/."
        )
    index = BuildingIndex.from_csv()
    for warning in index.warnings:
        print(f"[data] {warning}")
    create_app(index).run(debug=True, port=5000)
