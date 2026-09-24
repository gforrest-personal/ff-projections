"""Projection providers.

Each module exposes `fetch_<source>() -> DataFrame` with `player`, `team`,
`position`, and `<source>_points` columns, plus a `main()` that caches the
result as a CSV in output/raw/.
"""
