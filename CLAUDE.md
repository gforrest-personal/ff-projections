# CLAUDE.md

Guidance for Claude Code when working in this repo.

## What this is

A Python tool that pulls half-PPR season projections from Sleeper, ESPN, and
Yahoo, averages them per player, and writes a draft board to
`output/fantasy_draft_board.xlsx`. It's built for pre-draft use; see README.md
for the user-facing docs.

## Commands

Run everything from the repo root inside the virtual environment:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                            # the user fills in YAHOO_LEAGUE_ID

python -m fantasy_projections                   # full pipeline: fetch all 3 sites, write workbook
python -m fantasy_projections.sources.sleeper   # fetch one site (also .espn, .yahoo)
python -m fantasy_projections.aggregate         # rebuild workbook from output/raw/, no network
```

There is no test suite. To check a change, rebuild with `aggregate` and inspect
the workbook with pandas or openpyxl. Sleeper and ESPN need no credentials;
Yahoo needs the user's. Without a Yahoo download cached, the run succeeds but
the board is empty, because a player needs all three projections. That is
expected, not a bug.

## Credentials: handle with care

- `yahoo_cookies.txt` holds the user's Yahoo session cookie, a login
  credential, and `.env` holds their Yahoo league ID. Never print, echo, or
  commit their values. To check setup, report whether they're set without
  showing the values.
- Ask the user to paste the cookie directly into the file, not into the chat.
- `.env`, `yahoo_cookies.txt`, and `output/` are git-ignored. Keep it that way.

## Layout

- `fantasy_projections/config.py`: every setting and file path, anchored to
  the repo root. Board size per position is `POSITION_LIMITS`; the season comes
  from `SEASON` in `.env`.
- `fantasy_projections/sources/`: one module per site. Each exposes
  `fetch_<site>() -> DataFrame` with `player`, `team`, `position`, and
  `<site>_points` columns, plus `main()`, which caches it to
  `output/raw/<site>.csv`.
- `fantasy_projections/aggregate.py`: name matching (`normalize_name`,
  `_ALIASES`), merge, average, `build_board`, then calls the workbook writer.
- `fantasy_projections/excel_export.py`: formatting and writing only.
- `fantasy_projections/__main__.py`: runs the sources in order, then aggregate.

## How each source gets half-PPR numbers

- `sleeper.py`: Sleeper's public projections API; reads `stats.pts_half_ppr`.
  No auth.
- `espn.py`: ESPN's undocumented public fantasy API (`leaguedefaults/1`, which
  is standard scoring), filtered with the `X-Fantasy-Filter` header. Half-PPR
  = season projection `appliedTotal` + 0.5 x projected receptions (stat
  `"53"`). No auth.
- `yahoo.py`: scrapes the user's league Players page (`/f1/<league>/players`,
  `stat1=S_PS_<SEASON>`) with their session cookie. The points use the
  league's scoring settings, so the league must award 0.5 per reception.

## Behavior to preserve

- A player gets an `average_points` only when all three sites project them;
  a missing projection is never treated as zero.
- The board ranks players within each position first (`POSITION_LIMITS`), then
  combines them, so high QB totals don't crowd out other positions.
- The workbook is the only user-facing output. Don't add extra output files;
  per-site caches belong in `output/raw/`.

## Debugging a player missing from the board

1. Search `output/raw/*.csv` (case-insensitive, partial name) to see which
   site lacks the player.
2. If the player is listed under a different spelling, add an entry to
   `_ALIASES` in `aggregate.py`. Keys and values are already normalized:
   lowercase, no punctuation, no Jr./Sr./II suffixes.
3. If a site has no projection at all, that's usually expected. Once the
   season starts, sites zero out or drop season projections for injured
   players (OUT, IR); the ESPN fetcher skips zero projections, and Sleeper and
   Yahoo skip missing ones.

If Yahoo's numbers run consistently higher or lower than Sleeper's and ESPN's,
the user's Yahoo league probably isn't set to half-PPR scoring.

## Conventions

- Stay compatible with Python 3.9: use `from __future__ import annotations`
  for `X | None` hints.
- Keep lines at 88 characters or fewer and match the existing docstring and
  comment style.
- The Yahoo scraper sleeps between requests; keep it polite.
