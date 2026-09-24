"""Fetch half-PPR full-season projections from ESPN's public fantasy API.

ESPN's fantasy site is backed by an undocumented JSON API. Its `leaguedefaults`
endpoint serves projections for every player without a league or login. It
scores them in ESPN's standard (non-PPR) format, so half-PPR is derived by
adding half a point per projected reception.
"""

from __future__ import annotations

import json

import pandas as pd
import requests
from espn_api.football.constant import PRO_TEAM_MAP

from fantasy_projections.config import SEASON, POSITIONS, ESPN_CSV, COLLECT_LIMIT

# `leaguedefaults/1` = ESPN's default standard-scoring league.
ESPN_URL = (
    "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"
    f"/seasons/{SEASON}/segments/0/leaguedefaults/1?view=kona_player_info"
)

# Ask for QB/RB/WR/TE (lineup slots 0/2/4/6), sorted by season projection
# (stat source 1 = projected, split 0 = full season).
ESPN_FILTER = {
    "players": {
        "limit": 1000,
        "filterSlotIds": {"value": [0, 2, 4, 6]},
        "sortAppliedStatTotal": {
            "sortAsc": False,
            "sortPriority": 1,
            "value": f"10{SEASON}",
        },
    }
}

# ESPN's defaultPositionId -> position.
POSITION_IDS = {1: "QB", 2: "RB", 3: "WR", 4: "TE"}

RECEPTIONS_STAT = "53"
HALF_PPR_PER_REC = 0.5


def _season_projection(player: dict) -> dict | None:
    """Return the player's full-season projection entry, if ESPN has one."""
    for stat in player.get("stats") or []:
        if (
            stat.get("statSourceId") == 1
            and stat.get("statSplitTypeId") == 0
            and stat.get("seasonId") == SEASON
        ):
            return stat
    return None


def fetch_espn() -> pd.DataFrame:
    """Return a DataFrame of ESPN half-PPR season projections."""
    resp = requests.get(
        ESPN_URL,
        headers={"X-Fantasy-Filter": json.dumps(ESPN_FILTER)},
        timeout=30,
    )
    resp.raise_for_status()

    rows = []
    for entry in resp.json().get("players", []):
        player = entry.get("player") or {}
        position = POSITION_IDS.get(player.get("defaultPositionId"))
        proj = _season_projection(player)
        if position not in POSITIONS or proj is None:
            continue

        receptions = (proj.get("stats") or {}).get(RECEPTIONS_STAT, 0)
        pts = proj.get("appliedTotal", 0) + HALF_PPR_PER_REC * receptions
        if pts <= 0:
            continue

        rows.append(
            {
                "player": player.get("fullName"),
                "team": PRO_TEAM_MAP.get(player.get("proTeamId")),
                "position": position,
                "espn_points": round(float(pts), 2),
            }
        )

    if not rows:
        raise SystemExit(
            "ESPN returned no projections. Its fantasy API is undocumented and "
            "may have changed; check ESPN_URL and ESPN_FILTER in sources/espn.py."
        )

    df = pd.DataFrame(rows).sort_values("espn_points", ascending=False)
    df = df.head(COLLECT_LIMIT)
    return df.reset_index(drop=True)


def main() -> None:
    df = fetch_espn()
    df.to_csv(ESPN_CSV, index=False)
    print(f"ESPN: wrote {len(df)} players to {ESPN_CSV}")


if __name__ == "__main__":
    main()
