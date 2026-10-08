"""Load and validate local FAQ data and find an unambiguous match."""

import json
from pathlib import Path

from .intent import normalize

DEFAULT_FAQ_PATH = Path(__file__).resolve().parents[2] / "data" / "faq.json"


def load_faq(path=None):
    source = Path(path) if path is not None else DEFAULT_FAQ_PATH
    entries = json.loads(source.read_text(encoding="utf-8-sig"))
    if not isinstance(entries, list) or not entries:
        raise ValueError("FAQ must be a non-empty JSON array")
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Each FAQ must be an object")
        for key in ("id", "question", "answer"):
            if not isinstance(entry.get(key), str) or not entry[key].strip():
                raise ValueError(f"FAQ requires a non-empty string: {key}")
        if entry["id"] in seen:
            raise ValueError("Duplicate FAQ id")
        seen.add(entry["id"])
        keywords = entry.get("keywords")
        if not isinstance(keywords, list) or not keywords or any(
            not isinstance(word, str) or not normalize(word) for word in keywords
        ):
            raise ValueError("FAQ keywords must be non-empty strings")
        if len(entry["answer"]) > 2000:
            raise ValueError("FAQ answer is too long")
    return entries


def find_answer(text, entries):
    query = normalize(text)
    if not query:
        return None
    exact = {item["answer"] for item in entries if query == normalize(item["question"])}
    if len(exact) == 1:
        return exact.pop()
    matches = []
    for item in entries:
        score = max((len(normalize(word)) for word in item["keywords"]
                     if normalize(word) in query), default=0)
        if score:
            matches.append((score, item["answer"]))
    if not matches:
        return None
    best = max(score for score, _ in matches)
    answers = {answer for score, answer in matches if score == best}
    # Equal scores with different answers should not arbitrarily choose one.
    return answers.pop() if len(answers) == 1 else None
