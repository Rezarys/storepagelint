"""The sample run printed in README.md is produced here, so it cannot drift from the code."""

from __future__ import annotations

import json
from pathlib import Path

from storepagelint.cli import EXIT_FAIL, main

PAGE = {
    "name": "Dice Academy",
    "short_description": (
        "The masters of the old academy are watching, the halls are cold, and your name is not yet "
        "written on the wall."
    ),
    "long_description": "",
    "tags": [],
}

SAMPLE = """storepagelint: Dice Academy
  FAIL genre-above-the-fold: no genre word in the first 140 characters, the first glance budget [short_description at character 0]
  WARN genre-in-first-sentence: the first sentence names no genre, so the genre arrives late or not at all [short_description at character 0]
  WARN player-verb: the short description never names a thing the player does with their hands [short_description]
  1 to fix, 2 to look at, 0 noted"""


def test_the_readme_sample_is_the_real_output(tmp_path: Path, capsys):
    path = tmp_path / "page.json"
    path.write_text(json.dumps(PAGE), encoding="utf-8")
    code = main([str(path)])
    printed = capsys.readouterr().out.strip()
    assert code == EXIT_FAIL
    assert printed == SAMPLE, printed


def test_the_readme_holds_that_sample():
    """The summary line is left out of the README block on purpose."""
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
    for line in SAMPLE.splitlines()[:4]:
        assert line in readme, line
