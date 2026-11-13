#!/usr/bin/env python3
"""Check every New Jersey permit's printed county against the Census geocoder.

The permits print a county on the facility address, and 11 of them disagree with
the CRC's own County/Municipality table. Some of those are the same-name
collision HANDOFF warns about (Franklin Borough in Sussex against Franklin
Township in Warren) rather than an error, and that table covers only the 230
municipalities that have acted on cannabis, so it cannot settle the rest.

The permits carry a full street address, which the CRC's HTML list never did, so
the US Census geocoder can resolve each one at address level - the same official
route scripts/fill_counties.py already uses, sharing its cache so a re-run is
free and the provenance stays on disk.

Nothing is rewritten here. Two columns are added to the permits file:

  county_geocoded   what the Census geocoder returned for that street address
  geocoded_address  the address it actually matched, as evidence
  county_check      agrees / differs-confirmed / differs-unresolved / no match /
                    not geocodable

A row where they differ keeps BOTH counties. The verdict distinguishes the two
cases that matter: where the permit's own printed ZIP equals the ZIP of the
address the geocoder matched, the two agree on the building and only the
permit's county field is wrong; where the ZIPs differ, the geocoder matched
somewhere else and decides nothing, so that row stays unresolved.

Addresses are tried as the permit spells them first. The CRC abbreviates towns
("EGG HBR TWP"), so anything that fails to match is retried with the full
municipality name the CRC itself lists for that organisation - never an
expansion invented here.

Usage:
  python3 scripts/verify_nj_permit_counties.py [--limit N] [--dry-run]
"""
import argparse, csv, pathlib, re, sys, time
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fill_counties as fc
from nj_towns import norm_org, resolve_town

ROOT = pathlib.Path(__file__).resolve().parent.parent
PERMITS = ROOT / "data" / "clean" / "nj_crc_permits.csv"
LINK_INDEX = ROOT / "data" / "raw" / "new-jersey" / "permits" / "_link_index.csv"
NEW_COLUMNS = ["county_geocoded", "county_check", "geocoded_address"]

# A disagreement is only decided when the two sources agree on the ADDRESS and
# differ on nothing but the county field. The permit prints its own ZIP, so it
# can corroborate the geocoder against itself: where the permit's ZIP equals the
# ZIP of the address the geocoder matched, both describe the same building and
# the county field on the permit is simply wrong. Where the ZIPs differ, the
# geocoder matched a different point and settles nothing - that row keeps the
# permit's county and is reported as unresolved rather than silently rewritten.
AGREES = "agrees"
DIFFERS_CONFIRMED = "differs — same address, permit county wrong"
DIFFERS_UNRESOLVED = "differs — geocoder matched a different address, unresolved"
NO_MATCH = "no match"
NOT_GEOCODABLE = "not geocodable"


def listed_locations():
    """Each organisation's municipalities, as the CRC spells them in its HTML."""
    out = {}
    with open(LINK_INDEX, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = norm_org(row["organisation"])
            for town in (t.strip() for t in row["locations"].split(",")):
                if town:
                    out.setdefault(key, set()).add(town)
    return out


def zip_of(address):
    """The ZIP the geocoder's matched address ends with."""
    found = re.findall(r"\b(\d{5})\b", address or "")
    return found[-1] if found else ""


def lookup(street, town, cache, stats, dry_run):
    """Cached geocode. Returns (county, matched_address)."""
    key = f"{street}|{town}|NJ"
    hit = cache.get(key)
    if hit:
        stats["cached"] += 1
        return hit["county"], hit.get("matched_address", "")
    if dry_run:
        stats["would fetch"] += 1
        return "", ""
    try:
        county, matched, status = fc.geocode(street, town, "NJ")
    except Exception as exc:
        stats["error"] += 1
        return "", f"error: {type(exc).__name__}"
    cache[key] = {"key": key, "street": street, "town": town, "state": "NJ",
                  "county": county, "matched_address": matched, "status": status,
                  "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    stats["fetched"] += 1
    time.sleep(0.25)  # be a polite guest on a free federal service
    return county, matched


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(PERMITS, newline="", encoding="utf-8")))
    fields = [c for c in rows[0]] + [c for c in NEW_COLUMNS if c not in rows[0]]
    listed = listed_locations()
    cache = fc.load_cache()
    stats = {"cached": 0, "fetched": 0, "would fetch": 0, "error": 0}
    counts = {AGREES: 0, DIFFERS_CONFIRMED: 0, DIFFERS_UNRESOLVED: 0,
              NO_MATCH: 0, NOT_GEOCODABLE: 0}
    differs, retried = [], 0

    todo = rows[: args.limit] if args.limit else rows
    for i, r in enumerate(todo, 1):
        street, town = r["street_address"].strip(), r["town"].strip()
        if not street or not town:
            r["county_geocoded"], r["county_check"] = "", NOT_GEOCODABLE
            r["geocoded_address"] = ""
            counts[NOT_GEOCODABLE] += 1
            continue
        county, matched = lookup(street, town, cache, stats, args.dry_run)
        if not county:
            # The permit abbreviates the town. Retry with the CRC's own full
            # spelling for that organisation, if exactly one fits.
            full, _ = resolve_town(town, sorted(listed.get(norm_org(r["link_organisation"]), set())))
            if full and full.upper() != town.upper():
                retried += 1
                county, matched = lookup(street, full, cache, stats, args.dry_run)
        r["county_geocoded"], r["geocoded_address"] = county, matched
        if not county:
            r["county_check"] = NO_MATCH
        elif county.upper() == r["county"].strip().upper():
            r["county_check"] = AGREES
        elif zip_of(matched) and zip_of(matched) == r["zip"].strip():
            r["county_check"] = DIFFERS_CONFIRMED
            differs.append(r)
        else:
            r["county_check"] = DIFFERS_UNRESOLVED
            differs.append(r)
        counts[r["county_check"]] += 1
        if i % 100 == 0:
            print(f"  ... {i}/{len(todo)}  cached={stats['cached']} fetched={stats['fetched']}")

    if not args.dry_run:
        fc.save_cache(cache)
        with open(PERMITS, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in fields})

    print(f"\n{len(todo)} permit addresses checked against the Census geocoder")
    print(f"  cache hits {stats['cached']}, fetched {stats['fetched']}, "
          f"errors {stats['error']}, retried with the CRC's full town name {retried}")
    for k, v in counts.items():
        print(f"  {v:5}  {k}")
    if differs:
        print(f"\nthe {len(differs)} where the permit and the geocoder disagree:")
        for r in differs:
            verdict = "permit county wrong" if r["county_check"] == DIFFERS_CONFIRMED \
                else "UNRESOLVED, permit county kept"
            print(f"  {r['permit_number']:11} {r['facility_name'][:28]:30} "
                  f"{r['town']:14} permit={r['county']:11} census={r['county_geocoded']:11} "
                  f"zip {r['zip']}/{zip_of(r['geocoded_address']) or '?'}  {verdict}")
    if not args.dry_run:
        print(f"\nwrote county_geocoded and county_check to {PERMITS.relative_to(ROOT)}")
        print(f"cache: {fc.CACHE.relative_to(ROOT)} ({len(cache)} addresses)")


if __name__ == "__main__":
    main()
