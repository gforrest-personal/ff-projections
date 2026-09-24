# Fantasy Football Projection Aggregator

Pulls **half-PPR season projections** for every QB, RB, WR, and TE from three
sources (**Sleeper, ESPN, and Yahoo**), matches players across them, averages
the projections, and builds a ready-to-draft board as a formatted Excel
workbook.

No single site's projections are gospel, so averaging three of them gives you a
more stable ranking to draft from. A player is only ranked once **all three**
sites have a projection for him; a missing source is never treated as zero.

> **Built for draft day.** Run it before your draft. Once the season starts,
> sites zero out season projections for injured players (OUT, IR), so those
> players fall off the board.

---

## What you get

One file: **`output/fantasy_draft_board.xlsx`**. The `output/` folder isn't in
the repo; it's created the first time you run the tool, and each run refreshes
it with the latest projections.

![The RB sheet of the draft board workbook, with each site's projection, the average, and a color-scaled drop_to_next column](docs/draft-board.png)

*The RB sheet. Darker `drop_to_next` cells mark tier cliffs, like the 30-point
drop after Bijan Robinson.*

| Sheet | What's in it |
|-------|--------------|
| **ALL** | The **199-player draft board**, every position, ranked by average |
| **QB / RB / WR / TE** | The board split by position, plus a **`drop_to_next`** column |

Every sheet shows each site's projection side by side with the average.
`drop_to_next` is how many projected points a player is worth *over the next
player at his position*, so you can spot tier cliffs on draft day (e.g. a
20-point drop after TE2). Headers are frozen and filtered, point columns show
two decimals, and `drop_to_next` is color-scaled so big drop-offs stand out.

---

## How it works

```
Sleeper ─┐
ESPN  ───┼─►  match names  ─►  average (all 3 required)  ─►  draft board  ─►  .xlsx
Yahoo ───┘
```

1. **Collect** up to 500 players from each source, caching each download in
   `output/raw/`.
2. **Match names** so `A.J. Brown`, `AJ Brown`, and `A.J. Brown Jr.` line up
   across sites (handles suffixes, punctuation, and a few known aliases).
3. **Average**: `average_points = (sleeper + espn + yahoo) / 3`, but *only*
   when all three exist. Missing projections stay blank, never zero.
4. **Build the board**: rank players **within each position**, keep a
   configurable number per position (default 24 QB / 70 RB / 85 WR / 20 TE =
   199), then sort the combined board by average. Ranking within position first
   stops high QB point totals from crowding out RB/WR/TE.
5. **Write the workbook**: the full board plus one sheet per position.

---

## Where the numbers come from

| Site | How it's pulled | What you need |
|------|-----------------|---------------|
| **Sleeper** | Sleeper's public projections API, which includes a half-PPR total | Nothing |
| **ESPN** | ESPN's public (undocumented) fantasy API. It returns standard-scoring projections for every player; the tool adds 0.5 points per projected reception to get half-PPR | Nothing |
| **Yahoo** | Scrapes the **Players** page of your Yahoo league, showing season projections sorted by points | A Yahoo league with **half-PPR** scoring, plus your login cookie |

Yahoo scores projections with **your league's scoring settings**, so the league
must award **0.5 points per reception**. Otherwise its numbers won't be
half-PPR and the averages will be off. Any league works, including an empty one
you create just for this; you don't need to draft in it.

---

## Requirements

- Python 3.9+
- The packages in `requirements.txt`
- A **Yahoo** fantasy football league with **half-PPR** scoring (see
  [above](#where-the-numbers-come-from)). Sleeper and ESPN need no account.

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/gforrest-personal/ff-projections.git
cd ff-projections
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Connect your Yahoo league

**Check the league's scoring.** In your Yahoo league's settings, **Receptions**
should be worth **0.5** points. If you're creating a league just for this tool,
set that before running it.

**League ID.** Copy the template, then set `YAHOO_LEAGUE_ID` in `.env` to the
number in your league's URL (`.../f1/{YAHOO_LEAGUE_ID}/...`):

```bash
cp .env.example .env
```

**Login cookie.** Yahoo only shows projections to a logged-in league member,
so the tool reuses your browser session, kept in a separate file (not in
`.env`):
1. Log in to your Yahoo fantasy league.
2. Open DevTools → **Network** tab, reload the players page.
3. Click any request to `football.fantasysports.yahoo.com`, find the **`Cookie:`**
   request header, and copy the entire value.
4. Paste it into a file named **`yahoo_cookies.txt`** in the project root (one
   line).

> Both `.env` and `yahoo_cookies.txt` are git-ignored, so they will never be
> committed.

---

## Usage

From the project root, run the whole pipeline:

```bash
python -m fantasy_projections
```

This downloads fresh projections from all three sites. When it finishes, a new
`output/` folder appears in the project (in VS Code, look in the Explorer
sidebar; it shows greyed out because git ignores it). Open
**`output/fantasy_draft_board.xlsx`** in Excel, Numbers, or Google Sheets. VS
Code can't preview `.xlsx` files, so right-click it and choose **Reveal in
Finder** (macOS) or **Reveal in File Explorer** (Windows).

You can also run one step at a time. Because each download is cached in
`output/raw/`, if one site fails (say, an expired Yahoo cookie) you can fix it,
re-run just that source, and rebuild the workbook without re-fetching the
others:

```bash
python -m fantasy_projections.sources.sleeper   # no credentials needed
python -m fantasy_projections.sources.espn      # no credentials needed
python -m fantasy_projections.sources.yahoo     # needs yahoo_cookies.txt + YAHOO_LEAGUE_ID
python -m fantasy_projections.aggregate         # rebuild the workbook from output/raw/
```

---

## Running it with Claude Code

[Claude Code](https://claude.com/claude-code) can set up and run the project for
you, from your terminal or inside VS Code. The repo includes a
[`CLAUDE.md`](CLAUDE.md) that Claude Code reads automatically, so it already
knows the commands, the project layout, and to keep your credentials out of
the chat.

1. Clone the repo and start Claude Code in the project folder:

   ```bash
   git clone https://github.com/gforrest-personal/ff-projections.git
   cd ff-projections
   claude
   ```

2. Ask it to set things up:

   > Set up this project: create a virtual environment, install the
   > requirements, and copy .env.example to .env.

3. Add your Yahoo league ID to `.env` and your cookie to `yahoo_cookies.txt`
   yourself (see [Setup](#2-connect-your-yahoo-league)). Paste the cookie
   straight into the file rather than into the chat, since it's a login
   credential.

4. Ask it to run the tool:

   > Run the pipeline and tell me when the draft board is ready.

Once it's set up, you can also ask things like:

- "Rebuild the workbook from the cached downloads."
- "Change the board size for a 12-team league."
- "Why isn't *player name* on the draft board?"

---

## Configuration

All knobs live in `fantasy_projections/config.py`:

| Setting | Default | Meaning |
|---------|---------|---------|
| `SEASON` | `2026` | Projection year (override in `.env`) |
| `COLLECT_LIMIT` | `500` | Players pulled per source |
| `POSITION_LIMITS` | `24/70/85/20` | Board size per position (sized for a 10-team league) |

To tune the board for a different league size, just edit `POSITION_LIMITS`.

---

## Project structure

```
ff-projections/
├── docs/
│   └── draft-board.png        Screenshot used in this README
├── fantasy_projections/       Python package
│   ├── sources/               One module per projection site
│   │   ├── __init__.py
│   │   ├── espn.py            ESPN (public, undocumented fantasy API)
│   │   ├── sleeper.py         Sleeper (public API)
│   │   └── yahoo.py           Yahoo (scrapes your league's Players page)
│   ├── __init__.py
│   ├── __main__.py            Entry point: runs the full pipeline end to end
│   ├── aggregate.py           Match names, merge, average, build the board
│   ├── config.py              Settings and file paths; reads .env
│   └── excel_export.py        Format and write the Excel workbook
├── .env.example               Template for your Yahoo league ID
├── .gitignore                 Keeps secrets and output/ out of git
├── CLAUDE.md                  Project guide for Claude Code
├── LICENSE                    MIT license
├── README.md
└── requirements.txt           Python dependencies
```

Not in the repo: running the tool creates `output/` (the workbook plus a
`raw/` download cache), and setup has you create `.env` and
`yahoo_cookies.txt`. All three are git-ignored.

Data flows one way: `sources/*` cache each site's download in `output/raw/` →
`aggregate` merges them and builds the draft board → `excel_export` writes the
board into the workbook. To add a new site, drop a module in `sources/` that
returns the same columns, then wire it into `aggregate.py` and `__main__.py`.

---

## Troubleshooting

- **`Yahoo redirected to login`** or **`Yahoo returned no players`**: your
  Yahoo cookie has expired (they're short-lived, so grab a fresh one right
  before your draft; see Setup). If a fresh cookie doesn't fix it, check
  `YAHOO_LEAGUE_ID`.
- **Yahoo's numbers are consistently higher or lower than Sleeper's and
  ESPN's**, especially for pass catchers: your Yahoo league probably isn't
  half-PPR. Set Receptions to 0.5 points in its scoring settings and re-run the
  Yahoo step.
- **The ESPN step fails with an HTTP error or finds no players**: ESPN's
  fantasy API is undocumented, so ESPN can change it without notice. The
  endpoint and filter live at the top of `fantasy_projections/sources/espn.py`.
- **A player is missing from the board**: one of the three sites probably has
  no projection for him, so no average could be computed. This is common once
  the season starts (see *Built for draft day* above). Search the files in
  `output/raw/` to see which site doesn't list him.

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

---

## License

[MIT](LICENSE)
