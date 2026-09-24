"""Fantasy football projection aggregator.

Pulls half-PPR season projections from Sleeper, ESPN, and Yahoo, averages them,
and builds a draft board. Run the whole pipeline with:

    python -m fantasy_projections

Package layout:
    config.py        Shared settings, file paths, and secrets loaded from .env
    sources/         One module per projection provider (Sleeper, ESPN, Yahoo)
    aggregate.py     Normalize names, merge sources, average, build the board
    excel_export.py  Write the draft-day Excel workbook (the one output file)
    __main__.py      Run every step end to end
"""
