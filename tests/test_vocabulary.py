from __future__ import annotations

import json
from pathlib import Path

import pytest

from storepagelint import vocabulary
from storepagelint.cli import EXIT_FAIL, EXIT_OK, EXIT_USAGE, main


@pytest.fixture(autouse=True)
def fresh_vocabulary():
    vocabulary.reset()
    yield
    vocabulary.reset()


def test_the_shipped_lists_are_grouped_and_not_empty():
    families = vocabulary.genre_families()
    assert len(families) >= 8
    assert all(terms for terms in families.values())
    assert "deck builder" in vocabulary.all_genre_terms()


def test_every_term_appears_in_one_family_only():
    seen: dict[str, str] = {}
    for family, terms in vocabulary.genre_families().items():
        for term in terms:
            assert term not in seen, f"{term} is in {family} and in {seen.get(term)}"
            seen[term] = family


def test_a_replacement_vocabulary_changes_what_is_found():
    vocabulary.load({"genre_families": {"knitting": ["sock knitter"]}})
    assert vocabulary.all_genre_terms() == {"sock knitter": "knitting"}


def test_a_key_starting_with_an_underscore_is_a_comment():
    vocabulary.load({"_note": "written by hand", "filler_words": ["shiny"]})
    assert vocabulary.filler_words() == ("shiny",)


def test_an_unknown_vocabulary_key_is_refused():
    with pytest.raises(ValueError, match="unknown vocabulary key"):
        vocabulary.load({"genres": {}})


def test_a_badly_shaped_vocabulary_is_refused():
    with pytest.raises(ValueError, match="genre_families must map"):
        vocabulary.load({"genre_families": ["shooter"]})
    with pytest.raises(ValueError, match="filler_words must be"):
        vocabulary.load({"filler_words": {"a": 1}})


def test_the_cli_uses_the_vocabulary_file(tmp_path: Path, capsys):
    page = tmp_path / "page.json"
    page.write_text(
        json.dumps({"short_description": "A sock knitter where you build one stitch a turn."}),
        encoding="utf-8",
    )
    assert main([str(page)]) == EXIT_FAIL  # 'sock knitter' is not in the shipped lists
    capsys.readouterr()

    vocab = tmp_path / "vocab.json"
    vocab.write_text(json.dumps({"genre_families": {"knitting": ["sock knitter"]}}), encoding="utf-8")
    assert main([str(page), "--vocabulary", str(vocab)]) == EXIT_OK


def test_a_missing_vocabulary_file_is_a_usage_error(tmp_path: Path, capsys):
    page = tmp_path / "page.json"
    page.write_text(json.dumps({"short_description": "A dice game where you roll."}), encoding="utf-8")
    assert main([str(page), "--vocabulary", str(tmp_path / "nope.json")]) == EXIT_USAGE
    assert "no such vocabulary file" in capsys.readouterr().err
