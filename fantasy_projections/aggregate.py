"""Merge Sleeper, ESPN, and Yahoo projections, build the draft board, and write
the Excel workbook.

Run on its own (`python -m fantasy_projections.aggregate`) to rebuild the
workbook from the cached downloads in output/raw/ without re-fetching.
"""

import re
import os

import pandas as pd

from fantasy_projections.config import (
    SLEEPER_CSV,
    ESPN_CSV,
    YAHOO_CSV,
    POSITIONS,
    POSITION_LIMITS,
)
from fantasy_projections.excel_export import build_workbook

# Common suffixes that differ across platforms and should be stripped.
_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}

# A few name spellings that differ between providers.
_ALIASES = {
    "kenneth walker": "ken walker",
    "michael pittman": "mike pittman",
    "joshua palmer": "josh palmer",
    "cameron ward": "cam ward",
    "brian thomas": "brian thomas",
    "marquise brown": "hollywood brown",
    "chigoziem okonkwo": "chig okonkwo",
    "gabriel davis": "gabe davis",
}


def normalize_name(name: str) -> str:
    """Normalize a player name for cross-platform matching."""
    if not isinstance(name, str):
        return ""
    n = name.lower().strip()
    # Drop anything in parentheses, periods, apostrophes, commas, hyphens.
    n = re.sub(r"\(.*?\)", "", n)
    n = n.replace(".", "").replace("'", "").replace(",", "")
    n = n.replace("-", " ")
    # Collapse whitespace.
    n = re.sub(r"\s+", " ", n).strip()

    # Strip trailing generational suffixes.
    parts = [p for p in n.split(" ") if p and p not in _SUFFIXES]
    n = " ".join(parts)

    return _ALIASES.get(n, n)


def _load(path: str, label: str) -> pd.DataFrame:
    if not os.path.exists(path):
        print(f"  ! {label} file '{path}' not found — skipping.")
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["key"] = df["player"].map(normalize_name)
    return df


def aggregate() -> pd.DataFrame:
    sleeper = _load(SLEEPER_CSV, "Sleeper")
    espn = _load(ESPN_CSV, "ESPN")
    yahoo = _load(YAHOO_CSV, "Yahoo")

    # Base frame: union of all keys, carrying player/team/position metadata.
    # Prefer Sleeper metadata, then ESPN, then Yahoo.
    meta_frames = []
    for df in (sleeper, espn, yahoo):
        if not df.empty:
            meta_frames.append(df[["key", "player", "team", "position"]])
    if not meta_frames:
        raise SystemExit("No source CSVs available to aggregate.")

    meta = pd.concat(meta_frames).drop_duplicates(subset="key", keep="first")

    merged = meta.copy()
    for df, col in (
        (sleeper, "sleeper_points"),
        (espn, "espn_points"),
        (yahoo, "yahoo_points"),
    ):
        if df.empty:
            merged[col] = pd.NA
        else:
            merged = merged.merge(df[["key", col]], on="key", how="left")

    # Average only when all three projections exist; missing is never zero.
    have_all = (
        merged["sleeper_points"].notna()
        & merged["espn_points"].notna()
        & merged["yahoo_points"].notna()
    )
    merged["average_points"] = pd.NA
    merged.loc[have_all, "average_points"] = (
        merged.loc[have_all, "sleeper_points"]
        + merged.loc[have_all, "espn_points"]
        + merged.loc[have_all, "yahoo_points"]
    ) / 3
    merged["average_points"] = merged["average_points"].astype("Float64").round(2)

    merged = merged[merged["position"].isin(POSITIONS)]

    out = merged[
        [
            "player",
            "team",
            "position",
            "sleeper_points",
            "espn_points",
            "yahoo_points",
            "average_points",
        ]
    ]

    # Sort by average (players with all three first), then by any available data.
    out = out.sort_values(
        by=["average_points", "sleeper_points", "espn_points"],
        ascending=False,
        na_position="last",
    ).reset_index(drop=True)
    return out


def build_board(full: pd.DataFrame) -> pd.DataFrame:
    """Trim the full dataset to a position-limited 10-team draft board.

    Only players with a three-source average are eligible. Within each position
    we rank by average_points and keep the configured number, then combine and
    sort the whole board by average_points descending. This avoids letting the
    higher QB point totals crowd out RB/WR/TE.
    """
    eligible = full[full["average_points"].notna()]

    kept = []
    for pos, limit in POSITION_LIMITS.items():
        pool = eligible[eligible["position"] == pos]
        pool = pool.sort_values("average_points", ascending=False).head(limit)
        kept.append(pool)

    board = pd.concat(kept)
    board = board.sort_values("average_points", ascending=False).reset_index(drop=True)
    return board


def main() -> None:
    full = aggregate()
    complete = full["average_points"].notna().sum()
    print(f"Aggregate: matched {len(full)} players ({complete} with all three projections)")

    board = build_board(full)
    counts = board["position"].value_counts().to_dict()
    print(f"Draft board: {len(board)} players {counts}")

    build_workbook(board)


if __name__ == "__main__":
    main()
