"""Command line entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import vocabulary
from .core import FAIL, NOTE, WARN, Page, as_dict, check, rules

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_FAIL = 3

TEMPLATE = """{
  "name": "Your game",
  "short_description": "",
  "long_description": "",
  "tags": []
}
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="storepagelint",
        description=(
            "Read the copy of a game store page from a local file and say, rule by rule, where a "
            "reader can find the genre and where they cannot. It never says whether the game is "
            "appealing: that is not in the text."
        ),
    )
    parser.add_argument("page", nargs="?", help="a .json or .toml file holding the page copy")
    parser.add_argument("--json", action="store_true", help="print the findings as JSON")
    parser.add_argument(
        "--fold",
        type=int,
        default=None,
        help="first glance budget in characters (default: 140), the window the genre must appear in",
    )
    parser.add_argument("--init", action="store_true", help="print an empty page file and exit")
    parser.add_argument("--list-rules", action="store_true", help="print the rule names and exit")
    parser.add_argument(
        "--vocabulary",
        help="a .json file replacing any of genre_families, filler_words, player_verbs",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.init:
        print(TEMPLATE, end="")
        return EXIT_OK
    if args.list_rules:
        for name in rules():
            print(name)
        return EXIT_OK
    if not args.page:
        print("storepagelint: give a page file, or --init to print an empty one", file=sys.stderr)
        return EXIT_USAGE

    if args.vocabulary:
        vocab_path = Path(args.vocabulary)
        if not vocab_path.is_file():
            print(f"storepagelint: no such vocabulary file: {vocab_path}", file=sys.stderr)
            return EXIT_USAGE
        try:
            vocabulary.load(json.loads(vocab_path.read_text(encoding="utf-8")))
        except Exception as exc:
            print(f"storepagelint: {vocab_path}: {exc}", file=sys.stderr)
            return EXIT_USAGE

    path = Path(args.page)
    if not path.is_file():
        print(f"storepagelint: no such file: {path}", file=sys.stderr)
        return EXIT_USAGE
    try:
        page = Page.from_file(path)
    except Exception as exc:
        print(f"storepagelint: {exc}", file=sys.stderr)
        return EXIT_USAGE

    if args.fold is not None:
        if args.fold < 1:
            print("storepagelint: --fold takes a positive number of characters", file=sys.stderr)
            return EXIT_USAGE
        page.fold = args.fold

    findings = check(page)
    if args.json:
        print(json.dumps(as_dict(page, findings), indent=2, ensure_ascii=False))
    else:
        title = page.name or path.name
        print(f"storepagelint: {title}")
        if not findings:
            print("  nothing to report")
        for finding in findings:
            print(f"  {finding.line()}")
        counts = {level: sum(1 for f in findings if f.level == level) for level in (FAIL, WARN, NOTE)}
        print(f"  {counts[FAIL]} to fix, {counts[WARN]} to look at, {counts[NOTE]} noted")
    return EXIT_FAIL if any(f.level == FAIL for f in findings) else EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
