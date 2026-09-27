"""Word lists used by the rules.

Every list here is written by hand for this tool. None of it is taken from a store, a platform or a
third party taxonomy: these are ordinary English nouns and adjectives, grouped by hand. The lists are
short on purpose, and they are the first thing to extend for your own page: pass `--vocabulary my.json`
holding any of the keys `genre_families`, `filler_words`, `player_verbs`.
"""

from __future__ import annotations

# Genre nouns a reader recognises without being told. Grouped by hand into families, so a page can be
# told "a reader sees three unrelated families here".
GENRE_FAMILIES: dict[str, tuple[str, ...]] = {
    "action": (
        "shooter",
        "first person shooter",
        "third person shooter",
        "twin stick shooter",
        "shoot em up",
        "beat em up",
        "brawler",
        "bullet hell",
        "hack and slash",
        "platformer",
        "puzzle platformer",
        "metroidvania",
        "fighting game",
        "arcade game",
        "battle royale",
        "souls like",
        "moba",
    ),
    "strategy": (
        "strategy game",
        "real time strategy",
        "turn based strategy",
        "tactics game",
        "tower defence",
        "tower defense",
        "auto battler",
        "city builder",
        "colony sim",
        "wargame",
        "4x",
        "four x game",
    ),
    "puzzle": (
        "puzzle game",
        "match three",
        "sokoban",
        "word game",
        "logic game",
        "escape room",
        "physics puzzle",
    ),
    "cards and dice": (
        "card game",
        "deck builder",
        "deckbuilder",
        "dice game",
        "board game",
        "solitaire",
        "poker",
    ),
    "role playing": (
        "role playing game",
        "rpg",
        "jrpg",
        "crpg",
        "dungeon crawler",
        "roguelike",
        "roguelite",
        "party based rpg",
    ),
    "simulation": (
        "simulator",
        "management game",
        "tycoon game",
        "farming sim",
        "life sim",
        "driving sim",
        "flight sim",
        "idle game",
        "clicker",
        "incremental game",
        "immersive sim",
    ),
    "sandbox": (
        "sandbox game",
        "open world",
        "voxel builder",
        "creative builder",
        "physics sandbox",
    ),
    "cozy": (
        "cozy game",
        "wholesome game",
        "slice of life game",
    ),
    "narrative": (
        "visual novel",
        "adventure game",
        "point and click",
        "interactive fiction",
        "walking simulator",
        "detective game",
        "mystery game",
    ),
    "survival and horror": (
        "survival game",
        "survival horror",
        "horror game",
        "extraction shooter",
        "crafting game",
        "open world survival",
    ),
    "sport and racing": (
        "racing game",
        "sports game",
        "football game",
        "golf game",
        "skating game",
        "management sim",
    ),
    "rhythm": ("rhythm game", "music game", "typing game"),
}

# Adjectives that say nothing about what the player does. A page made of these reads the same as any
# other page.
FILLER_WORDS: tuple[str, ...] = (
    "unique",
    "immersive",
    "epic",
    "addictive",
    "innovative",
    "stunning",
    "breathtaking",
    "unforgettable",
    "revolutionary",
    "next level",
    "fun for everyone",
    "like never before",
    "endless possibilities",
)

# Second person verbs that name a thing the player does with their hands.
PLAYER_VERBS: tuple[str, ...] = (
    "you build",
    "you roll",
    "you draft",
    "you draw",
    "you place",
    "you shoot",
    "you dodge",
    "you solve",
    "you explore",
    "you command",
    "you manage",
    "you race",
    "you farm",
    "you craft",
    "you trade",
    "you fight",
    "you sneak",
    "you jump",
    "you stack",
    "you choose",
    "roll",
    "draft",
    "deploy",
    "build",
    "solve",
    "command",
)


_ACTIVE: dict[str, object] = {
    "genre_families": GENRE_FAMILIES,
    "filler_words": FILLER_WORDS,
    "player_verbs": PLAYER_VERBS,
}

_KEYS = tuple(_ACTIVE)


def genre_families() -> dict[str, tuple[str, ...]]:
    return _ACTIVE["genre_families"]  # type: ignore[return-value]


def filler_words() -> tuple[str, ...]:
    return _ACTIVE["filler_words"]  # type: ignore[return-value]


def player_verbs() -> tuple[str, ...]:
    return _ACTIVE["player_verbs"]  # type: ignore[return-value]


def all_genre_terms() -> dict[str, str]:
    """term -> family, longest terms first so that the longest match wins."""
    pairs = [(term, family) for family, terms in genre_families().items() for term in terms]
    pairs.sort(key=lambda p: -len(p[0]))
    return dict(pairs)


def load(data: dict) -> None:
    """Replace one or more word lists for this run. Unknown keys are refused, nothing is merged.

    A key starting with an underscore is a comment and is ignored, because JSON has no comments and a
    word list is a file people annotate.
    """
    data = {key: value for key, value in data.items() if not key.startswith("_")}
    unknown = sorted(set(data) - set(_KEYS))
    if unknown:
        raise ValueError(f"unknown vocabulary key(s) {unknown}, known keys are {list(_KEYS)}")
    if "genre_families" in data:
        families = data["genre_families"]
        if not isinstance(families, dict) or not all(
            isinstance(k, str) and isinstance(v, list) and all(isinstance(t, str) for t in v)
            for k, v in families.items()
        ):
            raise ValueError("genre_families must map a family name to a list of terms")
        _ACTIVE["genre_families"] = {k: tuple(v) for k, v in families.items()}
    for key in ("filler_words", "player_verbs"):
        if key in data:
            words = data[key]
            if not isinstance(words, list) or any(not isinstance(w, str) for w in words):
                raise ValueError(f"{key} must be a list of strings")
            _ACTIVE[key] = tuple(words)


def reset() -> None:
    _ACTIVE.update(
        genre_families=GENRE_FAMILIES, filler_words=FILLER_WORDS, player_verbs=PLAYER_VERBS
    )
