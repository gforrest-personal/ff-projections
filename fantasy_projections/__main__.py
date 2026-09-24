"""Run the full projection pipeline: Sleeper -> ESPN -> Yahoo -> aggregate -> Excel.

Usage (from the project root):
    python -m fantasy_projections
"""

from fantasy_projections import aggregate, excel_export
from fantasy_projections.sources import espn, sleeper, yahoo


def main() -> None:
    print("=== Sleeper ===")
    sleeper.main()

    print("\n=== ESPN ===")
    espn.main()

    print("\n=== Yahoo ===")
    yahoo.main()

    print("\n=== Aggregate ===")
    aggregate.main()

    print("\n=== Excel ===")
    excel_export.main()

    print("\nDone. See output/final_projections.csv and output/fantasy_draft_board.xlsx")


if __name__ == "__main__":
    main()
