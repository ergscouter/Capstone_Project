"""The questions Campus Buddy understands, written as data.

Each intent lists the parameters (slots) it needs, keyword phrases that point
to it, and a question template shown when the parser is unsure. To support a
new kind of question, add an Intent here; the parser does not need to change.

Keyword phrases are matched against the normalized question (lowercase, no
punctuation, apostrophes removed, so "what's" becomes "whats").
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Slot:
    name: str
    kind: str  # "building", "time", "day", or "count"
    prompt: str  # follow-up question when the slot is required but missing


@dataclass(frozen=True)
class Intent:
    name: str
    description: str
    template: str
    keywords: dict[str, float]
    required: tuple[Slot, ...] = ()
    optional: tuple[Slot, ...] = ()
    # Hypothetical intents only score when the question reads as a "what if"
    # (or names a crowd size), so "is the union closed?" stays an hours question.
    hypothetical: bool = False
    examples: tuple[str, ...] = field(default=())

    @property
    def slots(self) -> tuple[Slot, ...]:
        return self.required + self.optional


ORIGIN = Slot("origin", "building", "Where are you starting from?")
DESTINATION = Slot("destination", "building", "Where are you headed?")
BUILDING = Slot("building", "building", "Which building do you mean?")
NEAR = Slot("building", "building", "Near which building?")
VENUE = Slot("venue", "building", "Which venue is the event at?")
ATTENDANCE = Slot("attendance", "count", "About how many people will attend?")
TIME = Slot("time", "time", "What time?")
DAY = Slot("day", "day", "Which day?")

HYPOTHETICAL_MARKERS = (
    "what if",
    "what happens",
    "what would happen",
    "simulate",
    "simulation",
    "suppose",
    "imagine",
    "if",
)

INTENTS: tuple[Intent, ...] = (
    Intent(
        name="route",
        description="Walking route and time between two buildings",
        template="How do I walk from ___ to ___?",
        required=(ORIGIN, DESTINATION),
        optional=(TIME, DAY),
        keywords={
            "route": 3, "directions": 3, "navigate": 3, "get to": 3,
            "get from": 3, "how do i get": 3, "take me": 2, "walk": 2,
            "walking": 2, "fastest": 2, "quickest": 2, "shortest": 2,
            "way to": 2, "distance": 2, "how far": 2.5, "how long": 1.5,
            "go to": 1.5, "head to": 1.5, "from": 1, "minutes": 1,
        },
        examples=(
            "How do I walk from the Union to Willis Library?",
            "Fastest way to Wooten Hall from the GAB",
            "How long does it take to get to the Coliseum?",
        ),
    ),
    Intent(
        name="locate",
        description="Show a building on the map",
        template="Where is ___?",
        required=(BUILDING,),
        keywords={
            "where is": 3, "wheres": 3, "where": 1.5, "locate": 3,
            "located": 3, "find": 2, "show me": 2, "on the map": 2,
        },
        examples=("Where is Sage Hall?", "Show me the BLB on the map"),
    ),
    Intent(
        name="building_info",
        description="Details about a building",
        template="Tell me about ___.",
        required=(BUILDING,),
        keywords={
            "tell me about": 3, "info": 2, "information": 2, "details": 2,
            "history": 2, "named after": 3, "how big": 3, "square feet": 3,
            "size": 2, "what is": 1.5, "whats in": 2, "about": 1,
        },
        examples=("Tell me about Wooten Hall", "How big is the Coliseum?"),
    ),
    Intent(
        name="hours",
        description="Opening hours for a building",
        template="When does ___ open?",
        required=(BUILDING,),
        optional=(DAY,),
        keywords={
            "open": 3, "opens": 3, "close": 2.5, "closes": 3, "closing": 3,
            "closed": 2, "hours": 3, "what time": 1.5,
        },
        examples=("When does Willis Library close?", "Is the Union open Sunday?"),
    ),
    Intent(
        name="occupancy",
        description="How busy a building is",
        template="How busy is ___ at ___?",
        required=(BUILDING,),
        optional=(TIME, DAY),
        keywords={
            "busy": 3, "crowded": 3, "packed": 3, "occupancy": 3,
            "how many people": 3, "full": 1.5,
        },
        examples=("How busy is the Union at noon?", "Is the rec center crowded?"),
    ),
    Intent(
        name="parking",
        description="Where to park",
        template="Where can I park near ___?",
        optional=(NEAR, TIME, DAY),
        keywords={
            "park": 3, "parking": 3, "garage": 2.5, "lot": 2, "permit": 2,
            "spots": 2, "spaces": 1.5,
        },
        examples=("Where can I park near the Coliseum?", "Is there parking by the GAB?"),
    ),
    Intent(
        name="events",
        description="What is happening on campus",
        template="What's happening on campus ___?",
        optional=(NEAR, DAY, TIME),
        keywords={
            "events": 2.5, "event": 2, "happening": 3, "going on": 3,
            "whats on": 2, "game": 1.5, "concert": 1.5,
        },
        examples=("What's happening at the Union tonight?", "Any events Friday?"),
    ),
    Intent(
        name="simulate_event",
        description="Simulate crowds and parking for an event",
        template="What happens if ___ people attend an event at ___?",
        required=(VENUE, ATTENDANCE),
        optional=(DAY, TIME),
        hypothetical=True,
        keywords={
            "simulate": 3, "simulation": 3, "attendance": 3, "attend": 2,
            "what if": 2, "what happens": 2, "what would happen": 2,
            "suppose": 2, "imagine": 2, "crowd": 2, "if": 1, "event": 1,
            "people": 1,
        },
        examples=(
            "What happens to parking if 5000 people attend an event at the Coliseum?",
            "Simulate a 20,000 person game at Apogee",
        ),
    ),
    Intent(
        name="simulate_closure",
        description="Simulate a building or path closure",
        template="What happens if ___ is closed?",
        required=(BUILDING,),
        optional=(DAY, TIME),
        hypothetical=True,
        keywords={
            "closed": 2, "closure": 3, "shut down": 3, "shutdown": 3,
            "blocked": 3, "construction": 3, "detour": 2, "simulate": 2,
            "what if": 2, "what happens": 2, "what would happen": 2, "if": 1,
        },
        examples=("What if the Union is closed?", "Simulate Willis being under construction"),
    ),
    Intent(
        name="help",
        description="What the assistant can do",
        template="What can I ask?",
        keywords={"help": 3, "what can you do": 4, "what can i ask": 4},
    ),
)

INTENTS_BY_NAME = {intent.name: intent for intent in INTENTS}

# Shown when the parser cannot tell what the user wants.
DEFAULT_SUGGESTIONS = ("route", "building_info", "parking", "simulate_event")
