"""The page, the findings and the rules.

One idea holds the whole tool: a page is read left to right by someone who will leave in a few
seconds, so every finding says **where** in the text something is, or where it is missing. Nothing
here judges whether a game is appealing. That question is not in the text and the tool does not
pretend to answer it.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .vocabulary import all_genre_terms, filler_words, genre_families, player_verbs

# A first glance budget chosen by this tool, not a limit measured on any store. Where a store cuts a
# short description depends on the surface it is shown on, so no single number is true everywhere.
# Change it with --fold.
FOLD = 140
SHORT_LIMIT = 300  # characters a store short description usually accepts

FAIL, WARN, NOTE = "fail", "warn", "note"


@dataclass
class Finding:
    rule: str
    level: str
    message: str
    where: str = ""
    at: int | None = None

    def line(self) -> str:
        place = ""
        if self.where:
            place = f" [{self.where}" + (f" at character {self.at}" if self.at is not None else "") + "]"
        return f"{self.level.upper():4} {self.rule}: {self.message}{place}"


@dataclass
class Page:
    name: str = ""
    short_description: str = ""
    long_description: str = ""
    tags: list[str] = field(default_factory=list)
    fold: int = FOLD

    @property
    def text(self) -> str:
        return f"{self.short_description}\n{self.long_description}"

    @classmethod
    def from_file(cls, path: Path) -> "Page":
        raw = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".toml":
            data = _load_toml(raw, path)
        else:
            data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError(f"{path}: the page file must hold an object of fields")
        unknown = sorted(set(data) - {"name", "short_description", "long_description", "tags"})
        if unknown:
            raise ValueError(f"{path}: unknown field(s) {unknown}")
        tags = data.get("tags") or []
        if not isinstance(tags, list) or any(not isinstance(t, str) for t in tags):
            raise ValueError(f"{path}: tags must be a list of strings")
        return cls(
            name=str(data.get("name") or ""),
            short_description=str(data.get("short_description") or ""),
            long_description=str(data.get("long_description") or ""),
            tags=[str(t) for t in tags],
        )


def _load_toml(raw: str, path: Path) -> dict:
    try:
        import tomllib
    except ModuleNotFoundError as exc:  # Python 3.10 and older
        raise ValueError(
            f"{path}: reading TOML needs Python 3.11 or newer, write the page as .json instead"
        ) from exc
    return tomllib.loads(raw)


def normalise(text: str) -> str:
    """Lower case, punctuation to spaces, single spaces. Used on both sides of every comparison."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def find_terms(text: str, terms: dict[str, str] | tuple[str, ...]) -> list[tuple[str, int, str]]:
    """Return (term, position in the normalised text, family or "") for every term present."""
    flat = normalise(text)
    padded = f" {flat} "
    out = []
    taken: list[tuple[int, int]] = []
    items = terms.items() if isinstance(terms, dict) else ((t, "") for t in terms)
    for term, family in items:
        needle = f" {normalise(term)} "
        start = padded.find(needle)
        while start != -1:
            span = (start, start + len(needle))
            if not any(a <= span[0] and span[1] <= b for a, b in taken):
                taken.append(span)
                out.append((normalise(term), start, family))
            start = padded.find(needle, start + 1)
    out.sort(key=lambda item: item[1])
    return out


# --- rules -------------------------------------------------------------------------------------

Rule = Callable[[Page], list[Finding]]
_RULES: list[tuple[str, Rule]] = []


def rule(name: str) -> Callable[[Rule], Rule]:
    def wrap(func: Rule) -> Rule:
        _RULES.append((name, func))
        return func

    return wrap


@rule("short-description-present")
def _present(page: Page) -> list[Finding]:
    if page.short_description.strip():
        return []
    return [Finding("short-description-present", FAIL, "the short description is empty")]


@rule("genre-above-the-fold")
def _above_fold(page: Page) -> list[Finding]:
    fold = page.fold
    head = page.short_description[:fold]
    hits = find_terms(head, all_genre_terms())
    if hits:
        term, at, family = hits[0]
        return [
            Finding(
                "genre-above-the-fold",
                NOTE,
                f"a reader meets the word {term!r} ({family}) in the first {fold} characters",
                "short_description",
                at,
            )
        ]
    return [
        Finding(
            "genre-above-the-fold",
            FAIL,
            f"no genre word in the first {fold} characters, the first glance budget",
            "short_description",
            0,
        )
    ]


@rule("genre-in-first-sentence")
def _first_sentence(page: Page) -> list[Finding]:
    first = re.split(r"(?<=[.!?])\s", page.short_description.strip(), maxsplit=1)[0]
    if not first:
        return []
    if find_terms(first, all_genre_terms()):
        return []
    return [
        Finding(
            "genre-in-first-sentence",
            WARN,
            "the first sentence names no genre, so the genre arrives late or not at all",
            "short_description",
            0,
        )
    ]


@rule("tags-never-said")
def _tags_said(page: Page) -> list[Finding]:
    """Only tags that carry a genre are checked.

    A tag like 'atmospheric' or 'great soundtrack' is picked from a closed list and nobody writes it
    in a sentence, so asking for it in the text would be noise on every real page.
    """
    text = normalise(page.text)
    terms = all_genre_terms()
    carries_genre = [tag for tag in page.tags if find_terms(tag, terms)]
    missing = [tag for tag in carries_genre if normalise(tag) not in text]
    if not missing:
        return []
    return [
        Finding(
            "tags-never-said",
            WARN,
            "genre tag(s) never written in the text a reader reads: "
            + ", ".join(repr(t) for t in missing),
            "tags",
        )
    ]


@rule("genre-families")
def _families(page: Page) -> list[Finding]:
    found = {family for _, _, family in find_terms(page.text, all_genre_terms()) if family}
    for tag in page.tags:
        found.update(family for _, _, family in find_terms(tag, all_genre_terms()) if family)
    if len(found) <= 2:
        return []
    return [
        Finding(
            "genre-families",
            WARN,
            f"a reader is offered {len(found)} unrelated genre families: " + ", ".join(sorted(found)),
            "page",
        )
    ]


@rule("comparison-only")
def _comparison(page: Page) -> list[Finding]:
    pattern = re.compile(r"\b(?:like|meets|inspired by|in the vein of)\s+([A-Z][\w'’]+(?:\s+[A-Z][\w'’]+)*)")
    comparisons = pattern.findall(page.short_description)
    if not comparisons:
        return []
    level = FAIL if not find_terms(page.short_description, all_genre_terms()) else NOTE
    message = "the short description leans on a comparison: " + ", ".join(repr(c) for c in comparisons)
    if level == FAIL:
        message += "; a reader who does not know it learns nothing"
    return [Finding("comparison-only", level, message, "short_description")]


@rule("filler-words")
def _filler(page: Page) -> list[Finding]:
    hits = find_terms(page.short_description, filler_words())
    # A filler word inside a genre term is not filler: 'immersive sim' is a genre, 'immersive' is not.
    genre_spans = [
        (at, at + len(term) + 2) for term, at, _ in find_terms(page.short_description, all_genre_terms())
    ]
    hits = [h for h in hits if not any(a <= h[1] and h[1] + len(h[0]) + 2 <= b for a, b in genre_spans)]
    if not hits:
        return []
    return [
        Finding(
            "filler-words",
            WARN,
            "word(s) that would fit any page: " + ", ".join(repr(t) for t, _, _ in hits),
            "short_description",
            hits[0][1],
        )
    ]


@rule("player-verb")
def _verb(page: Page) -> list[Finding]:
    if find_terms(page.short_description, player_verbs()):
        return []
    return [
        Finding(
            "player-verb",
            WARN,
            "the short description never names a thing the player does with their hands",
            "short_description",
        )
    ]


@rule("short-description-length")
def _length(page: Page) -> list[Finding]:
    size = len(page.short_description)
    if size <= SHORT_LIMIT:
        return []
    return [
        Finding(
            "short-description-length",
            WARN,
            f"{size} characters, over the {SHORT_LIMIT} a store short description usually takes",
            "short_description",
            SHORT_LIMIT,
        )
    ]


def rules() -> list[str]:
    return [name for name, _ in _RULES]


def check(page: Page) -> list[Finding]:
    out: list[Finding] = []
    for _, func in _RULES:
        out.extend(func(page))
    order = {FAIL: 0, WARN: 1, NOTE: 2}
    out.sort(key=lambda f: (order.get(f.level, 3), f.rule))
    return out


def as_dict(page: Page, findings: list[Finding]) -> dict[str, Any]:
    return {
        "name": page.name,
        "fold": page.fold,
        "counts": {level: sum(1 for f in findings if f.level == level) for level in (FAIL, WARN, NOTE)},
        "findings": [
            {"rule": f.rule, "level": f.level, "message": f.message, "where": f.where, "at": f.at}
            for f in findings
        ],
        "families_known": sorted(genre_families()),
    }
