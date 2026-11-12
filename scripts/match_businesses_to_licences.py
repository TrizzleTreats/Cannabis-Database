#!/usr/bin/env python3
"""Match the business directory against the licence tables.

HANDOFF's rule: a business holding a state or tribal cannabis licence belongs
in the licence database, not the business directory. One of the open loose ends
is that this match was never done for California — "242 of 371 unverified; DCC
licence-list matching not done for any entry".

This reports; it does not delete. A directory entry that matches a licensee is
flagged with the licence numbers so the move can be judged entry by entry. The
matching is exact on a normalised name, never fuzzy: a false positive would
quietly drop a real directory entry, which is worse than a missed match.

Usage:
  python3 scripts/match_businesses_to_licences.py            # report
  python3 scripts/match_businesses_to_licences.py --apply    # also flag rows
"""
import argparse, collections, csv, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
LICENCE_TABLES = ["new_england_licences.csv", "mid_atlantic_licences.csv",
                  "regions_3_to_9_licences.csv"]
BUSINESSES = ROOT / "data" / "clean" / "businesses_master.csv"
OUT = ROOT / "data" / "clean" / "business_licence_matches.csv"

# Corporate forms and decorations that differ between a directory listing and a
# licence record for the same company.
SUFFIX = re.compile(r"\b(llc|l\.l\.c|inc|incorporated|corp|corporation|co|company|ltd|limited|"
                    r"lp|llp|pllc|plc|pc|pa|aps|apc|dba|the)\b", re.I)


def norm(name):
    n = (name or "").lower()
    n = re.sub(r"\(.*?\)", " ", n)          # drop parenthetical asides
    n = re.sub(r"[—–\-]+", " ", n)
    n = SUFFIX.sub(" ", n)
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # licensee name -> the licences carrying it
    by_name = collections.defaultdict(list)
    total = 0
    for t in LICENCE_TABLES:
        p = ROOT / "data/clean" / t
        if not p.exists():
            continue
        with open(p, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                total += 1
                for field in ("legal_name", "dba"):
                    n = norm(r.get(field, ""))
                    if len(n) >= 5:        # a 4-char name matches far too much
                        by_name[n].append((r["state"], r["licence_id"], r.get("legal_name", "")))
    print(f"licence rows: {total} | distinct normalised licensee names: {len(by_name)}")

    with open(BUSINESSES, encoding="utf-8") as f:
        biz = list(csv.DictReader(f))
    cols = list(biz[0].keys())

    matches, per_region = [], collections.Counter()
    for b in biz:
        n = norm(b["business_name"])
        if len(n) < 5:
            continue
        hits = by_name.get(n)
        if not hits:
            continue
        states = sorted({h[0] for h in hits})
        ids = [h[1] for h in hits][:6]
        matches.append({
            "business_id": b["business_id"], "region": b["region"],
            "business_name": b["business_name"], "category": b["category"],
            "audit_verdict": b["audit_verdict"], "normalised_name": n,
            "licence_states": ",".join(states), "licence_count": str(len(hits)),
            "licence_ids": "; ".join(ids),
            "licensee_name_as_published": hits[0][2],
        })
        per_region[b["region"]] += 1

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(matches[0].keys()) if matches else
                           ["business_id", "region", "business_name", "category", "audit_verdict",
                            "normalised_name", "licence_states", "licence_count", "licence_ids",
                            "licensee_name_as_published"])
        w.writeheader()
        for m in matches:
            w.writerow(m)
    print(f"\ndirectory entries whose name matches a licensee: {len(matches)}")
    print("by region:", dict(per_region.most_common()))
    print(f"wrote {OUT.relative_to(ROOT)}")
    for m in matches[:12]:
        print(f"   {m['region'][:13]:15} {m['business_name'][:40]:42} -> "
              f"{m['licence_count']} licence(s) in {m['licence_states']}")

    if a.apply and matches:
        by_id = {m["business_id"]: m for m in matches}
        changed = 0
        for b in biz:
            m = by_id.get(b["business_id"])
            if not m:
                continue
            note = (f"holds a state licence={m['licence_count']} licence(s) in "
                    f"{m['licence_states']} match this name ({m['licence_ids']}). HANDOFF puts a "
                    f"licensed operator in the licence database rather than the directory — review "
                    f"before moving, the match is on name alone")
            if "holds a state licence=" not in b["audit_note"]:
                b["audit_note"] = "; ".join(x for x in (b["audit_note"], note) if x)
                changed += 1
        with open(BUSINESSES, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for b in biz:
                w.writerow({c: b.get(c, "") for c in cols})
        print(f"\nflagged {changed} directory rows in businesses_master.csv")


if __name__ == "__main__":
    main()
