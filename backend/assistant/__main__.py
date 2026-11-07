"""Try the parser from a terminal:  python backend/assistant

Type questions and see the structured intent. Follow-up answers are linked
to the previous question, as they would be in the app.
"""

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from assistant import Parser  # noqa: E402
from buildings import DEFAULT_CSV_PATH, BuildingIndex  # noqa: E402

# Until data/UNT_buildings.csv is in place, the GIS export in Docs/ has the same columns.
FALLBACK_CSV = BACKEND_DIR.parent / "Docs" / "Building_Cartographic_Shape.csv"


def main() -> None:
    csv_path = DEFAULT_CSV_PATH if DEFAULT_CSV_PATH.exists() else FALLBACK_CSV
    parser = Parser(BuildingIndex.from_csv(csv_path).all())
    print(f"Loaded buildings from {csv_path.name}. Ctrl+C or a blank line to quit.")
    pending = None
    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            break
        result = parser.parse(text, pending=pending)
        print(json.dumps(result.to_dict(), indent=2))
        pending = result.to_dict() if result.missing else None


if __name__ == "__main__":
    main()
