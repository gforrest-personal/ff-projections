"""Projection providers.

Each module exposes `fetch_<source>() -> DataFrame` with `player`, `team`,
`position`, and `<source>_points` columns, plus a `main()` that writes the
result to its raw CSV in output/.
"""
