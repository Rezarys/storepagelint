# storepagelint

The feedback that keeps coming back on a store page is that a reader finishes it and still cannot tell what kind of game it is. This tool reads the copy you wrote and says, rule by rule, where a reader can find the genre and where they cannot. It never says whether the game is appealing. That is not in the text, and no tool can read it there.

```
pip install storepagelint==0.1.0
```

```
storepagelint --init > page.json   # fill in the fields
storepagelint page.json
```

```
storepagelint: Dice Academy
  FAIL genre-above-the-fold: no genre word in the first 140 characters, the first glance budget [short_description at character 0]
  WARN genre-in-first-sentence: the first sentence names no genre, so the genre arrives late or not at all [short_description at character 0]
  WARN player-verb: the short description never names a thing the player does with their hands [short_description]
```

That block is the real output of a run, produced by a test so that it cannot drift from the code. The page it read says "The masters of the old academy are watching, the halls are cold, and your name is not yet written on the wall". It is atmosphere only: a reader gets a mood and no kind of game.

## The rules

- `short-description-present`: there is a short description at all
- `genre-above-the-fold`: a genre word inside the first glance budget, 140 characters by default
- `genre-in-first-sentence`: the first sentence names a genre
- `tags-never-said`: your genre tags appear nowhere in the text a reader reads
- `genre-families`: how many unrelated genre families a reader is offered
- `comparison-only`: "like X" or "meets X", when the short description names no genre at all
- `filler-words`: words that would fit any page
- `player-verb`: a thing the player does with their hands
- `short-description-length`: over the 300 characters a store usually takes

`storepagelint --list-rules` prints them. Exit code is 0, 3 when a `FAIL` is found, and 2 on a usage error such as a missing file or a page file that does not parse. A release checklist should treat 2 as a failure too.

Two of these rules, `filler-words` and `player-verb`, are about clarity of writing rather than genre legibility. They are here because a page made of adjectives says nothing a reader can hold on to, but they are not a judgement on whether the game appeals.

## The 140 is this tool's budget, not a measurement

No store publishes one number at which a short description is cut: where the text ends depends on the surface it is shown on. 140 characters is a first glance budget chosen here, and `--fold N` changes it:

```
storepagelint page.json --fold 200
```

## Its word lists are opinions, not data

The genre words, the families, the filler words and the player verbs are written by hand and live in one file. They are short on purpose. They are not taken from any store, platform or third party list, so they will miss a genre you care about.

That is what `--vocabulary` is for:

```
storepagelint page.json --vocabulary my-words.json
```

```json
{ "genre_families": { "cards and dice": ["dice game", "push your luck"] } }
```

A key you provide **replaces** the shipped list, it is never merged into it, so the file above leaves the tool with exactly two genre words. To extend rather than replace, copy the shipped list out of `vocabulary.py` and add to it. Any of `genre_families`, `filler_words`, `player_verbs` can be replaced. An unknown key is refused rather than ignored. A key starting with an underscore is a comment.

## It reads a local file, and nothing else

No network call, ever. You paste your own copy into `page.json`. The tool does not fetch a store page, does not know your game, and does not send anything anywhere.

## What a FAIL means and does not mean

It means a reader cannot find the information at that place in your text. It does not mean your page is bad or your game is wrong. A reader who finishes the page and cannot name the kind of game is the problem this tool is pointed at; whether the genre itself sells is a different question and this tool stays out of it.

## Price

The tool is free and MIT. A larger vocabulary pack, with more families and more filler words, is priced at 9 EUR. Nothing can be bought today and no payment can be taken: if the pack would be worth it to you, open an issue on the repository and it will be read.

## Install from source

```
git clone https://github.com/Rezarys/storepagelint
cd storepagelint
pip install -e ".[dev]"
python -m pytest
```

## Notes

Built with AI assistance, reviewed and tested by me. The most useful bug report is a real page whose genre is obvious to a reader and that this tool marks FAIL, or the reverse.

MIT, Younes Z.
