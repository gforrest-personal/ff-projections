"""Scrape full-season projections from Yahoo Fantasy (requests + BeautifulSoup).

Yahoo requires an authenticated session. Export your browser's Cookie header for
football.fantasysports.yahoo.com into `yahoo_cookies.txt` in the project root
(a single line, exactly as sent in the request's `Cookie:` header) and this
module will reuse it via a plain requests.Session().

The projected points use the league's scoring settings, so the league must be
half-PPR (0.5 points per reception) for the numbers to line up with the other
sources.
"""

import re
import sys
import time

import requests
from bs4 import BeautifulSoup
import pandas as pd

from fantasy_projections.config import (
    SEASON,
    POSITIONS,
    YAHOO_LEAGUE_ID,
    YAHOO_COOKIE_FILE as COOKIE_FILE,
    YAHOO_CSV,
    COLLECT_LIMIT,
    require,
)

PAGE_SIZE = 25
MAX_PAGES = 6  # up to 150 players per position (600 total before the 500 cap)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _load_cookies() -> str:
    if not COOKIE_FILE.exists():
        sys.exit(
            f"Missing {COOKIE_FILE}. Paste your Yahoo Cookie header into that file "
            "(one line) and re-run."
        )
    with open(COOKIE_FILE) as fh:
        cookie = fh.read().strip()
    if not cookie:
        sys.exit(f"{COOKIE_FILE} is empty.")
    return cookie


def _make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    session.headers["Cookie"] = _load_cookies()
    return session


def _parse_page(html: str) -> list[dict]:
    """Parse one Yahoo players table page into a list of player dicts."""
    soup = BeautifulSoup(html, "lxml")
    rows = []

    for anchor in soup.select("a.name[data-ys-playerid]"):
        player_id = anchor.get("data-ys-playerid")
        name = anchor.get_text(strip=True)

        # The player row is the enclosing <tr>.
        row = anchor.find_parent("tr")
        if row is None:
            continue

        # Team + position live in a small element near the name, formatted like
        # "BUF - QB". Yahoo renders it in a <span class="Fz-xxs">, but injured
        # players get an extra Fz-xxs status span first (e.g. "Q"), so scan every
        # candidate and take the one matching the "TEAM - POS" pattern.
        team = position = None
        for meta in row.select("span.Fz-xxs"):
            text = meta.get_text(" ", strip=True)
            m = re.search(r"([A-Za-z]{2,4})\s*-\s*([A-Za-z,]+)", text)
            if m:
                team = m.group(1).upper()
                # A player can list multiple positions ("RB,WR"); take the first.
                position = m.group(2).split(",")[0].strip().upper()
                break

        # Projected points: the first td.pts in the row holds the season total
        # for the selected stat context (S_PS_<SEASON>).
        pts_cell = row.select_one("td.pts")
        pts = None
        if pts_cell:
            raw = pts_cell.get_text(strip=True).replace(",", "")
            try:
                pts = float(raw)
            except ValueError:
                pts = None

        rows.append(
            {
                "yahoo_id": player_id,
                "player": name,
                "team": team,
                "position": position,
                "yahoo_points": pts,
            }
        )

    return rows


def fetch_yahoo() -> pd.DataFrame:
    """Scrape Yahoo projections for QB/RB/WR/TE across all pages."""
    league_id = require("YAHOO_LEAGUE_ID", YAHOO_LEAGUE_ID)
    base_url = f"https://football.fantasysports.yahoo.com/f1/{league_id}/players"

    session = _make_session()
    all_rows = []

    for pos in ("QB", "RB", "WR", "TE"):
        for page in range(MAX_PAGES):
            count = page * PAGE_SIZE
            params = {
                "status": "ALL",
                "pos": pos,
                "cut_type": 9,
                "stat1": f"S_PS_{SEASON}",
                "myteam": 0,
                "sort": "PTS",
                "sdir": 1,
                "count": count,
            }
            resp = session.get(base_url, params=params, timeout=30)

            # A redirect to login means our cookies are stale/invalid.
            if "login.yahoo.com" in resp.url:
                sys.exit(
                    "Yahoo redirected to login — cookies are missing or expired. "
                    f"Refresh {COOKIE_FILE}."
                )
            resp.raise_for_status()

            page_rows = _parse_page(resp.text)
            if not page_rows:
                break  # no more players for this position

            all_rows.extend(page_rows)
            time.sleep(0.5)  # be polite

    # An expired session doesn't always redirect to login; Yahoo may instead
    # serve a "There was a problem" page with no player table.
    if not all_rows:
        sys.exit(
            "Yahoo returned no players — cookies are probably expired, or "
            f"YAHOO_LEAGUE_ID is wrong. Refresh {COOKIE_FILE} and re-run."
        )

    df = pd.DataFrame(all_rows)

    # Keep only our positions and rows with a real projection.
    df = df[df["position"].isin(POSITIONS)]
    df = df[df["yahoo_points"].notna()]
    df = df.drop_duplicates(subset="yahoo_id")
    df["yahoo_points"] = df["yahoo_points"].round(2)
    df = df.sort_values("yahoo_points", ascending=False)
    df = df.head(COLLECT_LIMIT)
    return df.reset_index(drop=True)


def main() -> None:
    df = fetch_yahoo()
    df.to_csv(YAHOO_CSV, index=False)
    print(f"Yahoo: wrote {len(df)} players to {YAHOO_CSV}")


if __name__ == "__main__":
    main()
