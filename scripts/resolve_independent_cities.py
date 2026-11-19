#!/usr/bin/env python3
"""Separate independent cities from the same-named county in the county column.

Census gives Baltimore city and Baltimore County, St. Louis city and St. Louis
County, and four Virginia pairs (Fairfax, Franklin, Richmond, Roanoke) the SAME
basename. The county column holds basenames, and fill_counties.py stripped the
"City" designator when it normalised spellings, so "Baltimore City" and
"Baltimore County" both became "Baltimore". A county page or count would then
add two separate jurisdictions together.

The rule, applied here and in fill_counties.py from now on:
  * an independent city is written as Census writes its county-equivalent name:
    "Baltimore city", "St. Louis city";
  * the county keeps its bare basename ("Baltimore"), as every other county does,
    and the row records that the city/county question was checked and how.

Each row is settled from the regulator's own county field in data/raw/, never
from a town name: a Baltimore mailing address is often in Baltimore County.
A row the raw data cannot settle has its county cleared, with the reason on the
row, because a wrong county is worse than a blank one.

Idempotent: a row already carrying the "city or county checked=" note is left alone.

Usage:
  python3 scripts/resolve_independent_cities.py [--dry-run]
"""
import argparse, collections, csv, html, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLEAN = ROOT / "data" / "clean"
TABLES = ["new_england_licences.csv", "mid_atlantic_licences.csv", "regions_3_to_9_licences.csv"]
NOTE = "city or county checked="


def ambiguous_basenames():
    pairs = collections.defaultdict(set)
    with open(ROOT / "data/raw/census_counties_by_state.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pairs[(r["state"], r["county_basename"])].add(r["county_name"])
    return {k for k, v in pairs.items() if len(v) > 1}


def missouri():
    g = json.loads((ROOT / "data/raw/missouri/mo_dcr_verified_dispensaries.geojson")
                   .read_text(encoding="utf-8"))
    return {str(x["properties"]["License"]).strip(): x["properties"]["County"]
            for x in g["features"]}


def street_key(addr):
    """House number plus the first word of the street: '35 E. Cross St' -> '35 e'."""
    m = re.match(r"\s*([\dA-Za-z-]*\d[\dA-Za-z-]*)\s+([A-Za-z]+)", addr)
    return f"{m.group(1).lower()} {m.group(2).lower()}" if m else ""


def maryland():
    page = (ROOT / "data/raw/maryland/mca_dispensary_locator_2026-11-12.html").read_text(
        encoding="utf-8", errors="replace")
    out = collections.defaultdict(set)
    for row in re.findall(r"<tr>(.*?)</tr>", page, re.S):
        cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        if len(cells) >= 3 and cells[2]:
            out[street_key(cells[1])].add(cells[2])
    return out


def decide(r, mo, md):
    """Return (new_county, note) or None when this row cannot be settled."""
    st, base = r["state"], r["county"]
    if st == "MO":
        raw = mo.get(r["licence_id"])
        src = "the DCR GIS County field"
    elif st == "MD":
        hits = md.get(street_key(r["street_address"]), set())
        raw = next(iter(hits)) if len(hits) == 1 else None
        src = "the MCA Dispensary Locator county column"
    else:
        raw = None
        src = ""
    if raw is None:
        return None
    if re.search(r"\bcity\s*$", raw, re.I):
        return f"{base} city", f"{NOTE}{base} city, not {base} County — {src} says '{raw}'"
    if raw.strip().lower() in (base.lower(), f"{base} county".lower()):
        return base, f"{NOTE}{base} County, not {base} city — {src} says '{raw}'"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    amb, mo, md = ambiguous_basenames(), missouri(), maryland()
    tally = collections.Counter()
    for name in TABLES:
        path = CLEAN / name
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        changed = 0
        for r in rows:
            if (r["state"], r["county"]) not in amb or NOTE in r["extra_details"]:
                continue
            got = decide(r, mo, md)
            if got:
                county, note = got
                tally[(r["state"], county)] += 1
            else:
                county, note = "", (
                    f"county unavailable={r['county']} is both {r['county']} city and "
                    f"{r['county']} County in {r['state']}, and the regulator's own data does not "
                    "say which; the county is cleared rather than guessed. "
                    f"(was: {r['county']}; {r['county_source']})")
                tally[(r["state"], "(cleared)")] += 1
            r["county"] = county
            if not county:
                r["county_source"] = ""
            r["extra_details"] = "; ".join(x for x in (r["extra_details"], note) if x)
            changed += 1
        if changed and not args.dry_run:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
        if changed:
            print(f"{name}: {changed} rows")
    for (st, c), n in sorted(tally.items()):
        print(f"  {n:>3}  {st}  {c}")
    if args.dry_run:
        print("(nothing written)")


if __name__ == "__main__":
    main()
