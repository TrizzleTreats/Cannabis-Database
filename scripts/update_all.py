#!/usr/bin/env python3
"""The daily update: fetch, rebuild, check, and build the public site data, in order.

HANDOFF: "The site will update itself daily with scripts and agents." This is that
run. Every step is an existing script; this file only fixes the order and stops at the
first failure, so a bad day never reaches the site.

  1. fetch      scripts/fetch_raw.py --refresh: every declared source downloaded
                again. Unchanged files are logged and left alone; a suspect or failed
                download is logged and the last good file stays current.
  2. build      the three licence tables, from the current raw files.
  3. counties   fill_counties.py: geocode new addresses (cached), then apply,
                canonicalise and validate, then resolve_independent_cities.py.
  4. types      add_standard_type.py --apply (the builders do not write it).
  5. law        build_legal_status.py, build_quick_reference.py and build_market.py (hand-curated; they
                only change when someone edits their data files, but are re-checked).
  6. site       build_site_data.py: the public JSON, on its allowlist.
  7. verify     verify.py. A failure here fails the run.

Order matters, and was established by rebuilding from data/raw/ and comparing with the
committed tables (19 Nov 2026): with this order, all three licence tables come back
identical, row for row and column for column.

Not in the daily run: New Jersey's per-business permit PDFs (scripts/fetch_nj_permits.py,
a 517-file set), the business directory (built once from the audited reports), and Maine,
Vermont, Rhode Island and New Hampshire, whose regulators publish nothing the fetcher can
download (their rows are carried forward and say so).

Usage:
  python3 scripts/update_all.py                    # the full daily run (needs the network)
  python3 scripts/update_all.py --offline          # no fetch, no geocoder: rebuild only
  python3 scripts/update_all.py --summary out.md   # also write a markdown summary
"""
import argparse, collections, csv, pathlib, subprocess, sys, time
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLEAN = ROOT / "data" / "clean"
TABLES = ["new_england_licences.csv", "mid_atlantic_licences.csv", "regions_3_to_9_licences.csv"]
MANIFEST = ROOT / "data" / "raw" / "manifest.csv"

STEPS = [
    ("fetch", ["fetch_raw.py", "--refresh"], "online"),
    ("build New England", ["build_new_england.py"], None),
    ("build Mid-Atlantic", ["build_mid_atlantic.py"], None),
    ("build regions 3-9", ["build_states.py"], None),
    ("geocode new addresses", ["fill_counties.py", "--geocode"], "online"),
    ("apply counties", ["fill_counties.py", "--apply"], None),
    ("canonicalise counties", ["fill_counties.py", "--canonicalise"], None),
    ("validate counties", ["fill_counties.py", "--validate"], None),
    ("independent cities", ["resolve_independent_cities.py"], None),
    ("standard types", ["add_standard_type.py", "--apply"], None),
    ("review worksheet", ["build_review_worksheet.py"], None),
    ("legal status", ["build_legal_status.py"], None),
    ("quick reference", ["build_quick_reference.py"], None),
    ("market", ["build_market.py"], None),
    ("site data", ["build_site_data.py"], None),
    ("verify", ["verify.py"], None),
]


def counts():
    out = collections.Counter()
    for t in TABLES:
        p = CLEAN / t
        if p.exists():
            with open(p, newline="", encoding="utf-8") as f:
                out.update(r["state"] for r in csv.DictReader(f))
    return out


def manifest_rows():
    if not MANIFEST.exists():
        return []
    with open(MANIFEST, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true",
                    help="skip the fetch and the geocoder; rebuild from what is on disk")
    ap.add_argument("--summary", help="write a markdown summary of the run to this file")
    args = ap.parse_args()

    started = datetime.now(timezone.utc)
    before, n_manifest = counts(), len(manifest_rows())
    ran, failed = [], None
    for name, cmd, needs in STEPS:
        if needs == "online" and args.offline:
            ran.append((name, "skipped (offline)", 0.0))
            continue
        t0 = time.time()
        print(f"\n=== {name}: python3 scripts/{' '.join(cmd)}", flush=True)
        proc = subprocess.run([sys.executable, str(ROOT / "scripts" / cmd[0]), *cmd[1:]],
                              cwd=ROOT, text=True, capture_output=True)
        out = (proc.stdout + proc.stderr).rstrip()
        print("\n".join(out.splitlines()[-12:]))
        secs = time.time() - t0
        if proc.returncode != 0:
            ran.append((name, f"FAILED (exit {proc.returncode})", secs))
            failed = (name, out.splitlines()[-25:])
            break
        ran.append((name, "ok", secs))

    after = counts()
    fetched = manifest_rows()[n_manifest:]
    by_status = collections.Counter(
        "changed" if r["status"] == "ok" else "unchanged" if r["status"] == "ok: unchanged"
        else "suspect" if r["status"].startswith("suspect") else "failed" for r in fetched)
    changed_states = sorted(s for s in set(before) | set(after) if before[s] != after[s])

    lines = [f"# Daily update, {started:%Y-%m-%d %H:%M} UTC",
             "", f"**Result: {'FAILED at ' + failed[0] if failed else 'ok'}**"
             + (" (offline: no fetch, no geocoder)" if args.offline else ""), "",
             "| Step | Result | Seconds |", "|---|---|---|"]
    lines += [f"| {n} | {r} | {s:.0f} |" for n, r, s in ran]
    if fetched:
        lines += ["", "**Sources:** " + ", ".join(f"{v} {k}" for k, v in sorted(by_status.items())),
                  ""]
        lines += [f"- {r['id']}: {r['status']}" for r in fetched
                  if r["status"] not in ("ok: unchanged",)]
    lines += ["", f"**Licence rows:** {sum(before.values()):,} before, {sum(after.values()):,} after."]
    if changed_states:
        lines += [f"- {s}: {before[s]:,} -> {after[s]:,}" for s in changed_states]
    if failed:
        lines += ["", "Last output of the failed step:", "", "```", *failed[1], "```"]
    text = "\n".join(lines) + "\n"
    print("\n" + text)
    if args.summary:
        pathlib.Path(args.summary).write_text(text, encoding="utf-8")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
