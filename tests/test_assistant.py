"""Tests for the question parser.

SAMPLES is the labeled question set. Add real questions from users and
teammates here; each one becomes its own test, so a failure names the question.
"""

from datetime import datetime

import pytest

from app import create_app
from assistant import INTENTS, Parser
from assistant.entities import find_counts, find_time
from buildings import Building, BuildingIndex

# Real names from the UNT data, so aliases behave as they will in the app.
BUILDINGS = [
    Building(code, name, 33.21, -97.15, None, None)
    for code, name in [
        ("0108", "General Academic Bldg"),
        ("0113", "Eagle Student Services Center"),
        ("0118", "Pohl Recreation Center"),
        ("0126", "Chilton Hall"),
        ("0129", "Performing Arts Center"),
        ("0149", "Willis Library"),
        ("0150", "Wooten Hall"),
        ("0153", "Art Bldg"),
        ("0154", "Coliseum"),
        ("0155", "University Union Bldg"),
        ("0156", "Business Leadership Building"),
        ("0158", "Welch Street Complex 1"),
        ("0178", "Crumley Hall"),
        ("0180", "Kerr Hall"),
        ("0181", "West Hall"),
        ("0322", "Apogee Stadium"),
        ("0001", "Union Circle Parking Garage"),
    ]
]

TUESDAY = datetime(2026, 11, 3, 9, 0)

# (question, intent, expected slots: building slots by code, others by value)
SAMPLES = [
    ("fastest walk from the union to ESSC at 1 pm thursday", "route",
     {"origin": "0155", "destination": "0113", "time": "13:00", "day": "thursday"}),
    ("how do i walk from wooten hal to the libary", "route", {"origin": "0150", "destination": "0149"}),
    ("whats the quickest route from crumley to the pac", "route", {"origin": "0178", "destination": "0129"}),
    ("between kerr hall and the business leadership building how long is the walk", "route",
     {"origin": "0180", "destination": "0156"}),
    ("how far is chilton hall from the blb", "route", {"origin": "0156", "destination": "0126"}),
    ("How do I get to Willis Libary?", "route", {"destination": "0149"}),
    ("take me to bldg 150", "route", {"destination": "0150"}),
    ("walk to welch street complex 1 from art bldg at 10:30", "route",
     {"origin": "0153", "destination": "0158", "time": "10:30"}),
    ("where is the gab", "locate", {"building": "0108"}),
    ("show me West Hall on the map", "locate", {"building": "0181"}),
    ("tell me about wooten hall", "building_info", {"building": "0150"}),
    ("how big is the coliseum", "building_info", {"building": "0154"}),
    ("when does the library close on sunday", "hours", {"building": "0149", "day": "sunday"}),
    ("is the union open tomorrow", "hours", {"building": "0155", "day": "wednesday"}),
    ("is the union closed today", "hours", {"building": "0155", "day": "tuesday"}),
    ("how busy is the union at noon", "occupancy", {"building": "0155", "time": "12:00"}),
    ("is the rec center crowded", "occupancy", {"building": "0118"}),
    ("how many people are in the union", "occupancy", {"building": "0155"}),
    ("where can I park near the coliseum tonight", "parking",
     {"building": "0154", "time": "19:00", "day": "tuesday"}),
    ("parking at 8am", "parking", {"time": "08:00"}),
    ("what's happening at the union tonight", "events", {"building": "0155", "day": "tuesday"}),
    ("any events friday", "events", {"day": "friday"}),
    ("What happens to parking if 5000 people attend an event at the Coliseum?", "simulate_event",
     {"venue": "0154", "attendance": 5000}),
    ("Simulate a 20,000 person game at Apogee on Saturday", "simulate_event",
     {"venue": "0322", "attendance": 20000, "day": "saturday"}),
    ("5k fans at apogee stadium", "simulate_event", {"venue": "0322", "attendance": 5000}),
    ("if apogee gets 30000 fans saturday what happens to traffic", "simulate_event",
     {"venue": "0322", "attendance": 30000}),
    ("what if the union is closed", "simulate_closure", {"building": "0155"}),
    ("what happens if willis is under construction", "simulate_closure", {"building": "0149"}),
    ("what can you do", "help", {}),
]


@pytest.fixture(scope="module")
def parser() -> Parser:
    return Parser(BUILDINGS)


def _slot_values(slots: dict) -> dict:
    return {k: v["code"] if isinstance(v, dict) else v for k, v in slots.items()}


@pytest.mark.parametrize("question,intent,expected", SAMPLES, ids=[s[0] for s in SAMPLES])
def test_sample_questions(parser, question, intent, expected):
    result = parser.parse(question, now=TUESDAY)
    assert result.intent == intent
    actual = _slot_values(result.slots)
    assert {k: actual.get(k) for k in expected} == expected


def test_every_intent_has_a_sample():
    covered = {intent for _, intent, _ in SAMPLES}
    assert covered == {i.name for i in INTENTS}


def test_unrecognized_question_offers_suggestions(parser):
    result = parser.parse("hello there")
    assert result.intent == "unknown"
    assert not result.complete
    assert len(result.suggestions) >= 2


def test_missing_parameter_asks_follow_up(parser):
    result = parser.parse("directions to the rec")
    assert result.intent == "route"
    assert result.missing == ["origin"]
    assert result.follow_up == "Where are you starting from?"


def test_follow_up_answer_fills_missing_slot(parser):
    first = parser.parse("how do I get to Willis Library").to_dict()
    second = parser.parse("the union", pending=first)
    assert second.intent == "route"
    assert second.complete
    assert _slot_values(second.slots) == {"origin": "0155", "destination": "0149"}


def test_simulation_asks_for_crowd_size(parser):
    first = parser.parse("simulate an event at the coliseum")
    assert first.intent == "simulate_event"
    assert first.missing == ["attendance"]
    second = parser.parse("about 8000", pending=first.to_dict())
    assert second.complete
    assert second.slots["attendance"] == 8000


def test_new_question_overrides_pending(parser):
    pending = parser.parse("how do I get to Willis Library").to_dict()
    result = parser.parse("how busy is the coliseum", pending=pending)
    assert result.intent == "occupancy"


def test_pending_with_unknown_building_is_ignored(parser):
    pending = {"intent": "route", "slots": {"destination": {"code": "9999", "name": "Fake"}},
               "missing": ["origin"]}
    result = parser.parse("the union", pending=pending)
    assert "9999" not in str(result.slots)


def test_union_does_not_match_union_circle_garage(parser):
    result = parser.parse("where is union circle garage")
    assert result.slots["building"]["code"] == "0001"


@pytest.mark.parametrize("text,expected", [
    ("1pm", "13:00"), ("1:30 p.m.", "13:30"), ("12 am", "00:00"), ("12pm", "12:00"),
    ("at 14:45", "14:45"), ("noon", "12:00"), ("no time here", None),
])
def test_find_time(text, expected):
    assert find_time(text)[0] == expected


def test_counts_ignore_lot_and_building_numbers():
    attendance, numbers = find_counts("park in lot 20 near building 155 for 300 guests")
    assert attendance == 300
    assert numbers == []


def test_ask_endpoint():
    client = create_app(BuildingIndex(BUILDINGS)).test_client()
    response = client.post("/api/ask", json={"text": "where is willis library"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["intent"] == "locate"
    assert body["complete"] is True


@pytest.mark.parametrize("payload", [{}, {"text": ""}, {"text": 5}, {"text": "a" * 301}])
def test_ask_endpoint_rejects_bad_input(payload):
    client = create_app(BuildingIndex(BUILDINGS)).test_client()
    assert client.post("/api/ask", json=payload).status_code == 400
