"""Shared configuration for the fantasy projections aggregator.

Secrets and personal identifiers (league IDs, ESPN cookies) are read from
environment variables so they never live in source control. Copy `.env.example`
to `.env` and fill in your values, or export the variables in your shell. See
README.md for how to obtain each one.
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
    need no credentials — like Sleeper — keep working even with an empty .env.
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

# --- ESPN (private league requires cookie auth; see README) ---
ESPN_LEAGUE_ID = os.environ.get("ESPN_LEAGUE_ID")
ESPN_SWID = os.environ.get("ESPN_SWID")
ESPN_S2 = os.environ.get("ESPN_S2")

# --- Yahoo (requires a browser session cookie in yahoo_cookies.txt; see README) ---
YAHOO_LEAGUE_ID = os.environ.get("YAHOO_LEAGUE_ID")
YAHOO_COOKIE_FILE = PROJECT_ROOT / "yahoo_cookies.txt"

# --- Output files (all generated on each run; output/ is git-ignored) ---
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

SLEEPER_CSV = OUTPUT_DIR / "sleeper_projections.csv"
ESPN_CSV = OUTPUT_DIR / "espn_projections.csv"
YAHOO_CSV = OUTPUT_DIR / "yahoo_projections.csv"
# Full merged dataset (every matched player) — nothing is lost here.
FULL_CSV = OUTPUT_DIR / "all_projections.csv"
# The trimmed, position-limited draft board.
FINAL_CSV = OUTPUT_DIR / "final_projections.csv"
# Draft-day Excel workbook (ALL + per-position sheets with drop-off analysis).
XLSX_FILE = OUTPUT_DIR / "fantasy_draft_board.xlsx"
