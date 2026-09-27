from __future__ import annotations

import json
from pathlib import Path

from storepagelint.cli import EXIT_FAIL, EXIT_OK, EXIT_USAGE, main


def page_file(tmp_path: Path, **fields) -> Path:
    path = tmp_path / "page.json"
    path.write_text(json.dumps(fields), encoding="utf-8")
    return path


def test_a_clean_page_exits_zero(tmp_path: Path, capsys):
    path = page_file(
        tmp_path,
        name="Dice Academy",
        short_description="A dice game where you roll five dice and the hand you finish casts a spell.",
        tags=["dice game"],
    )
    assert main([str(path)]) == EXIT_OK
    out = capsys.readouterr().out
    assert "Dice Academy" in out
    assert "0 to fix" in out


def test_a_page_without_a_genre_word_exits_three(tmp_path: Path, capsys):
    path = page_file(tmp_path, short_description="Gems glow in the vaults of the old academy.")
    assert main([str(path)]) == EXIT_FAIL
    out = capsys.readouterr().out
    assert "genre-above-the-fold" in out
    assert "FAIL" in out


def test_json_output_is_machine_readable(tmp_path: Path, capsys):
    path = page_file(tmp_path, short_description="Gems glow.", tags=["dice game"])
    main([str(path), "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["counts"]["fail"] >= 1
    assert any(f["rule"] == "tags-never-said" for f in data["findings"])
    assert data["fold"] == 140


def test_init_prints_a_page_file_that_reads_back(tmp_path: Path, capsys):
    assert main(["--init"]) == EXIT_OK
    text = capsys.readouterr().out
    assert set(json.loads(text)) == {"name", "short_description", "long_description", "tags"}


def test_list_rules_prints_every_rule(capsys):
    assert main(["--list-rules"]) == EXIT_OK
    names = capsys.readouterr().out.split()
    assert "genre-above-the-fold" in names
    assert len(names) >= 8


def test_no_argument_is_a_usage_error(capsys):
    assert main([]) == EXIT_USAGE
    assert "--init" in capsys.readouterr().err


def test_a_missing_file_is_a_usage_error(tmp_path: Path, capsys):
    assert main([str(tmp_path / "nope.json")]) == EXIT_USAGE
    assert "no such file" in capsys.readouterr().err


def test_broken_json_is_a_usage_error_not_a_crash(tmp_path: Path, capsys):
    path = tmp_path / "page.json"
    path.write_text("{not json", encoding="utf-8")
    assert main([str(path)]) == EXIT_USAGE
    assert "storepagelint:" in capsys.readouterr().err
