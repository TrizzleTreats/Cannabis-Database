# Start here

Paste the prompt below into a new Claude Code session opened in this folder.

The original handoff from Claude chat — set up git, add the domain list, download
the Mid-Atlantic licence files — is **done**, along with a good deal more. See
`docs/STATUS.md` for where things actually stand; that file is the source of
truth, not this one.

## Paste this into Claude Code (opened in this folder)

```
Read CLAUDE.md, then docs/STATUS.md, docs/HANDOFF.md and docs/FILE_INDEX.md.

This is a git repo (branch build/setup-and-mid-atlantic, local only — never add a
remote or push). Run `python3 scripts/verify.py` first: it is the project's own
check and it passed clean at the last commit. If it fails, fix that before
anything else.

State of the data: 50,544 licences across 26 of 51 jurisdictions in three tables
(new_england / mid_atlantic / regions_3_to_9), all sharing one 41-column schema,
plus 2,087 business-directory entries. Raw downloads are declared in
scripts/sources.json and logged in data/raw/manifest.csv.

Work the docs/STATUS.md "Next" list. Before starting, tell me which item you plan
to take and why, then do that one — don't fan out across several.

Hard rules, learned the hard way in this repo:
- Primary sources only. Never guess a file URL — resolve it from the official
  page. If a source genuinely isn't published, record UNAVAILABLE with the
  reason rather than substituting something close.
- Never solve or bypass a CAPTCHA. Minnesota's licence page is behind one and
  stays blocked until a person fetches it.
- Every fact carries a source and a date. Never let a placeholder ("Out Of
  State/Unknown", "Data Not Available", "Not Published") become a published value.
- Never mix "issued", "approved", "licensed", "pending renewal" and "operating"
  in one count, and never reconcile two differently-dated figures into one number.
- Connecticut uses its TRADITIONAL EIGHT counties, not Census Planning Regions.
- data/clean/ is tracked and contains private columns — see the private-columns
  rule in CLAUDE.md. Stage named paths; never `git commit -a`.
- A fetch that returns HTTP 200 can still be a bot check, an unrendered
  dashboard, or a truncated API page. Check content, not status codes.

Then stop and show me a plan before changing data.
```

## Two things that need a decision from me, not more work

- **The 22 business entries flagged as holding a state licence**
  (`data/clean/business_licence_matches.csv`). Each either moves to the licence
  table or stays in the directory. The match is on name alone, so it needs a
  human call — Cookies, STIIIZY and Papa & Barkley look clear-cut; GAIACA, a
  waste-services firm that also holds two distributor licences, does not.
- **Whether to chase the 26 states that publish no licensee list at all.** That
  means a data request to each regulator or a per-licensee portal crawl, which
  is a different kind of work from everything done so far.

## Tools that already exist — read these before writing new ones

| Script | What it does |
|---|---|
| `scripts/verify.py` | The project's check: private data, domain allowlist, raw-file hashes, table integrity, county validity |
| `scripts/fetch_raw.py` | Downloads everything declared in `scripts/sources.json`, logging each attempt to `data/raw/manifest.csv` |
| `scripts/discover_sources.py` | Walks the licensee pages the reports cite and records the data files they link to |
| `scripts/build_new_england.py`, `build_mid_atlantic.py`, `build_states.py` | The three licence-table builders; adding a state means adding a spec |
| `scripts/build_businesses.py` | Parses all 11 audited business directories |
| `scripts/match_businesses_to_licences.py` | Matches directory entries to licensees by normalised name |
| `scripts/fill_counties.py` | Fills, canonicalises and validates the county column |
| `scripts/xlsx_reader.py` | Reads .xlsx; predates openpyxl being installed, still used by the builders |

Installed since the first session: `pypdf`, `openpyxl`, `xlrd`. Python's SSL store
needs an explicit CA bundle (`/etc/ssl/cert.pem`) — the scripts already handle it.
