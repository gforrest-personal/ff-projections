# Fantasy Football Projection Aggregator

Pulls **2026 half-PPR season projections** for every QB, RB, WR, and TE from
**three sources — Sleeper, ESPN, and Yahoo** — merges them by player, averages
them, and builds a ready-to-draft board as both CSV and a formatted Excel
workbook.

The idea: no single site's projections are gospel, so averaging three of them
gives you a more stable ranking to draft from. A player is only ranked once
**all three** sites have a projection for him — a missing source is never
treated as zero.

---

## What you get

Running the tool writes these files to the `output/` folder (git-ignored):

| File | What's in it |
|------|--------------|
| `sleeper_projections.csv` | Raw Sleeper projections |
| `espn_projections.csv` | Raw ESPN projections |
| `yahoo_projections.csv` | Raw Yahoo projections |
| `all_projections.csv` | **Every** matched player, all three sources side by side |
| `final_projections.csv` | The trimmed **199-player draft board** |
| `fantasy_draft_board.xlsx` | The draft board as a formatted, draft-day Excel workbook |

The Excel workbook has an **ALL** sheet plus one sheet per position (**QB / RB /
WR / TE**). Each position sheet adds a **`drop_to_next`** column — how many
projected points a player is worth *over the next player at his position* — so
you can spot tier cliffs on draft day (e.g. a 20-point drop after TE2). Headers
are frozen and filtered, point columns show two decimals, and `drop_to_next` is
color-scaled so big drop-offs stand out.

---

## How it works

```
Sleeper ─┐
ESPN  ───┼─►  normalize names  ─►  merge  ─►  average (all 3 required)  ─►  board
Yahoo ───┘
```

1. **Collect** up to 500 players from each source (plenty for matching depth).
2. **Normalize names** so `A.J. Brown`, `AJ Brown`, and `A.J. Brown Jr.` all
   match across sites (handles suffixes, punctuation, and a few known aliases).
3. **Average** — `average_points = (sleeper + espn + yahoo) / 3`, but *only*
   when all three exist. Missing projections stay blank, never zero.
4. **Build the board** — rank players **within each position**, keep a
   configurable number per position (default 24 QB / 70 RB / 85 WR / 20 TE =
   199), then sort the combined board by average. Ranking within position first
   stops high QB point totals from crowding out RB/WR/TE.

---

## Requirements

- Python 3.9+
- The packages in `requirements.txt`
- An ESPN account (for a private ESPN league) and a Yahoo account

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/gforrest-personal/ff-projections.git
cd ff-projections
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Add your league IDs and credentials

Copy the template and fill in your values:

```bash
cp .env.example .env
```

Then edit `.env`. Here's how to find each value:

**League IDs** — open your league on each site; the number in the URL is the ID.
- ESPN: `.../leagues/{ESPN_LEAGUE_ID}/...`
- Yahoo: `.../f1/{YAHOO_LEAGUE_ID}/...`

**ESPN cookies** (`ESPN_SWID` and `ESPN_S2`) — only needed for a **private**
league:
1. Log in at [espn.com](https://espn.com).
2. Open DevTools → **Application** → **Cookies** → `espn.com`.
3. Copy the values of `SWID` (keep the curly braces) and `espn_s2`.

**Yahoo cookie** — Yahoo requires a full browser session, kept in a separate
file (not in `.env`):
1. Log in to your Yahoo fantasy league.
2. Open DevTools → **Network** tab, reload the players page.
3. Click any request to `football.fantasysports.yahoo.com`, find the **`Cookie:`**
   request header, and copy the entire value.
4. Paste it into a file named **`yahoo_cookies.txt`** in the project root (one
   line).

> Both `.env` and `yahoo_cookies.txt` are git-ignored — they will never be
> committed.

---

## Usage

Run the whole pipeline from the project root:

```bash
python -m fantasy_projections
```

Or run any step on its own (handy for debugging):

```bash
python -m fantasy_projections.sources.sleeper   # no credentials needed
python -m fantasy_projections.sources.espn      # needs ESPN_* in .env
python -m fantasy_projections.sources.yahoo     # needs yahoo_cookies.txt + YAHOO_LEAGUE_ID
python -m fantasy_projections.aggregate         # merges whatever CSVs already exist in output/
python -m fantasy_projections.excel_export      # rebuilds the workbook from output/final_projections.csv
```

---

## Configuration

All knobs live in `fantasy_projections/config.py`:

| Setting | Default | Meaning |
|---------|---------|---------|
| `SEASON` | `2026` | Projection year (override in `.env`) |
| `COLLECT_LIMIT` | `500` | Players pulled per source |
| `POSITION_LIMITS` | `24/70/85/20` | Board size per position |

To tune the board for a different league size, just edit `POSITION_LIMITS`.

---

## Project structure

```
fantasy_projections/
├── fantasy_projections/       Python package
│   ├── __main__.py            Entry point: runs the full pipeline end to end
│   ├── config.py              Shared settings and file paths; loads secrets from .env
│   ├── sources/               One module per projection provider
│   │   ├── sleeper.py         Sleeper projections (public API)
│   │   ├── espn.py            ESPN projections (espn-api, cookie auth)
│   │   └── yahoo.py           Yahoo projections (requests + BeautifulSoup scraper)
│   ├── aggregate.py           Normalize names, merge, average, build the board
│   └── excel_export.py        Write the formatted Excel workbook
├── output/                    Generated CSVs and workbook (git-ignored)
├── .env.example               Template for your league IDs and ESPN cookies
├── LICENSE
├── requirements.txt
└── README.md
```

Data flows one way: `sources/*` write raw CSVs to `output/` → `aggregate`
merges them into the full dataset and draft board → `excel_export` turns the
board into the workbook. To add a new provider, drop a module in `sources/`
that returns the same columns, then wire it into `aggregate.py` and
`__main__.py`.

---

## Troubleshooting

- **`Yahoo redirected to login — cookies are missing or expired`** — Yahoo
  session cookies are short-lived. Grab a fresh one (see setup) and re-run.
- **`ESPNAccessDenied` / ESPN returns nothing** — your `ESPN_S2`/`SWID` expired
  or the league went private. Refresh the cookies in `.env`.
- **A player is missing from the board** — he's probably missing a projection on
  one of the three sites, so no average could be computed. Check
  `output/all_projections.csv` to see which source is blank.

---

## Notes

- Projections are **half-PPR, full-season**. Kickers and D/ST are intentionally
  skipped.
- This is a personal side project and is not affiliated with Sleeper, ESPN, or
  Yahoo. Yahoo data is scraped from your own logged-in league view; be
  respectful of their servers (the scraper already rate-limits itself).

---

## Contributing

This is a personal project, but you're welcome to fork it and adapt it for your
own league. Issues and pull requests are welcome, though changes are merged at
the owner's discretion.

## License

[MIT](LICENSE)
