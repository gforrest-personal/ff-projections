"""Shared configuration for the fantasy projections aggregator.

Personal settings (the Yahoo league ID) are read from environment variables so
they never live in source control. Copy `.env.example` to `.env` and fill in
your values, or export the variables in your shell. The Yahoo session cookie
lives in `yahoo_cookies.txt`. See README.md for how to obtain each one.
"""

from __future__ import annotations

import os
from pathlib import Path

# Repo root (the folder containing this package). All file paths below are
# anchored here so the tool works no matter which directory you run it from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load a local .env file if python-dotenv is installed. It's optional: if the
# package isn't present, we fall back to whatever is already in the environment.
try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass


def require(name: str, value: str | None) -> str:
    """Return a required config value, or exit with a clear message if missing.

    Called by the fetchers at run time (not import time) so that sources which
    need no credentials, like Sleeper and ESPN, keep working with an empty .env.
    """
    if not value:
        raise SystemExit(
            f"Missing required setting {name!r}. Copy .env.example to .env and "
            "fill it in (see README.md)."
        )
    return value


# --- Season (override in .env to roll to a new year) ---
SEASON = int(os.environ.get("SEASON", "2026"))

# --- Positions we care about (skip DST and K) ---
POSITIONS = {"QB", "RB", "WR", "TE"}

# --- Collect up to this many players from each source (matching + completeness) ---
COLLECT_LIMIT = 500

# --- Final draft-board size per position for a 10-team half-PPR league ---
# Max board = 24 + 70 + 85 + 20 = 199 players.
POSITION_LIMITS = {
    "QB": 24,
    "RB": 70,
    "WR": 85,
    "TE": 20,
}

# --- Yahoo (requires a half-PPR league and a browser session cookie; see README) ---
YAHOO_LEAGUE_ID = os.environ.get("YAHOO_LEAGUE_ID")
YAHOO_COOKIE_FILE = PROJECT_ROOT / "yahoo_cookies.txt"

# --- Output files (all generated on each run; output/ is git-ignored) ---
OUTPUT_DIR = PROJECT_ROOT / "output"
# Each source's raw download, cached so the board can be rebuilt without
# re-fetching (e.g. after the Yahoo cookie expires).
RAW_DIR = OUTPUT_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

SLEEPER_CSV = RAW_DIR / "sleeper.csv"
ESPN_CSV = RAW_DIR / "espn.csv"
YAHOO_CSV = RAW_DIR / "yahoo.csv"
# The one file meant for people: the draft board plus per-position sheets with
# drop-off analysis.
XLSX_FILE = OUTPUT_DIR / "fantasy_draft_board.xlsx"
