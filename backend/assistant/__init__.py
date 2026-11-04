"""Question parser for Campus Buddy: text in, structured intent out. No model downloads."""

from .catalog import INTENTS, INTENTS_BY_NAME, Intent, Slot
from .parser import ParseResult, Parser

__all__ = ["INTENTS", "INTENTS_BY_NAME", "Intent", "Slot", "ParseResult", "Parser"]
