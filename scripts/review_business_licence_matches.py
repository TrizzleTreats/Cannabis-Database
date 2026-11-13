#!/usr/bin/env python3
"""Review the directory entries whose name matches a licensee.

match_businesses_to_licences.py finds them, deliberately on an exact normalised
name and never fuzzily, and deliberately deletes nothing: "a false positive
would quietly drop a real directory entry, which is worse than a missed match."
That leaves the judgement to be made, which is what this does.

HANDOFF: "Businesses that hold a state or tribal cannabis licence, or operate
under another company's licence, go in the licence database, not the business
directory (link them to the licensee's parent profile)." So a match matters, but
only if it is really the same business — and the matcher gives two clues about
that, because it matches on the licensee's legal name AND on its DBA:

  legal name matched   the licensee IS a company of that name. Strong.
  only the DBA matched the licensee is some other company trading under that
                       name. That is exactly HANDOFF's "operates under another
                       company's licence" — or a different business that happens
                       to trade under the same words.

The second clue is geography. A licence in a state the directory entry has
nothing to do with is evidence against, not for: "A1 Organics" is a composting
firm at 16350 WCR 76, Eaton, Colorado, and the matching licence is a California
cultivation licence in Trinity County. Same words, almost certainly not the
same company.

So each match gets one of four verdicts, with the evidence recorded beside it:

  same business          legal name matched and the geography agrees
  geography unknown      legal name matched but the directory gives the business
                         no state and no address, so there is nothing to check
                         against. Silence is not confirmation
  trades under another   only the DBA matched — HANDOFF's case, but which brand
                         it is needs a person
  likely different       the name matched but the geography contradicts it

A licensee often registers a shorter form of its trading name, so a legal name
counts as matching when one name's words are a subset of the other's: "Gaiaca,
LLC" is the licensee behind "GAIACA Waste Revitalization".

Nothing is deleted and no directory entry is moved. The verdict and its reason
are written to data/clean/business_licence_matches.csv and flagged on the
business row, so the public build can hold back an entry that is really a
licensee while a person settles the uncertain ones.

Usage:
  python3 scripts/review_business_licence_matches.py [--dry-run]
"""
import argparse, csv, pathlib, re, sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
MATCHES = ROOT / "data" / "clean" / "business_licence_matches.csv"
MASTER = ROOT / "data" / "clean" / "businesses_master.csv"
TABLES = ["new_england_licences.csv", "mid_atlantic_licences.csv",
          "regions_3_to_9_licences.csv"]

SAME = "same business — belongs in the licence database"
DBA = "trades under another company's licence — needs a person"
DIFFERENT = "likely a different business with the same name"
UNKNOWN = "name matches, geography unknown — needs a person"
STATE = re.compile(r"\b([A-Z]{2})\b")
NATIONAL = re.compile(r"national|multi-state|nationwide|all states|statewide", re.I)


def norm(name):
    s = re.sub(r"\(.*?\)", " ", (name or "").upper())
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = re.sub(r"\b(LLC|LLP|LP|INC|CORP|CORPORATION|CO|COMPANY|PC|PLLC|PA|THE|AND|"
               r"HOLDINGS|GROUP|LTD|DBA)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def states_of(biz):
    """Every state the directory itself associates with this business."""
    found = set()
    for field in ("home_state", "states_served_codes"):
        found |= set(STATE.findall((biz.get(field) or "").upper()))
    tail = re.search(r",\s*([A-Z]{2})\s*\d{5}", (biz.get("address") or "").upper())
    if tail:
        found.add(tail.group(1))
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    matches = list(csv.DictReader(open(MATCHES, newline="", encoding="utf-8")))
    biz_rows = list(csv.DictReader(open(MASTER, newline="", encoding="utf-8")))
    biz = {r["business_id"]: r for r in biz_rows}
    licences = {}
    for name in TABLES:
        for r in csv.DictReader(open(ROOT / "data/clean" / name, encoding="utf-8")):
            licences[r["licence_id"]] = r

    verdicts = Counter()
    for m in matches:
        b = biz.get(m["business_id"], {})
        ids = [x.strip() for x in m["licence_ids"].split(";") if x.strip()]
        rows = [licences[i] for i in ids if i in licences]
        lic_states = sorted({r["state"] for r in rows})
        # A licensee often registers a shorter form of its trading name:
        # "Gaiaca, LLC" against "GAIACA Waste Revitalization". Treat one name as
        # the other when its words are a subset, not only when they are equal.
        a, b_name = norm(m["licensee_name_as_published"]).split(), norm(m["business_name"]).split()
        legal_match = bool(a) and bool(b_name) and (
            set(a) <= set(b_name) or set(b_name) <= set(a))
        own = states_of(b)
        national = bool(NATIONAL.search((b.get("states_served") or "") + " " + (b.get("scope") or "")))
        geography_ok = national or bool(own & set(lic_states))

        if not legal_match:
            verdict = DBA
            why = (f"the licence is held by {m['licensee_name_as_published']!r}, not by this "
                   f"business — the names agree only on the licensee's trading name")
        elif not own and not national:
            # The directory gives this entry no state and no address, so there
            # is nothing to agree or disagree with. Silence is not confirmation.
            verdict = UNKNOWN
            why = (f"the licensee's legal name is this business's name, but the directory gives "
                   f"the business no state or address, so there is nothing to check the "
                   f"licence state ({', '.join(lic_states)}) against")
        elif geography_ok:
            verdict = SAME
            why = (f"the licensee's own legal name is this business's name, and its licence "
                   f"state{'s' if len(lic_states) > 1 else ''} "
                   f"({', '.join(lic_states)}) "
                   + ("is consistent with a business the directory calls national"
                      if national and not (own & set(lic_states))
                      else f"match the states the directory gives it ({', '.join(sorted(own)) or 'none given'})"))
        else:
            verdict = DIFFERENT
            why = (f"the name matches but the geography does not: the directory places this "
                   f"business in {', '.join(sorted(own))} while the licence is in "
                   f"{', '.join(lic_states)}")
        m["review"] = verdict
        m["review_basis"] = why
        m["licence_states_checked"] = ", ".join(lic_states)
        m["directory_states"] = ", ".join(sorted(own))
        verdicts[verdict] += 1

        if b:
            note = f"licence match review={verdict}: {why}"
            existing = b.get("audit_note") or ""
            if "licence match review=" not in existing:
                b["audit_note"] = "; ".join(x for x in (existing.strip(), note) if x)

    print(f"{len(matches)} matched entries reviewed\n")
    for v, n in verdicts.most_common():
        print(f"  {n:3}  {v}")
    for v in (SAME, UNKNOWN, DBA, DIFFERENT):
        print(f"\n{v}:")
        for m in matches:
            if m["review"] == v:
                print(f"    {m['business_name'][:44]:46} {m['licence_states_checked']:10} "
                      f"<- {m['licensee_name_as_published'][:34]}")

    if args.dry_run:
        print("\n(nothing written)")
        return
    cols = [c for c in matches[0]]
    with open(MATCHES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for m in matches:
            w.writerow({c: m.get(c, "") for c in cols})
    bcols = [c for c in biz_rows[0]]
    with open(MASTER, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=bcols)
        w.writeheader()
        for r in biz_rows:
            w.writerow({c: r.get(c, "") for c in bcols})
    print(f"\nwrote {MATCHES.relative_to(ROOT)} and flagged the business rows")


if __name__ == "__main__":
    main()
