"""Pull buildings, times, days, and crowd sizes out of a question.

Only the standard library is used. Fuzzy building matching uses difflib, so
small typos ("Willis Libary") still match without installing anything.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from difflib import get_close_matches
from typing import Iterable, Optional

from buildings import Building


def normalize(text: str) -> str:
    """Lowercase, spell out '&', drop apostrophes, and turn other punctuation into spaces."""
    text = text.lower().replace("&", " and ")
    text = re.sub(r"['’]", "", text)
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


# Words that never start or end a fuzzy building match.
STOPWORDS = frozenset(
    "a an the to from at in on of for and or is are be me my i near by "
    "if what when where how this that it with".split()
)
# Words too vague to stand alone as a building name ("West Hall" -> not "west").
GENERIC_WORDS = frozenset("west east north south general information power university".split())

# Names students actually say, keyed by building code. Codes missing from the
# loaded data are skipped. The team should review and extend this list.
NICKNAMES: dict[str, tuple[str, ...]] = {
    "0155": ("union", "the union", "university union", "student union", "uu"),
    "0149": ("willis", "library", "the library", "willis library"),
    "0113": ("essc", "eagle student services", "eagle student services center"),
    "0108": ("gab", "general academic"),
    "0156": ("blb", "business building", "business leadership"),
    "0160": ("eesat", "eesat building", "environmental science", "environmental science building", "environmental science bldg", "env sci"),
    "0190": ("discovery park", "dp"),
    "0118": ("pohl", "pohl rec", "rec center", "the rec", "rec"),
    "0129": ("pac", "performing arts"),
    "0140": ("rtfp", "rtvf"),
    "0154": ("coliseum", "the coliseum", "super pit", "the pit"),
    "0322": ("apogee", "apogee stadium", "football stadium"),
    "0001": ("union circle garage", "union circle parking", "union circle"),
    "0002": ("highland garage", "highland street garage", "highland parking garage"),
    "0161": ("gateway",),
}

FUZZY_CUTOFF = 0.85
MIN_FUZZY_CHARS = 5
CODE_RE = re.compile(r"^\d{4}$")

# Articles that can be stripped from building aliases.
ARTICLES = frozenset({"a", "an", "the"})

def _strip_articles(alias: str) -> str:
    first, _, rest = alias.partition(" ")
    return rest if first in ARTICLES and rest else alias

def aliases_for_name(name: str) -> set[str]:
    """Derive the ways a building's official name might be typed."""
    base = _strip_articles(normalize(name))
    aliases = {base}
    words = base.split()
    if len(words) > 1 and words[-1] in ("bldg", "building"):
        stem = words[:-1]
        if not (len(stem) == 1 and stem[0] in GENERIC_WORDS):
            aliases.add(" ".join(stem))
        other = "building" if words[-1] == "bldg" else "bldg"
        aliases.add(" ".join(stem + [other]))
    if len(words) == 2 and words[1] == "hall" and words[0] not in GENERIC_WORDS:
        aliases.add(words[0])  # "Kerr Hall" -> "kerr"
    return aliases


@dataclass(frozen=True)
class BuildingMention:
    code: str
    name: str
    start: int  # token index where the mention begins
    end: int  # token index just past the mention
    matched: str  # the alias that matched
    exact: bool

    def to_slot(self) -> dict:
        return {"code": self.code, "name": self.name}


class BuildingMatcher:
    """Find building mentions in a list of normalized tokens."""

    def __init__(self, buildings: Iterable[Building]):
        named = [b for b in buildings if CODE_RE.match(b.code) and b.name]
        self._by_code = {b.code: b for b in named}
        self._alias_to_code: dict[str, str] = {}
        # Official full names win over derived short forms; nicknames win over both.
        for b in named:
            self._alias_to_code.setdefault(_strip_articles(normalize(b.name)), b.code)
        for b in named:
            for alias in aliases_for_name(b.name):
                self._alias_to_code.setdefault(alias, b.code)
        for code, nicknames in NICKNAMES.items():
            if code in self._by_code:
                for alias in nicknames:
                    self._alias_to_code[_strip_articles(normalize(alias))] = code

        self._by_length: dict[int, list[str]] = {}
        for alias in self._alias_to_code:
            if len(alias) >= MIN_FUZZY_CHARS:
                self._by_length.setdefault(len(alias.split()), []).append(alias)
        self._max_len = max((len(a.split()) for a in self._alias_to_code), default=1)

    def get(self, code: str) -> Optional[Building]:
        return self._by_code.get(code)

    def find(self, tokens: list[str]) -> list[BuildingMention]:
        mentions: list[BuildingMention] = []
        i = 0
        while i < len(tokens):
            mention = self._match_at(tokens, i)
            if mention:
                # "the union union" or a split typo should count once.
                if mentions and mentions[-1].code == mention.code and mentions[-1].end == mention.start:
                    prev = mentions.pop()
                    mention = BuildingMention(
                        prev.code, prev.name, prev.start, mention.end, prev.matched, prev.exact
                    )
                mentions.append(mention)
                i = mention.end
            else:
                i += 1
        return mentions

    def _mention(self, code: str, start: int, end: int, matched: str, exact: bool) -> BuildingMention:
        return BuildingMention(code, self._by_code[code].name, start, end, matched, exact)

    def _match_at(self, tokens: list[str], i: int) -> Optional[BuildingMention]:
        # "building 155" or "bldg 0155"
        if tokens[i] in ("building", "bldg") and i + 1 < len(tokens) and tokens[i + 1].isdigit():
            code = tokens[i + 1].zfill(4)
            if code in self._by_code:
                return self._mention(code, i, i + 2, code, True)

        longest = min(self._max_len, len(tokens) - i)
        exact = None
        for length in range(longest, 0, -1):
            phrase = " ".join(tokens[i : i + length])
            code = self._alias_to_code.get(phrase)
            if code:
                exact = self._mention(code, i, i + length, phrase, True)
                break

        # A longer fuzzy match beats a shorter exact one: in "willis libary",
        # "willis library" (fuzzy) should win over "willis" (exact).
        shortest_fuzzy = exact.end - i + 1 if exact else 1
        for length in range(longest, shortest_fuzzy - 1, -1):
            window = tokens[i : i + length]
            if window[0] in STOPWORDS or window[-1] in STOPWORDS:
                continue
            phrase = " ".join(window)
            if len(phrase) < MIN_FUZZY_CHARS:
                continue
            hit = get_close_matches(phrase, self._by_length.get(length, ()), n=1, cutoff=FUZZY_CUTOFF)
            if hit:
                return self._mention(self._alias_to_code[hit[0]], i, i + length, hit[0], False)
        return exact


# ---- times, days, and counts -------------------------------------------------

_TIME_12H = re.compile(r"\b(1[0-2]|0?[1-9])(?::([0-5]\d))?\s*([ap])\.?\s?m\b\.?")
_TIME_24H = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")
_TIME_WORDS = {
    "noon": "12:00", "midnight": "00:00", "morning": "09:00",
    "afternoon": "14:00", "evening": "18:00", "tonight": "19:00",
}
_WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
_DAY_WORDS = {
    **{day: day for day in _WEEKDAYS},
    **{day + "s": day for day in _WEEKDAYS},  # "mondays"
    "mon": "monday", "tue": "tuesday", "tues": "tuesday", "wed": "wednesday",
    "weds": "wednesday", "thu": "thursday", "thur": "thursday",
    "thurs": "thursday", "fri": "friday", "sat": "saturday", "sun": "sunday",
}
_COUNT_RE = re.compile(
    r"(?<![\d:.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(k|thousand)?\b"
    r"(?:[\s-]*(people|persons|person|attendees|fans|students|guests|visitors|spectators))?"
)
# Spans that contain numbers but are not crowd sizes.
_NOT_COUNTS = re.compile(r"\b(?:building|bldg|lot|room|rm)\s*#?\s*[a-z]*\d+\w*")
MIN_LOOSE_COUNT = 20


@dataclass
class Entities:
    tokens: list[str]
    buildings: list[BuildingMention]
    time: Optional[str] = None
    day: Optional[str] = None
    attendance: Optional[int] = None  # a number followed by "people", "fans", etc.
    numbers: list[int] = field(default_factory=list)  # other numbers, as a fallback


def find_time(text: str) -> tuple[Optional[str], str]:
    """Return (HH:MM or None, text with the time blanked out)."""
    lowered = text.lower()
    match = _TIME_12H.search(lowered)
    if match:
        hour = int(match.group(1)) % 12 + (12 if match.group(3) == "p" else 0)
        minute = int(match.group(2) or 0)
        return f"{hour:02d}:{minute:02d}", _blank(lowered, match)
    match = _TIME_24H.search(lowered)
    if match:
        return f"{int(match.group(1)):02d}:{match.group(2)}", _blank(lowered, match)
    for word, value in _TIME_WORDS.items():
        if re.search(rf"\b{word}\b", lowered):
            return value, lowered
    return None, lowered


def find_day(tokens: list[str], now: datetime) -> Optional[str]:
    for token in tokens:
        if token in ("today", "tonight"):
            return _WEEKDAYS[now.weekday()]
        if token == "tomorrow":
            return _WEEKDAYS[(now + timedelta(days=1)).weekday()]
        if token in _DAY_WORDS:
            return _DAY_WORDS[token]
    return None


def find_counts(text: str) -> tuple[Optional[int], list[int]]:
    text = _NOT_COUNTS.sub(" ", text)
    attendance = None
    numbers = []
    for match in _COUNT_RE.finditer(text):
        value = float(match.group(1).replace(",", ""))
        if match.group(2):
            value *= 1000
        if match.group(3) and attendance is None:
            attendance = int(value)
        else:
            numbers.append(int(value))
    return attendance, numbers


def _blank(text: str, match: re.Match) -> str:
    return text[: match.start()] + " " * (match.end() - match.start()) + text[match.end() :]


class EntityExtractor:
    def __init__(self, buildings: Iterable[Building]):
        self.matcher = BuildingMatcher(buildings)

    def extract(self, text: str, now: Optional[datetime] = None) -> Entities:
        now = now or datetime.now()
        time, without_time = find_time(text)
        tokens = normalize(text).split()
        buildings = self.matcher.find(tokens)
        # Building names can contain numbers ("Welch Street Complex 2"); remove
        # them before looking for crowd sizes.
        without_names = without_time
        for mention in buildings:
            without_names = re.sub(rf"\b{re.escape(mention.matched)}\b", " ", without_names)
        attendance, numbers = find_counts(without_names)
        return Entities(
            tokens=tokens,
            buildings=buildings,
            time=time,
            day=find_day(tokens, now),
            attendance=attendance,
            numbers=numbers,
        )
