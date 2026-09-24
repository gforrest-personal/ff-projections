"""Fetch 2026 projections from ESPN via the espn-api package."""

import pandas as pd
from espn_api.football import League

from fantasy_projections.config import (
    SEASON,
    POSITIONS,
    ESPN_LEAGUE_ID,
    ESPN_SWID,
    ESPN_S2,
    ESPN_CSV,
    COLLECT_LIMIT,
    require,
)


def fetch_espn() -> pd.DataFrame:
    """Return a DataFrame of ESPN full-season projected points."""
    league = League(
        league_id=int(require("ESPN_LEAGUE_ID", ESPN_LEAGUE_ID)),
        year=SEASON,
        swid=require("ESPN_SWID", ESPN_SWID),
        espn_s2=require("ESPN_S2", ESPN_S2),
    )

    # Combine the free-agent pool with any rostered players so we capture
    # every player regardless of draft status.
    players = list(league.free_agents(size=2000))
    for team in league.teams:
        players.extend(team.roster)

    rows = []
    seen = set()
    for p in players:
        if p.playerId in seen:
            continue
        seen.add(p.playerId)

        if p.position not in POSITIONS:
            continue

        pts = p.projected_total_points
        if pts is None or pts <= 0:
            continue

        rows.append(
            {
                "player": p.name,
                "team": p.proTeam,
                "position": p.position,
                "espn_points": round(float(pts), 2),
            }
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
