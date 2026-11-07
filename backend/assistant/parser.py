"""Turn a typed question into a structured intent: a name plus parameters.

    parse("fastest walk from the union to willis at 1pm thursday")
    -> intent="route", slots={origin: 0155, destination: 0149, time: "13:00", day: "thursday"}

The result does not answer the question. Route, simulation, and info code
consume it, the same way they would consume a request from a map button. A
future LLM could produce the same ParseResult, with this parser as the fallback.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Iterable, Optional

from buildings import Building

from .catalog import (
    DEFAULT_SUGGESTIONS,
    HYPOTHETICAL_MARKERS,
    INTENTS,
    INTENTS_BY_NAME,
    Intent,
)
from .entities import Entities, EntityExtractor, MIN_LOOSE_COUNT

FROM_WORDS = frozenset({"from", "leaving", "starting"})
TO_WORDS = frozenset({"to", "toward", "towards", "reach", "into"})
ARTICLES = frozenset({"the", "a", "an"})

# Scores at or above this mean "clearly a new question", even mid-follow-up.
NEW_QUESTION_SCORE = 3.0
# Below this confidence the result carries "did you mean" suggestions.
SUGGEST_BELOW = 0.5


@dataclass
class ParseResult:
    text: str
    intent: str  # an Intent name, or "unknown"
    confidence: float
    slots: dict = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    follow_up: Optional[str] = None
    suggestions: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return self.intent != "unknown" and not self.missing

    def to_dict(self) -> dict:
        return {**asdict(self), "complete": self.complete}


class Parser:
    def __init__(self, buildings: Iterable[Building], intents: Iterable[Intent] = INTENTS):
        self.extractor = EntityExtractor(buildings)
        self.intents = tuple(intents)

    def parse(
        self, text: str, pending: Optional[dict] = None, now: Optional[datetime] = None
    ) -> ParseResult:
        """Parse one message.

        pending is the previous result's to_dict() when it asked a follow-up
        question. If this message looks like an answer to it, its slots are
        filled in instead of starting over.
        """
        entities = self.extractor.extract(text, now)
        ranked = self._rank(entities)
        top_name, top_score = ranked[0]
        second_score = ranked[1][1] if len(ranked) > 1 else 0.0

        previous = self._load_pending(pending)
        if previous and (top_score < NEW_QUESTION_SCORE or top_name == previous[0].name):
            intent, slots, missing = previous
            self._fill(intent, entities, slots, prefer=missing)
            return self._result(text, intent, 1.0, slots, [])

        if top_score <= 0:
            return ParseResult(
                text=text,
                intent="unknown",
                confidence=0.0,
                follow_up="I'm not sure what you're asking. Try one of these:",
                suggestions=[INTENTS_BY_NAME[n].template for n in DEFAULT_SUGGESTIONS],
            )

        confidence = round(min(1.0, top_score / (top_score + second_score)) * min(1.0, top_score / 3), 2)
        intent = INTENTS_BY_NAME[top_name]
        slots: dict = {}
        self._fill(intent, entities, slots, prefer=[])
        suggestions = []
        if confidence < SUGGEST_BELOW:
            suggestions = [INTENTS_BY_NAME[name].template for name, score in ranked[:3] if score > 0]
        return self._result(text, intent, confidence, slots, suggestions)

    # ---- intent scoring ------------------------------------------------------

    def _rank(self, entities: Entities) -> list[tuple[str, float]]:
        padded = f" {' '.join(entities.tokens)} "
        hypothetical = entities.attendance is not None or any(
            f" {marker} " in padded for marker in HYPOTHETICAL_MARKERS
        )
        scores = {}
        for intent in self.intents:
            if intent.hypothetical and not hypothetical:
                scores[intent.name] = 0.0
                continue
            score = sum(w for phrase, w in intent.keywords.items() if f" {phrase} " in padded)
            # Parameters are evidence too: two buildings suggest a route, and a
            # crowd size suggests an event simulation.
            if intent.name == "route" and len(entities.buildings) >= 2:
                score += 2
            if intent.name == "simulate_event" and entities.attendance is not None:
                score += 3
            scores[intent.name] = score
        return sorted(scores.items(), key=lambda item: item[1], reverse=True)

    # ---- slot filling --------------------------------------------------------

    def _fill(self, intent: Intent, entities: Entities, slots: dict, prefer: list[str]) -> None:
        """Copy entities into the intent's slots without overwriting filled ones."""
        building_slots = [s.name for s in intent.slots if s.kind == "building"]
        if building_slots:
            self._fill_buildings(building_slots, entities, slots, prefer)
        for slot in intent.slots:
            if slot.name in slots:
                continue
            if slot.kind == "time" and entities.time:
                slots[slot.name] = entities.time
            elif slot.kind == "day" and entities.day:
                slots[slot.name] = entities.day
            elif slot.kind == "count":
                count = entities.attendance
                if count is None:
                    loose = [n for n in entities.numbers if n >= MIN_LOOSE_COUNT]
                    count = max(loose) if loose else None
                if count is not None:
                    slots[slot.name] = count

    def _fill_buildings(
        self, names: list[str], entities: Entities, slots: dict, prefer: list[str]
    ) -> None:
        tokens = entities.tokens
        unmarked = []
        for mention in entities.buildings:
            j = mention.start - 1
            while j >= 0 and tokens[j] in ARTICLES:  # "from the union"
                j -= 1
            before = tokens[j] if j >= 0 else ""
            if before in FROM_WORDS and "origin" in names and "origin" not in slots:
                slots["origin"] = mention.to_slot()
            elif before in TO_WORDS and "destination" in names and "destination" not in slots:
                slots["destination"] = mention.to_slot()
            else:
                unmarked.append(mention)

        empty = [n for n in prefer if n in names and n not in slots]
        empty += [n for n in names if n not in slots and n not in empty]
        # One unmarked building in a route question is where you're going
        # ("how do I get to Willis"); two are taken in order ("Union to Willis"
        # is caught above, "between the Union and Willis" lands here).
        if not prefer and len(unmarked) < len(empty) and "destination" in empty:
            empty.remove("destination")
            empty.insert(0, "destination")
        for name, mention in zip(empty, unmarked):
            slots[name] = mention.to_slot()

    # ---- helpers -------------------------------------------------------------

    def _result(
        self, text: str, intent: Intent, confidence: float, slots: dict, suggestions: list[str]
    ) -> ParseResult:
        missing = [s.name for s in intent.required if s.name not in slots]
        follow_up = next((s.prompt for s in intent.required if s.name in missing), None)
        return ParseResult(
            text=text,
            intent=intent.name,
            confidence=confidence,
            slots=slots,
            missing=missing,
            follow_up=follow_up,
            suggestions=suggestions,
        )

    def _load_pending(self, pending: Optional[dict]) -> Optional[tuple[Intent, dict, list[str]]]:
        """Validate a previous result sent back by the client. Returns None if unusable."""
        if not isinstance(pending, dict):
            return None
        intent = INTENTS_BY_NAME.get(pending.get("intent"))
        missing = pending.get("missing")
        if intent is None or not isinstance(missing, list) or not missing:
            return None
        raw_slots = pending.get("slots") if isinstance(pending.get("slots"), dict) else {}
        slots: dict = {}
        # Rebuild each slot from trusted data instead of echoing client values.
        for slot in intent.slots:
            value = raw_slots.get(slot.name)
            if slot.kind == "building" and isinstance(value, dict):
                building = self.extractor.matcher.get(str(value.get("code", "")))
                if building:
                    slots[slot.name] = {"code": building.code, "name": building.name}
            elif slot.kind == "count" and isinstance(value, int) and value > 0:
                slots[slot.name] = value
            elif slot.kind in ("time", "day") and isinstance(value, str) and len(value) <= 10:
                slots[slot.name] = value
        missing = [s.name for s in intent.required if s.name not in slots]
        return (intent, slots, missing) if missing else None
