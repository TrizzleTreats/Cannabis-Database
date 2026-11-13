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
abbreviates them on the permit ("EGG HBR TWP", "EDGEWATER PRK") while spelling
them out in the HTML table ("Egg Harbor Township"). Rather than invent an
expansion table, each abbreviated town is matched against the full municipality
names the CRC itself lists for that same organisation, accepting a match only
when the abbreviation is a letter-by-letter subsequence of the full name and
exactly one candidate fits. Anything else is reported as unresolved.

Usage:
  python3 scripts/reconcile_nj_permits.py
"""
import csv, pathlib, re, sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
PERMITS = ROOT / "data" / "clean" / "nj_crc_permits.csv"
MASTER = ROOT / "data" / "clean" / "mid_atlantic_licences.csv"
LINK_INDEX = ROOT / "data" / "raw" / "new-jersey" / "permits" / "_link_index.csv"


def norm_org(name):
    """Compare organisation names without punctuation or corporate suffixes."""
    s = name.upper()
    s = re.sub(r"\(.*?\)", " ", s)                      # "(formerly Justice Grown NJ)"
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = re.sub(r"\b(LLC|L L C|INC|CORP|CORPORATION|CO|COMPANY|LP|LLP|"
               r"HOLDINGS|GROUP|THE)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def norm_town(name):
    s = name.upper()
    s = re.sub(r"[^A-Z ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def is_abbrev_of(short, full):
    """True if `short` is a token-wise abbreviation of `full`.

    Each token of the abbreviation must share its first letter with the matching
    token of the full name and be a subsequence of it: HBR of HARBOR, TWP of
    TOWNSHIP, PRK of PARK. Token counts must agree, which keeps "EGG HBR TWP"
    from matching "EGG HARBOR CITY".
    """
    a, b = norm_town(short).split(), norm_town(full).split()
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x == y:
            continue
        if not y.startswith(x[0]) or len(x) > len(y):
            return False
        it = iter(y)
        if not all(ch in it for ch in x):
            return False
    return True


def resolve_town(permit_town, candidates):
    """The CRC's own full spelling for an abbreviated town, or ('', reason)."""
    pt = norm_town(permit_town)
    exact = [c for c in candidates if norm_town(c) == pt]
    if len(exact) == 1:
        return exact[0], ""
    if len(exact) > 1:
        return exact[0], ""
    hits = [c for c in candidates if is_abbrev_of(permit_town, c)]
    if len(hits) == 1:
        return hits[0], ""
    if not hits:
        return "", "no listed location matches"
    return "", f"ambiguous between {len(hits)}: {', '.join(hits)}"


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

    print("\nHow they line up with the table's NJ rows")
    print("-----------------------------------------")
    print(f"  NJ rows in mid_atlantic_licences.csv    {len(nj)}")
    print(f"  of those, rows with a real licence id   "
          f"{sum(1 for r in nj if not r['licence_id'].startswith('NJ-'))}")

    # The organisation's own listed locations, as the CRC spells them.
    listed = defaultdict(set)
    for l in links:
        for town in (t.strip() for t in l["locations"].split(",")):
            if town:
                listed[norm_org(l["organisation"])].add(town)

    master_by_org = defaultdict(list)
    for r in nj:
        master_by_org[norm_org(r["legal_name"])].append(r)

    matched, unresolved, no_row, org_only = 0, [], [], 0
    claimed = set()
    for p in permits:
        key = norm_org(p["link_organisation"])
        rows = master_by_org.get(key, [])
        if not rows:
            no_row.append((p["permit_number"], p["link_organisation"], "organisation not in the table"))
            continue
        org_only += 1
        full, why = resolve_town(p["town"], sorted(listed.get(key, set())))
        hit = [r for r in rows if norm_town(r["town"]) == norm_town(full)] if full else []
        if len(hit) == 1:
            matched += 1
            claimed.add(id(hit[0]))
        elif full and not hit:
            no_row.append((p["permit_number"], f"{p['link_organisation']} / {p['town']}",
                           f"no row for town '{full}'"))
        elif full and len(hit) > 1:
            unresolved.append((p["permit_number"], p["town"], f"{len(hit)} rows share that town"))
        else:
            unresolved.append((p["permit_number"], p["town"], why))

    print(f"  permits whose organisation is in the table   {org_only}")
    print(f"  permits matched to exactly one row           {matched}")
    print(f"  table rows claimed by a permit               {len(claimed)}")
    print(f"  table rows with no permit                    {len(nj) - len(claimed)}")
    print(f"  permits whose town could not be resolved     {len(unresolved)}")
    for n, t, why in unresolved[:12]:
        print(f"    {n:10} '{t}'  {why}")
    if len(unresolved) > 12:
        print(f"    ... and {len(unresolved)-12} more")
    print(f"  permits describing a facility with no row    {len(no_row)}")
    for n, who, why in no_row[:12]:
        print(f"    {n:10} {who}  —  {why}")
    if len(no_row) > 12:
        print(f"    ... and {len(no_row)-12} more")

    print("\nCounty gaps")
    print("-----------")
    blank = [r for r in nj if not r["county"]]
    print(f"  NJ rows with no county today        {len(blank)}")
    towns_with_county = {}
    for p in permits:
        if p["county"]:
            towns_with_county.setdefault(norm_town(p["town"]), set()).add(p["county"])
    closable, conflicted = 0, 0
    for r in blank:
        hits = set()
        for p in permits:
            if norm_org(p["link_organisation"]) == norm_org(r["legal_name"]) and p["county"]:
                full, _ = resolve_town(p["town"], sorted(listed.get(norm_org(r["legal_name"]), set())))
                if full and norm_town(full) == norm_town(r["town"]):
                    hits.add(p["county"])
        if len(hits) == 1:
            closable += 1
        elif len(hits) > 1:
            conflicted += 1
    print(f"  closable from a permit for the same org+town   {closable}")
    print(f"  permits disagreeing on the county             {conflicted}")
    print(f"  distinct counties seen on permits             "
          f"{len({p['county'] for p in permits if p['county']})} of New Jersey's 21")

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
