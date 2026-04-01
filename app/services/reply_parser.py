import re
from dataclasses import dataclass


AUTO_REPLY_PATTERNS = ["automatic reply", "out of office", "autoreply", "auto-reply"]


@dataclass
class ParseResult:
    command: str | None
    note: str | None
    ambiguous: bool = False
    ignored: bool = False


class ReplyParser:
    def __init__(self):
        self.command_keywords = {
            "complete": {"done", "completed", "complete", "finished"},
            "skip": {"skip", "skipped"},
            "defer": {"defer", "deferred"},
        }

    def parse(self, subject: str, body_text: str) -> ParseResult:
        combined = f"{subject}\n{body_text}".strip().lower()
        if any(p in combined for p in AUTO_REPLY_PATTERNS):
            return ParseResult(command=None, note=None, ignored=True)

        lines = [ln.strip() for ln in body_text.splitlines() if ln.strip()]
        if not lines:
            return ParseResult(command=None, note=None, ambiguous=True)

        first = lines[0].lower()
        tokens = re.split(r"\s+", first)
        cmd = tokens[0]
        note = " ".join(tokens[1:]) if len(tokens) > 1 else None
        for normalized, keywords in self.command_keywords.items():
            if cmd in keywords:
                return ParseResult(command=normalized, note=note, ambiguous=False)
        return ParseResult(command=None, note=first, ambiguous=True)
