from __future__ import annotations

import json
from pathlib import Path

import pytest

from storepagelint.core import FAIL, FOLD, NOTE, WARN, Page, check, find_terms, normalise
from storepagelint.vocabulary import all_genre_terms


def levels(findings, rule):
    return [f.level for f in findings if f.rule == rule]


def test_normalise_folds_case_and_punctuation():
    assert normalise("Deck-Builder,  ROLL!") == "deck builder roll"


def test_find_terms_gives_the_family_and_the_place():
    hits = find_terms("A tense extraction shooter for two", all_genre_terms())
    assert hits[0][0] == "extraction shooter"
    assert hits[0][2] == "survival and horror"
    assert hits[0][1] > 0


def test_find_terms_takes_the_longest_match_only():
    hits = find_terms("a roguelike deck builder", all_genre_terms())
    assert sorted(term for term, _, _ in hits) == ["deck builder", "roguelike"]


def test_a_page_that_names_its_genre_early_passes_the_hard_rules():
    page = Page(
        name="Dice Academy",
        short_description=(
            "A dice game about spell schools: you roll five dice, lock the ones you want, and the hand "
            "you finish becomes the spell you cast."
        ),
        long_description="A dice game with a deck builder run structure.",
        tags=["dice game", "deck builder"],
    )
    findings = check(page)
    assert not [f for f in findings if f.level == FAIL], [f.line() for f in findings]
    assert levels(findings, "genre-above-the-fold") == [NOTE]


def test_a_page_with_no_genre_word_fails_above_the_fold():
    page = Page(
        short_description="Gems glow in the vaults of the academy and the masters are watching you.",
        tags=["dice game"],
    )
    findings = check(page)
    assert levels(findings, "genre-above-the-fold") == [FAIL]
    assert levels(findings, "tags-never-said") == [WARN]


def test_a_genre_word_after_the_fold_still_fails_above_the_fold():
    filler = "The academy is old and its halls are long. " * 4
    assert len(filler) > FOLD
    page = Page(short_description=filler + "It is a dice game.")
    findings = check(page)
    assert levels(findings, "genre-above-the-fold") == [FAIL]


def test_a_comparison_alone_is_a_hard_finding():
    page = Page(short_description="It is like Hollow Vaults, but with friends.")
    findings = check(page)
    assert levels(findings, "comparison-only") == [FAIL]


def test_a_comparison_is_only_a_note_when_the_text_names_a_genre_somewhere():
    page = Page(short_description="A deck builder like Hollow Vaults, where you draft one card a turn.")
    findings = check(page)
    assert levels(findings, "comparison-only") == [NOTE]


def test_filler_words_are_named_back():
    page = Page(short_description="A unique and immersive dice game where you roll to cast.")
    findings = check(page)
    assert levels(findings, "filler-words") == [WARN]
    message = [f.message for f in findings if f.rule == "filler-words"][0]
    assert "'unique'" in message and "'immersive'" in message


def test_three_unrelated_families_are_reported():
    page = Page(
        short_description="A dice game, a racing game and a visual novel where you roll to move.",
        tags=[],
    )
    findings = check(page)
    assert levels(findings, "genre-families") == [WARN]


def test_two_families_are_not_reported():
    page = Page(short_description="A roguelike deck builder where you draft a card each turn.")
    findings = check(page)
    assert levels(findings, "genre-families") == []


def test_a_missing_player_verb_is_reported():
    page = Page(short_description="A dice game set in an academy of magic.")
    findings = check(page)
    assert levels(findings, "player-verb") == [WARN]


def test_an_over_long_short_description_is_reported():
    page = Page(short_description="A dice game where you roll. " * 20)
    findings = check(page)
    assert levels(findings, "short-description-length") == [WARN]


def test_an_empty_short_description_fails():
    findings = check(Page())
    assert levels(findings, "short-description-present") == [FAIL]


def test_findings_are_sorted_hard_first():
    page = Page(short_description="Gems glow, unique and immersive.", tags=["dice game"])
    findings = check(page)
    assert findings[0].level == FAIL


def test_a_page_reads_from_json(tmp_path: Path):
    path = tmp_path / "page.json"
    path.write_text(
        json.dumps({"name": "X", "short_description": "A dice game.", "tags": ["dice game"]}),
        encoding="utf-8",
    )
    page = Page.from_file(path)
    assert page.name == "X"
    assert page.tags == ["dice game"]


def test_an_unknown_field_is_refused(tmp_path: Path):
    path = tmp_path / "page.json"
    path.write_text(json.dumps({"shortdescription": "typo"}), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown field"):
        Page.from_file(path)


def test_tags_must_be_a_list_of_strings(tmp_path: Path):
    path = tmp_path / "page.json"
    path.write_text(json.dumps({"tags": [1, 2]}), encoding="utf-8")
    with pytest.raises(ValueError, match="tags must be"):
        Page.from_file(path)
