#!/usr/bin/env python3
"""Collect everything that needs a person's judgement into one worksheet.

Several decisions in this project cannot be made by a script, and they are
scattered across STATUS, business_licence_matches.csv and the licence tables.
This gathers them into data/clean/review_worksheet.csv — one row per decision,
each with the exact question, the page to open, and what the record says now —
so the work is reading and deciding rather than hunting.

Nothing here changes any data. Filling in the `decision` column and telling
Claude is what applies it.

Three kinds, most decisive first:

  licence match   22 directory entries whose name matches a licensee. 6 are
                  settled on evidence; the other 16 are not. HANDOFF puts a
                  business that holds a licence, or operates under another
                  company's, in the licence database rather than the directory,
                  so each needs a yes or no.
  repealed class  Vermont's 2 "Integrated" licences. Act 176 repealed that
                  class on 1 July 2026 (§909 repealed; §901(d) now lists six
                  types), so their current status needs checking against the
                  CCB's own portal.
  unverified      the directory entries an audit could not confirm. They are
                  already held back from the public site; a decision here is
                  what releases one.

Usage:
  python3 scripts/build_review_worksheet.py [--kinds licence-match,repealed-class]
"""
import argparse, csv, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLEAN = ROOT / "data" / "clean"
OUT = CLEAN / "review_worksheet.csv"
FIELDS = ["item_id", "kind", "priority", "subject", "the_question", "what_the_record_says",
          "open_this", "decision", "notes"]
SETTLED = "same business — belongs in the licence database"


def licence_matches():
    path = CLEAN / "business_licence_matches.csv"
    if not path.exists():
        return []
    out = []
    for i, m in enumerate(csv.DictReader(open(path, newline="", encoding="utf-8")), 1):
        if m["review"] == SETTLED:
            continue        # already decided on evidence
        dba_only = m["review"].startswith("trades under")
        out.append({
            "item_id": f"LM-{i:02d}",
            "kind": "licence match",
            "priority": "1",
            "subject": f'{m["business_name"]} ({m["region"]}, {m["category"]})',
            "the_question": (
                f'Is this the same business as licensee "{m["licensee_name_as_published"]}" in '
                f'{m["licence_states_checked"]}? If yes it belongs in the licence database, not '
                f'the directory. If it only shares a name, say so and the match is dropped.'
                if dba_only else
                f'The licence holder is named "{m["licensee_name_as_published"]}" in '
                f'{m["licence_states_checked"]}, and the directory gives this business no state '
                f'or address, so the two could not be checked against each other. Same business?'),
            "what_the_record_says": m["review_basis"],
            "open_this": m.get("licence_ids", ""),
            "decision": "",
            "notes": "",
        })
    return out


def repealed_class():
    out = []
    for name in ("new_england_licences.csv",):
        path = CLEAN / name
        if not path.exists():
            continue
        for r in csv.DictReader(open(path, newline="", encoding="utf-8")):
            if r["state"] == "VT" and r["category"] == "Integrated":
                out.append({
                    "item_id": f'RC-{r["licence_id"]}',
                    "kind": "repealed class",
                    "priority": "1",
                    "subject": f'{r["legal_name"]} — {r["town"] or "town not published"}',
                    "the_question": (
                        "Vermont's Act 176 repealed the Integrated licence class on 1 July 2026 "
                        "(§909 repealed; §901(d) now lists six types). Does the CCB's own portal "
                        "still show this licence, and under what class now?"),
                    "what_the_record_says": f'{r["licence_type"]} · {r["status"] or "no status published"}'
                                            f' · standard_status {r["standard_status"] or "(empty)"}',
                    "open_this": r["source_url"],
                    "decision": "",
                    "notes": "",
                })
    return out


def unverified():
    path = CLEAN / "businesses_master.csv"
    if not path.exists():
        return []
    out = []
    for r in csv.DictReader(open(path, newline="", encoding="utf-8")):
        if r.get("is_primary_profile") != "Y":
            continue
        verdict = (r["audit_verdict"] or "").strip().lower()
        flag = (r["needs_verify"] or "").strip().lower()
        if not (verdict.startswith("unverif") or flag in ("true", "yes", "y")):
            continue
        out.append({
            "item_id": f'UV-{r["business_id"]}',
            "kind": "unverified",
            "priority": "3",
            "subject": f'{r["business_name"]} ({r["region"]}, {r["category"]})',
            "the_question": "Does this business exist, serve the cannabis or hemp industry, and "
                            "are its details right? A yes releases it to the public site.",
            "what_the_record_says": (r["audit_note"] or r["audit_verdict"] or "")[:300],
            "open_this": r["website"] or r["evidence_links"] or r["sources"],
            "decision": "",
            "notes": "",
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kinds", default="licence-match,repealed-class,unverified")
    args = ap.parse_args()
    wanted = {k.strip() for k in args.kinds.split(",")}

    rows = []
    if "licence-match" in wanted:
        rows += licence_matches()
    if "repealed-class" in wanted:
        rows += repealed_class()
    if "unverified" in wanted:
        rows += unverified()
    rows.sort(key=lambda r: (r["priority"], r["item_id"]))

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    by_kind = {}
    for r in rows:
        by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1
    print(f"{len(rows)} decisions -> {OUT.relative_to(ROOT)}")
    for kind, n in sorted(by_kind.items(), key=lambda kv: -kv[1]):
        print(f"  {n:4}  {kind}")
    urgent = [r for r in rows if r["priority"] == "1"]
    print(f"\n  {len(urgent)} are priority 1 — the ones that change what the database says:")
    for r in urgent:
        print(f"    {r['item_id']:14} {r['subject'][:66]}")


if __name__ == "__main__":
    main()
