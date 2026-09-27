"""The two rules the first review found soft: the fold budget and which tags are checked."""

from __future__ import annotations

import json
from pathlib import Path

from storepagelint.cli import EXIT_FAIL, EXIT_OK, EXIT_USAGE, main
from storepagelint.core import FAIL, NOTE, WARN, Page, check

LATE = "The masters of the old academy are watching and the halls are cold today. " * 2


def levels(findings, rule):
    return [f.level for f in findings if f.rule == rule]


def test_the_fold_is_a_setting_not_a_constant():
    page = Page(short_description=LATE + "It is a dice game.")
    assert levels(check(page), "genre-above-the-fold") == [FAIL]
    page.fold = 400
    assert levels(check(page), "genre-above-the-fold") == [NOTE]


def test_the_message_says_the_budget_it_used():
    page = Page(short_description=LATE + "It is a dice game.", fold=50)
    message = [f.message for f in check(page) if f.rule == "genre-above-the-fold"][0]
    assert "first 50 characters" in message
    assert "search result" not in message


def test_the_cli_passes_the_fold_through(tmp_path: Path, capsys):
    path = tmp_path / "page.json"
    path.write_text(json.dumps({"short_description": LATE + "It is a dice game."}), encoding="utf-8")
    assert main([str(path)]) == EXIT_FAIL
    capsys.readouterr()
    assert main([str(path), "--fold", "400"]) == EXIT_OK


def test_a_fold_of_zero_is_a_usage_error(tmp_path: Path, capsys):
    path = tmp_path / "page.json"
    path.write_text(json.dumps({"short_description": "A dice game where you roll."}), encoding="utf-8")
    assert main([str(path), "--fold", "0"]) == EXIT_USAGE
    assert "positive number" in capsys.readouterr().err


def test_a_tag_that_carries_no_genre_is_not_asked_for():
    page = Page(
        short_description="A dice game where you roll to cast.",
        tags=["atmospheric", "great soundtrack", "singleplayer"],
    )
    assert levels(check(page), "tags-never-said") == []


def test_a_genre_tag_missing_from_the_text_is_reported():
    page = Page(short_description="A dice game where you roll to cast.", tags=["deck builder"])
    assert levels(check(page), "tags-never-said") == [WARN]
    message = [f.message for f in check(page) if f.rule == "tags-never-said"][0]
    assert "genre tag(s)" in message
    assert "deck builder" in message


def test_a_filler_word_inside_a_genre_term_is_not_filler():
    page = Page(short_description="An immersive sim where you sneak through one building.")
    assert levels(check(page), "filler-words") == []


def test_the_filler_rule_still_catches_the_word_on_its_own():
    page = Page(short_description="An immersive dice game where you roll.")
    assert levels(check(page), "filler-words") == [WARN]


def test_the_summary_line_separates_notes_from_warnings(tmp_path: Path, capsys):
    path = tmp_path / "page.json"
    path.write_text(
        json.dumps({"short_description": "A dice game where you roll five dice and cast a spell."}),
        encoding="utf-8",
    )
    assert main([str(path)]) == EXIT_OK
    assert "0 to fix, 0 to look at, 1 noted" in capsys.readouterr().out
