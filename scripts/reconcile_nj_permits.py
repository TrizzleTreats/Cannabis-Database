#!/usr/bin/env python3
"""Reconcile New Jersey's permit PDFs against the NJ rows already in the table.

This changes nothing. It answers the questions that have to be settled before
the master table is touched:

  * how many permits the PDFs actually publish, and how many distinct numbers
  * which of the 517 listed organisations have a permit PDF and which do not
  * how the permits line up with the existing organisation-x-location rows
  * how many of NJ's county gaps a permit closes
  * which permits describe a facility the current table has no row for

The join is on organisation plus town, and the towns need care: the CRC
abbreviates them on the permit ("EGG HBR TWP") while spelling them out in the
HTML table ("Egg Harbor Township"). The matching rules live in scripts/nj_towns.py,
shared with the builder and the county check so no two of them can disagree.
Anything they cannot resolve confidently is reported as unresolved, not guessed.

Usage:
  python3 scripts/reconcile_nj_permits.py
"""
import csv, pathlib, sys
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from nj_towns import is_abbrev_of, norm_org, norm_town, resolve_town

ROOT = pathlib.Path(__file__).resolve().parent.parent
PERMITS = ROOT / "data" / "clean" / "nj_crc_permits.csv"
MASTER = ROOT / "data" / "clean" / "mid_atlantic_licences.csv"
LINK_INDEX = ROOT / "data" / "raw" / "new-jersey" / "permits" / "_link_index.csv"


def main():
    for p in (PERMITS, MASTER, LINK_INDEX):
        if not p.exists():
            sys.exit(f"missing {p.relative_to(ROOT)}")
    records = list(csv.DictReader(open(PERMITS, newline="", encoding="utf-8")))
    # Only licences are licences. The consumption-area endorsements ride along
    # in the same file and are reported separately, never counted as licences.
    permits = [r for r in records if r["record_kind"] == "licence"]
    endorsements = [r for r in records if r["record_kind"] != "licence"]
    links = list(csv.DictReader(open(LINK_INDEX, newline="", encoding="utf-8")))
    master = list(csv.DictReader(open(MASTER, newline="", encoding="utf-8")))
    nj = [r for r in master if r["state"] == "NJ"]

    print("What the permit PDFs publish")
    print("----------------------------")
    print(f"  permits parsed                     {len(permits)}")
    print(f"  distinct permit numbers            {len({p['permit_number'] for p in permits})}")
    print(f"  organisations with >=1 permit      {len({p['link_organisation'] for p in permits})}")
    print(f"  PDFs that yielded them             {len({p['pdf_filename'] for p in permits})}")
    per_pdf = Counter(p["pdf_filename"] for p in permits)
    print(f"  permits per PDF                    "
          f"{min(per_pdf.values())}-{max(per_pdf.values())} "
          f"(median {sorted(per_pdf.values())[len(per_pdf)//2]})")
    print(f"  programme                          "
          f"{dict(Counter(p['program'] for p in permits))}")
    print(f"  consumption-area endorsements      {len(endorsements)} "
          f"({', '.join(e['permit_number'] for e in endorsements)})")

    have = {p["pdf_filename"] for p in permits}
    gap = [l for l in links if l["filename"] not in have]
    print(f"\n  listed organisations with no permit parsed: {len(gap)}")
    for l in gap[:12]:
        print(f"    {l['organisation']}  ({l['filename']})")
    if len(gap) > 12:
        print(f"    ... and {len(gap)-12} more")

    print("\nEvery permit is represented in the master table")
    print("-----------------------------------------------")
    # Before the migration this joined on organisation and town, because the
    # table held no licence numbers. It holds them now, so the join is on the
    # number - the only key that cannot be ambiguous. A number printed on two
    # permits at one premises appears as ~1 and ~2, so the suffix is stripped
    # before comparing.
    def base(licence_id):
        return licence_id.split("~")[0]

    in_table = {}
    for r in nj:
        in_table.setdefault(base(r["licence_id"]), []).append(r)
    permit_numbers = Counter(p["permit_number"] for p in permits)

    missing = [n for n in permit_numbers if n not in in_table]
    print(f"  permits published                 {len(permits)} ({len(permit_numbers)} numbers)")
    print(f"  NJ rows in the master table       {len(nj)}")
    print(f"  rows carrying a real licence id   {sum(1 for r in nj if not r['licence_id'].startswith('NJ-'))}")
    print(f"  permit numbers absent from table  {len(missing)}")
    for n in missing[:10]:
        print(f"    {n}")

    # The reverse direction: a row must not claim a number the permits do not.
    invented = [r for r in nj if not r["licence_id"].startswith("NJ-")
                and base(r["licence_id"]) not in permit_numbers]
    print(f"  rows claiming an unpublished id   {len(invented)}")
    for r in invented[:10]:
        print(f"    {r['licence_id']}  {r['legal_name']}")

    # And the row count has to decompose exactly.
    suffixed = sum(1 for r in nj if "~" in r["licence_id"])
    nopermit = sum(1 for r in nj if r["licence_id"].startswith("NJ-NOPERMIT"))
    print(f"  of those rows: {len(nj) - nopermit} permit rows ({suffixed} with a ~n suffix for a "
          f"shared premises number) + {nopermit} CRC-listed locations with no permit")

    print("\nWhat the table now carries that the HTML list never did")
    print("-------------------------------------------------------")
    for label, field in (("real licence number", "licence_id"), ("street address", "street_address"),
                         ("county", "county"), ("full ISO expiry date", "expiry_date")):
        if field == "licence_id":
            have = sum(1 for r in nj if not r["licence_id"].startswith("NJ-"))
        elif field == "expiry_date":
            have = sum(1 for r in nj if len(r["expiry_date"]) == 10)
        else:
            have = sum(1 for r in nj if r[field])
        print(f"  {label:22} {have}/{len(nj)}")

    print("\nCounty, and where each one came from")
    print("------------------------------------")
    blank = [r for r in nj if not r["county"]]
    print(f"  NJ rows with no county   {len(blank)}  (88 of 586 before the permits were read)")
    for r in blank:
        print(f"    {r['licence_id']:16} {r['legal_name'][:30]:32} {r['town']}")
    for src, n in Counter(r["county_source"] for r in nj).most_common():
        print(f"  {n:5}  {src[:92] or '(none)'}")
    disputed = [r for r in nj if "county disputed=" in r["extra_details"]]
    corrected = [r for r in nj if "county as printed on the permit=" in r["extra_details"]]
    print(f"\n  {len(corrected)} rows publish a county the Census geocoder corrected, with the "
          f"permit's printed value kept on the row")
    print(f"  {len(disputed)} row is disputed and keeps the regulator's printed value:")
    for r in disputed:
        print(f"    {r['licence_id']} {r['legal_name']} — published as {r['county']}")

    print("\nLoose ends this settles")
    print("-----------------------")
    for name in ("Talaria", "Crested River"):
        hits = [p for p in permits if name.lower() in p["facility_name"].lower()
                or name.lower() in p["link_organisation"].lower()]
        for h in hits:
            print(f"  {name}: {h['permit_number']} — {h['licence_class_state']}, "
                  f"{h['facility_name']}, {h['town']} ({h['county']}), "
                  f"expires {h['expiration_date']}")
        if not hits:
            print(f"  {name}: no permit PDF found")


if __name__ == "__main__":
    main()
