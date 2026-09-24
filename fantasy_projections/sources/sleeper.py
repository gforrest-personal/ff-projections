"""Fetch 2026 half-PPR full-season projections from Sleeper."""

import requests
import pandas as pd

from fantasy_projections.config import SEASON, POSITIONS, SLEEPER_CSV, COLLECT_LIMIT

SLEEPER_URL = (
    f"https://api.sleeper.com/projections/nfl/{SEASON}"
    "?season_type=regular&order_by=pts_half_ppr"
)


def fetch_sleeper() -> pd.DataFrame:
    """Return a DataFrame of Sleeper half-PPR season projections."""
    resp = requests.get(SLEEPER_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for entry in data:
        player = entry.get("player") or {}
        stats = entry.get("stats") or {}
        pos = player.get("position")
        pts = stats.get("pts_half_ppr")

        if pos not in POSITIONS or pts is None:
            continue

        name = f"{player.get('first_name', '')} {player.get('last_name', '')}".strip()
        rows.append(
            {
                "player": name,
                "team": entry.get("team") or player.get("team"),
                "position": pos,
                "sleeper_points": round(float(pts), 2),
            }
        )

    df = pd.DataFrame(rows).sort_values("sleeper_points", ascending=False)
    df = df.head(COLLECT_LIMIT)
    return df.reset_index(drop=True)


def main() -> None:
    df = fetch_sleeper()
    df.to_csv(SLEEPER_CSV, index=False)
    print(f"Sleeper: wrote {len(df)} players to {SLEEPER_CSV}")


if __name__ == "__main__":
    main()
