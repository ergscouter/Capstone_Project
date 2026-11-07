"""Pre-merge checks for the question parser against the real UNT building data.

test_assistant.py uses a hand-picked list of 17 buildings. These tests load
data/UNT_buildings.csv (all 164 buildings), where name clashes and fuzzy
matches between similar names actually show up. The whole file is skipped if
the CSV is not in data/.

Run just this file:  pytest tests/test_assistant_real_data.py -v
"""

import json
import random
import string
from datetime import datetime

import pytest

from app import create_app
from assistant import INTENTS_BY_NAME, Parser
from assistant.entities import NICKNAMES, aliases_for_name
from buildings import DEFAULT_CSV_PATH, BuildingIndex

pytestmark = pytest.mark.skipif(
    not DEFAULT_CSV_PATH.exists(), reason="data/UNT_buildings.csv is not present"
)

THURSDAY = datetime(2026, 11, 5, 14, 0)
RESULT_KEYS = {"text", "intent", "confidence", "slots", "missing", "follow_up", "suggestions", "complete"}


@pytest.fixture(scope="module")
def index() -> BuildingIndex:
    return BuildingIndex.from_csv()


@pytest.fixture(scope="module")
def parser(index) -> Parser:
    return Parser(index.all())


@pytest.fixture(scope="module")
def client(index):
    return create_app(index).test_client()


def _codes(slots: dict) -> dict:
    return {k: v["code"] if isinstance(v, dict) else v for k, v in slots.items()}


# ---- the building data itself -------------------------------------------------

def test_every_nickname_points_to_a_real_building(index):
    """A nickname for a code that is not in the CSV is silently dropped."""
    missing = [code for code in NICKNAMES if index.get(code) is None]
    assert missing == []


def test_no_building_name_is_claimed_by_another_building(parser, index):
    """If 'kerr' (from Kerr Hall) pointed at a different building, users would get the wrong one."""
    alias_to_code = parser.extractor.matcher._alias_to_code
    clashes = []
    for b in index.all():
        for alias in aliases_for_name(b.name):
            owner = alias_to_code.get(alias)
            if owner and owner != b.code:
                clashes.append(f"{b.name!r}: {alias!r} -> {owner}")
    assert clashes == []


@pytest.mark.parametrize("template", ["where is {}", "where is the {}"])
def test_every_building_is_found_by_its_official_name(parser, index, template):
    wrong = []
    for b in index.all():
        if not b.name:
            continue
        result = parser.parse(template.format(b.name))
        got = result.slots.get("building", {}).get("code")
        if got != b.code:
            wrong.append(f"{b.code} {b.name!r} -> {got}")
    assert wrong == []


# ---- real questions -----------------------------------------------------------
# (question, intent, expected slot values). The first two are the professor's
# example queries from the project description.

REAL_QUESTIONS = [
    ("What is the fastest way to walk from the Union to the Environmental Science Building "
     "at 1 pm on Thursdays?", "route",
     {"origin": "0155", "destination": "0160", "time": "13:00", "day": "thursday"}),
    ("What happens to parking availability if the university hosts a 5000 person event "
     "at the Coliseum?", "simulate_event", {"venue": "0154", "attendance": 5000}),
    ("how do i get from willis to the gab", "route", {"origin": "0149", "destination": "0108"}),
    ("directions from eesat to discovery park", "route", {"origin": "0160", "destination": "0190"}),
    ("how far is kerr from the union", "route", {"origin": "0155", "destination": "0180"}),
    ("how do i get from the union to the library", "route", {"origin": "0155", "destination": "0149"}),
    ("where is the music building", "locate", {"building": "0127"}),
    ("where is the union circle garage", "locate", {"building": "0001"}),
    ("where is the library annex", "locate", {"building": "0170"}),
    ("where is the ESSC", "locate", {"building": "0113"}),
    ("tell me about the blb", "building_info", {"building": "0156"}),
    ("how big is the coliseum", "building_info", {"building": "0154"}),
    ("is willis open sunday", "hours", {"building": "0149", "day": "sunday"}),
    ("how busy is the rec at 5pm", "occupancy", {"building": "0118", "time": "17:00"}),
    ("where can i park near apogee", "parking", {"building": "0322"}),
    ("what if 20k people go to apogee saturday", "simulate_event",
     {"venue": "0322", "attendance": 20000, "day": "saturday"}),
    ("what if the union is closed", "simulate_closure", {"building": "0155"}),
]


@pytest.mark.parametrize("question,intent,expected", REAL_QUESTIONS, ids=[q[0][:60] for q in REAL_QUESTIONS])
def test_real_questions(parser, question, intent, expected):
    result = parser.parse(question, now=THURSDAY)
    assert result.intent == intent
    actual = _codes(result.slots)
    assert {k: actual.get(k) for k in expected} == expected
    assert result.missing == []


# ---- the result is always well formed ------------------------------------------

def _assert_well_formed(result: dict):
    assert set(result) == RESULT_KEYS
    assert 0.0 <= result["confidence"] <= 1.0
    if result["intent"] == "unknown":
        assert result["complete"] is False
        return
    intent = INTENTS_BY_NAME[result["intent"]]
    assert set(result["slots"]) <= {s.name for s in intent.slots}
    assert result["missing"] == [s.name for s in intent.required if s.name not in result["slots"]]
    assert result["complete"] == (not result["missing"])
    assert (result["follow_up"] is not None) == bool(result["missing"])
    json.dumps(result)  # the endpoint must be able to send it


ODD_INPUTS = [
    "", " ", "?", "!!!", "a" * 300, "where is", "from to", "the the the", "0155", "building 9999",
    "WHERE IS WILLIS LIBRARY???", "where's willis", "willis\nlibrary", "where is Willis Libary",
    "5000000000000000000000 people at the coliseum", "1,000,000 fans at apogee", "-5 people",
    "at 25:99", "13pm", "café at the union", "how do i get to the union 🙂",
    "<script>alert(1)</script>", "'; DROP TABLE buildings; --",
]


@pytest.mark.parametrize("text", ODD_INPUTS)
def test_odd_input_never_crashes(parser, text):
    _assert_well_formed(parser.parse(text).to_dict())


BAD_PENDING = [
    None, {}, [], "route", 5, {"intent": "nope", "missing": ["origin"]},
    {"intent": "route", "missing": "origin"},
    {"intent": "route", "missing": ["origin"], "slots": "x"},
    {"intent": "route", "missing": ["origin"], "slots": {"destination": "0149"}},
    {"intent": "route", "missing": ["origin"], "slots": {"destination": {"code": None}}},
    {"intent": "simulate_event", "missing": ["venue"], "slots": {"attendance": -10}},
    {"intent": "simulate_event", "missing": ["venue"], "slots": {"attendance": "lots"}},
    {"intent": "route", "missing": ["origin"], "slots": {"time": "x" * 1000}},
]


@pytest.mark.parametrize("pending", BAD_PENDING)
def test_bad_pending_never_crashes(parser, pending):
    result = parser.parse("the union", pending=pending).to_dict()
    _assert_well_formed(result)
    assert "x" * 11 not in json.dumps(result)  # oversized client values are not echoed back


def test_random_input_never_crashes(parser):
    rng = random.Random(4901)
    alphabet = string.printable + "é’—🙂"
    for _ in range(2000):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 120)))
        _assert_well_formed(parser.parse(text).to_dict())


# ---- follow-ups survive a round trip through JSON, as they will in the browser ---

def test_follow_up_round_trip_through_json(parser):
    first = parser.parse("how do I get to Willis Library", now=THURSDAY)
    assert first.missing == ["origin"]
    pending = json.loads(json.dumps(first.to_dict()))
    second = parser.parse("from the gab", pending=pending, now=THURSDAY)
    assert second.complete
    assert _codes(second.slots) == {"origin": "0108", "destination": "0149"}


def test_two_step_simulation_follow_up(parser):
    first = parser.parse("what if there's an event", now=THURSDAY).to_dict()
    assert first["intent"] == "simulate_event"
    second = parser.parse("the coliseum", pending=first).to_dict()
    assert second["slots"]["venue"]["code"] == "0154"
    assert second["missing"] == ["attendance"]
    third = parser.parse("12,000", pending=second).to_dict()
    assert third["complete"] is True
    assert third["slots"]["attendance"] == 12000


# ---- POST /api/ask with the real data -----------------------------------------

def test_ask_returns_full_result(client):
    response = client.post("/api/ask", json={"text": "how do i get from willis to the gab"})
    assert response.status_code == 200
    body = response.get_json()
    _assert_well_formed(body)
    assert body["intent"] == "route"
    assert body["slots"]["origin"] == {"code": "0149", "name": "Willis Library"}


def test_ask_follow_up_round_trip(client):
    first = client.post("/api/ask", json={"text": "directions to the coliseum"}).get_json()
    assert first["follow_up"] == "Where are you starting from?"
    second = client.post("/api/ask", json={"text": "the union", "pending": first}).get_json()
    assert second["complete"] is True
    assert _codes(second["slots"]) == {"origin": "0155", "destination": "0154"}


def test_ask_accepts_max_length_question(client):
    assert client.post("/api/ask", json={"text": "a" * 300}).status_code == 200


@pytest.mark.parametrize("kwargs", [
    {"data": "where is willis", "content_type": "text/plain"},
    {"data": "{not json", "content_type": "application/json"},
    {"json": ["where is willis"]},
    {"json": {"text": "   "}},
])
def test_ask_rejects_malformed_requests(client, kwargs):
    assert client.post("/api/ask", **kwargs).status_code == 400


def test_ask_is_post_only(client):
    # The frontend catch-all route also matches GET /api/ask, finds no such
    # file, and returns 404 rather than 405. Either way the parser must not run.
    response = client.get("/api/ask")
    assert response.status_code in (404, 405)
    assert "intent" not in response.get_data(as_text=True)
