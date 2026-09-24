"""Run the full pipeline: Sleeper -> ESPN -> Yahoo -> draft board workbook.

Usage (from the project root):
    python -m fantasy_projections
"""

from fantasy_projections import aggregate
from fantasy_projections.sources import espn, sleeper, yahoo


def main() -> None:
    print("=== Sleeper ===")
    sleeper.main()

    print("\n=== ESPN ===")
    espn.main()

    print("\n=== Yahoo ===")
    yahoo.main()

    print("\n=== Draft board ===")
    aggregate.main()

    print("\nDone. See output/fantasy_draft_board.xlsx")


if __name__ == "__main__":
    main()
