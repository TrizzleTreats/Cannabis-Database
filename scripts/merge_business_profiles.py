#!/usr/bin/env python3
"""Group the business directory into one profile per business.

A national firm legitimately appears in the national directory and again in
every regional directory that covers it — Vicente LLP is in six of them. Those
are not errors in the parse; they are eleven separately audited documents
describing the same company. But a search for "Vicente LLP" must return one
result that serves six regions, not six results.

HANDOFF: "Licences tied to one company are grouped under a parent profile" and
"National firms appear in several regional directories ... merge under parent
profiles."

NOTHING IS DELETED. The licence tables solved the same one-entity-many-rows
problem with group_id / linked_group / licences_in_group, and the licence-match
work took the same care: "Nothing was deleted: the match is on name alone, and
a false positive would quietly drop a real directory entry, which is worse than
a missed match." So every row stays, each directory's own description, verdict,
evidence and sources intact, and five columns say how the rows relate:

  profile_id          shared by every row describing one business
  is_primary_profile  Y on the one row a public listing should show
  duplicate_of        the primary row's business_id, on the others
  entries_in_profile  how many directory entries describe this business
  regions_in_profile  every directory it appears in, '; '-joined

The public build therefore filters to is_primary_profile=Y and reads
regions_in_profile for "serves", rather than deleting anything.

The primary is the National entry where one exists, because that is the
parent-level profile HANDOFF asks for; otherwise the most complete row. Contact
detail is then merged ONTO the primary from its own group, filling blanks only
and never overwriting — a regional audit often found a phone the national one
did not, and vice versa.

Matching is on the normalised name only, which is deliberately conservative: a
shared name is strong evidence, and the alternative — fuzzy matching — risks
merging two genuinely different firms, which is worse than leaving a duplicate.

Usage:
  python3 scripts/merge_business_profiles.py [--dry-run] [--show N]
"""
import argparse, csv, html, pathlib, re, sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
MASTER = ROOT / "data" / "clean" / "businesses_master.csv"
NEW_COLUMNS = ["profile_id", "is_primary_profile", "duplicate_of",
               "entries_in_profile", "regions_in_profile"]
# Filled onto the primary from its group when the primary's own cell is blank.
MERGEABLE = ["website", "phone", "email", "address", "description", "states_served",
             "states_served_codes", "sub_type", "cannabis_focus", "credentials",
             "key_people_private", "evidence_links"]
SUFFIX = re.compile(r"\b(LLC|L\.L\.C|LLP|LP|INC|CORP|CORPORATION|CO|COMPANY|PC|PLLC|"
                    r"PA|THE|AND|GROUP|HOLDINGS|INCORPORATED|LTD)\b")


def norm(name):
    """The match key: the business name with decoration removed.

    Drops a bracketed flag, an " — place" tail, a " / alias", anything in
    parentheses, punctuation and corporate suffixes, so "Vicente LLP (formerly
    Vicente Sederberg LLP)" and "Vicente LLP" are one business.
    """
    s = html.unescape(html.unescape(name or ""))
    s = re.sub(r"\s*\[[^\]]*\]\s*", " ", s)
    s = re.split(r"\s+—\s+|\s+–\s+", s)[0]
    s = s.split(" / ")[0]
    s = re.sub(r"\(.*?\)", " ", s.upper())
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = SUFFIX.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


def completeness(row):
    return sum(1 for f in MERGEABLE if (row.get(f) or "").strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--show", type=int, default=12)
    args = ap.parse_args()

    rows = list(csv.DictReader(open(MASTER, newline="", encoding="utf-8")))
    cols = [c for c in rows[0]] + [c for c in NEW_COLUMNS if c not in rows[0]]

    groups = defaultdict(list)
    for r in rows:
        groups[norm(r["business_name"])].append(r)

    merged_cells = Counter()
    multi = 0
    for key, members in sorted(groups.items()):
        if not key:
            # No usable name: left ungrouped rather than lumped together.
            for r in members:
                r["profile_id"], r["is_primary_profile"] = "", "Y"
                r["duplicate_of"], r["entries_in_profile"] = "", "1"
                r["regions_in_profile"] = r["region"]
            continue
        profile_id = "BP-" + re.sub(r"[^A-Z0-9]+", "-", key)[:40].strip("-")
        regions = sorted({r["region"] for r in members})
        # National is the parent-level profile when it exists; else the fullest row.
        national = [r for r in members if r["region"] == "National"]
        primary = max(national or members, key=completeness)
        if len(members) > 1:
            multi += 1
        for r in members:
            r["profile_id"] = profile_id
            r["entries_in_profile"] = str(len(members))
            r["regions_in_profile"] = "; ".join(regions)
            if r is primary:
                r["is_primary_profile"] = "Y"
                r["duplicate_of"] = ""
            else:
                r["is_primary_profile"] = "N"
                r["duplicate_of"] = primary["business_id"]
        # Where two directories put the same business in different categories,
        # say so on the row rather than letting the primary's category stand as
        # though it were agreed. The category itself is not changed: picking a
        # winner here would bury a real disagreement between two audits.
        cats = sorted({r["category"] for r in members if r["category"]})
        if len(cats) > 1:
            others = [c for c in cats if c != primary["category"]]
            note = (f"category disagreement=this business is categorised "
                    f"{' and '.join(repr(c) for c in others)} in "
                    f"{', '.join(sorted({r['region'] for r in members if r['category'] in others}))}, "
                    f"against {primary['category']!r} here — not reconciled")
            if "category disagreement=" not in (primary.get("audit_note") or ""):
                primary["audit_note"] = "; ".join(
                    x for x in ((primary.get("audit_note") or "").strip(), note) if x)

        # Fill the primary's blanks from its own group. Never overwrite.
        for f in MERGEABLE:
            if (primary.get(f) or "").strip():
                continue
            for r in members:
                if r is primary:
                    continue
                v = (r.get(f) or "").strip()
                if v:
                    primary[f] = v
                    merged_cells[f] += 1
                    break

    primaries = [r for r in rows if r["is_primary_profile"] == "Y"]
    print(f"{len(rows)} directory entries -> {len(primaries)} business profiles")
    print(f"  profiles with more than one entry: {multi}")
    print(f"  entries marked as a duplicate of another: {len(rows) - len(primaries)}")
    print("\n  cells filled onto a primary from its own group:")
    for f, n in merged_cells.most_common():
        print(f"    {f:22} {n}")

    widest = sorted((r for r in primaries if int(r["entries_in_profile"]) > 1),
                    key=lambda r: -int(r["entries_in_profile"]))
    print(f"\n  the most widely listed businesses:")
    for r in widest[:args.show]:
        print(f"    {r['entries_in_profile']}x {r['business_name'][:38]:40} {r['regions_in_profile'][:72]}")

    # A profile whose members disagree on category is worth a human look.
    clashes = []
    for key, members in groups.items():
        cats = {r["category"] for r in members if r["category"]}
        if len(cats) > 1:
            clashes.append((members[0]["business_name"], sorted(cats)))
    print(f"\n  profiles whose directories disagree on the category: {len(clashes)}")
    for name, cats in clashes[:8]:
        print(f"    {name[:40]:42} {cats}")

    if args.dry_run:
        print("\n(nothing written)")
        return
    with open(MASTER, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    print(f"\nwrote {MASTER.relative_to(ROOT)} — {len(cols)} columns")


if __name__ == "__main__":
    main()
