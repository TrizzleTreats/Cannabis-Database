#!/usr/bin/env python3
"""Fill the California business rows' contact detail from the report's own prose.

The California directory is two documents in one. PART 1 is an audit table —
business, sub-region, verdict, what was checked — and that is what
build_businesses.py parsed, which is why all 371 California rows carry a verdict
and none carries a website, phone, email, address or description. PART 2, the
"CORRECTED REWRITE", is where the contact detail lives.

Part 2 uses three layouts, none of them tabular:

  A  a numbered heading, then "Label:" / value on separate lines
  B  an id heading ("9-11b-01 — Humboldt Hydroponics — Eureka") then
     <ul><li><strong>Label:</strong> value</li>
  C  one paragraph per business, opening <strong>Name — ... — Verdict: X.</strong>
     with the labels inline and separated by full stops
  D  "Row 1 — Spokes Digital — Unverified" headings, sometimes with the
     report's own row id in the middle ("Row 43 — 5-11a-1 — Tact Firm")

So the parse keys on the LABELS, which are consistent, rather than on the
markup, which is not. The labels themselves vary in wording and both forms are
accepted: Address / Street address, Areas served / Areas, Social / Social links,
Credential / Credential / DCC, Evidence link / Evidence.

Nothing is invented and no placeholder is published. "Not published — Verify"
is the report's own wording for a field it could not confirm, and it appears
1,359 times in Part 2; every such value is treated as absent, because
CLAUDE.md forbids letting a placeholder become a published value. A field
already filled on a row is never overwritten.

People's names go to key_people_private only — they are individuals, and
CLAUDE.md keeps individuals' details in private columns.

Usage:
  python3 scripts/fill_california_contacts.py [--dry-run] [--report]
"""
import argparse, csv, html, pathlib, re, sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPORT = ROOT / "reports" / "businesses" / "california-businesses-audited.html"
MASTER = ROOT / "data" / "clean" / "businesses_master.csv"

# Every label Part 2 uses, longest first so "Street address" wins over "Address"
# and "Areas served" over "Areas".
LABELS = [
    "Standard category", "Cannabis / hemp tag", "Source Verify note", "Credential / DCC",
    "County / city", "City / County", "Street address", "Social links", "Areas served",
    "Evidence link", "Scope tag", "Audit note", "Description", "Credential", "Sub-region",
    "Subtype", "Sub-type", "Evidence", "Verdict", "Website", "Address", "Areas", "People",
    "Social", "Phone", "Email", "Scope", "County", "Type", "Tag", "DBA", "Source",
]
LABEL_RE = re.compile(r"\b(" + "|".join(re.escape(l) for l in LABELS) + r")\s*:", re.I)

# The report's own ways of saying a field is NOT confirmed. All treated as
# absent, and the leading "Verify" matters as much as "Not published": the
# report writes "Phone: Verify — conflict: directory (415) 651-4613 ...; opened
# page footer 707-380-7058" and "Email: Verify — opened page footer lists
# jared@harris-sliwoski.com, a non-schwasslaw.com domain". A regex will happily
# pull a phone- or email-shaped string out of either, and publishing it would
# be publishing a value the auditor explicitly declined to confirm.
NOT_PUBLISHED = re.compile(r"^\s*(not\s+published|none\s+published|not\s+stated|"
                           r"not\s+listed|no\s+website|n/?a|verify|unverified|"
                           r"unknown|conflict)\b", re.I)

FILLABLE = {"website": ["Website"],
            "phone": ["Phone"],
            "email": ["Email"],
            "address": ["Street address", "Address"],
            "description": ["Description"]}
ID_HEAD = re.compile(r"^\d+-[\dA-Za-z]+-\d+\s*—\s*(.+)$")
ROW_HEAD = re.compile(r"^Row\s+\d+\s*—\s*(.+)$", re.I)
SEGMENT_ID = re.compile(r"^\d+-[\dA-Za-z]+-\d+$")
# Bold lead-ins that are the report talking about its own method, not a business.
NOT_A_BUSINESS = (
    "standard category for every entry", "corrected rewrite entries", "note", "method",
    "reconciliation", "internal-duplicate check", "end of slice audit", "duplicates",
    "licensed operators moved out", "hemp licence only", "rows ", "category block",
)


def text_of(fragment):
    """Visible text, with links reduced to their href so a URL survives.

    Unescapes twice: this report is double-escaped, so one pass leaves "M&amp;A"
    in a description.
    """
    out = re.sub(r'<a[^>]*href="([^"]+)"[^>]*>.*?</a>', r" \1 ", fragment, flags=re.S | re.I)
    out = re.sub(r"<li[^>]*>", " \n", out, flags=re.I)
    out = re.sub(r"</(p|li|h\d|ul|div)>", " \n", out, flags=re.I)
    out = re.sub(r"<[^>]+>", " ", out)
    out = html.unescape(html.unescape(out))
    return re.sub(r"[ \t]+", " ", out).strip()


def entry_starts(part2):
    """Every position in Part 2 where a business entry begins."""
    found = []
    for m in re.finditer(r"<(h[2-6])[^>]*>(.*?)</\1>", part2, re.S | re.I):
        t = text_of(m.group(2))
        if re.match(r"^\d+\.\s+\S", t) or ID_HEAD.match(t) or ROW_HEAD.match(t):
            found.append((m.start(), t))
    # Layouts C and E: a paragraph that opens in bold. Numbered or not — the
    # Compliance and Consulting block runs 110 entries with no numbers at all.
    for m in re.finditer(r"<p[^>]*>\s*<strong>(.*?)</strong>", part2, re.S | re.I):
        t = text_of(m.group(1))
        if len(t) > 3 and not LABEL_RE.match(t):
            found.append((m.start(), t))
    found.sort()
    # Drop a start that is really a section lead-in rather than a business.
    return [(p, t) for p, t in found if not t.lower().startswith(NOT_A_BUSINESS)]


def clean_name(raw):
    """The business name out of a heading or bold lead-in.

    The name is not always the first segment: the report prefixes some entries
    with a row number, an internal id, or both ("Row 43 — 5-11a-1 — Tact Firm
    — Unverified"), so leading segments that are only a number or an id are
    dropped before the name is taken.
    """
    t = raw.strip()
    # Strip a bracketed flag FIRST: "[UNVERIFIED — KEEP FLAGGED]" contains an em
    # dash, so splitting on dashes before removing it leaves "Name [UNVERIFIED".
    t = re.sub(r"\s*\[[^\]]*\]\s*", " ", t).strip()
    t = re.sub(r"^\d+\.\s*", "", t)                       # "23. Cantein"
    rowm = ROW_HEAD.match(t)
    if rowm:                                              # "Row 1 — Name — Verdict"
        t = rowm.group(1)
    segments = [x.strip() for x in re.split(r"\s+—\s+|\s+–\s+", t) if x.strip()]
    while segments and SEGMENT_ID.match(segments[0]):     # "5-11a-1"
        segments.pop(0)
    t = segments[0] if segments else ""
    t = re.sub(r"\s*—\s*(Confirmed|Corrected|Unverified|National.*)$", "", t, flags=re.I)
    return t.strip(" .,—–")


def fields_of(block):
    """{label: value} for one entry, each value running to the next label."""
    body = text_of(block)
    hits = list(LABEL_RE.finditer(body))
    out = {}
    for i, m in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(body)
        value = body[m.end():end].strip(" .;,—–\n")
        label = m.group(1).title()
        if label not in out or (not out[label] and value):
            out[label] = value
    return out


def first_published(fields, labels):
    for l in labels:
        for key in (l, l.title()):
            v = fields.get(key, "")
            if v and not NOT_PUBLISHED.match(v):
                return v
    return ""


def tidy(field, value):
    """Trim a value to just the fact, dropping the report's parenthetical notes."""
    v = re.sub(r"\s+", " ", value).strip()
    if field == "website":
        urls = re.findall(r"https?://[^\s,;)]+", v)
        return urls[0].rstrip(".") if urls else ""
    if field == "email":
        mails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", v)
        return mails[0].rstrip(".") if mails else ""
    if field == "phone":
        nums = re.findall(r"(?:\+1[\s-]*)?(?:\(\d{3}\)|\d{3})[\s.-]*\d{3}[\s.-]*\d{4}", v)
        return nums[0].strip() if nums else ""
    if field == "address":
        # An address's parenthetical is always the auditor's caveat about it
        # ("(directory listings; opened page did not repeat street address —
        # Verify)"), never part of the address, so the address ends at it. The
        # caveat is not lost: the row carries audit_verdict and needs_verify,
        # which is this project's existing mechanism for an unconfirmed entry.
        # The caveat is appended either in parentheses or after an em dash
        # ("...CA 95472 — same building as...", "Fairfield, CA — street address
        # Not published — Verify"), so the address ends at whichever comes first.
        v = re.split(r"\s+\(|\s+—\s+|\s+–\s+", v)[0]
        if NOT_PUBLISHED.match(v) or re.search(r"not published", v, re.I):
            return ""
        return v.strip(" .;,")
    # description: drop a trailing parenthetical caveat only
    v = re.sub(r"\s*\((?:not re-opened|per |source row|opened|do not|described).*?\)\s*$", "", v,
               flags=re.I)
    return v.strip(" .;,")


def norm(name):
    """A match key. Both sides of the join need the same two reductions.

    The audit table names a business "Allison B. Margolin, PLC (formerly
    Margolin & Lawrence) — Beverly Hills", appending the place after an em
    dash, while Part 2 names the same business without it. And the California
    report is double-escaped, so a name can arrive as "Richter &amp; Hampton".
    """
    s = html.unescape(html.unescape(name or ""))
    s = re.sub(r"\s*\[[^\]]*\]\s*", " ", s)
    s = s.split(" — ")[0].split(" – ")[0]
    # An alias is written " / Other Name" on one side and "(Other Name)" on the
    # other, so both forms are dropped and the primary name is what matches.
    s = s.split(" / ")[0]
    s = s.upper()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = re.sub(r"\b(LLC|LLP|LP|INC|CORP|CORPORATION|CO|COMPANY|PC|PLLC|PA|THE|AND)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true", help="show what was parsed, change nothing")
    args = ap.parse_args()

    doc = REPORT.read_text(encoding="utf-8", errors="replace")
    part2 = doc[doc.index("PART 2 — CORRECTED REWRITE"):]
    starts = entry_starts(part2)
    parsed = {}
    for i, (pos, raw) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(part2)
        fields = fields_of(part2[pos:end])
        if "Website" not in fields and "Phone" not in fields:
            continue                                   # not a business entry
        name = clean_name(raw)
        if not name:
            continue
        rec = {f: tidy(f, first_published(fields, labels)) for f, labels in FILLABLE.items()}
        rec["people"] = first_published(fields, ["People"])
        key = norm(name)
        if key and (key not in parsed or sum(bool(v) for v in rec.values())
                    > sum(bool(v) for v in parsed[key].values())):
            rec["_name"] = name
            parsed[key] = rec
    print(f"Part 2: {len(starts)} entry starts, {len(parsed)} distinct businesses parsed")
    got = Counter()
    for rec in parsed.values():
        for f in list(FILLABLE) + ["people"]:
            if rec.get(f):
                got[f] += 1
    for f in list(FILLABLE) + ["people"]:
        print(f"    {f:12} published for {got[f]:>4} of {len(parsed)}")

    rows = list(csv.DictReader(open(MASTER, newline="", encoding="utf-8")))
    ca = [r for r in rows if r["region"] == "California"]
    matched = filled = Counter(), Counter()
    matched, filled = Counter(), Counter()
    unmatched_rows, used = [], set()
    for r in ca:
        rec = parsed.get(norm(r["business_name"]))
        if not rec:
            unmatched_rows.append(r["business_name"])
            continue
        used.add(norm(r["business_name"]))
        matched["rows"] += 1
        for f in FILLABLE:
            if rec.get(f) and not r[f].strip():
                r[f] = rec[f]
                filled[f] += 1
        if rec.get("people") and not r["key_people_private"].strip():
            r["key_people_private"] = rec["people"]
            filled["key_people_private"] += 1

    print(f"\nmatched {matched['rows']} of {len(ca)} California rows to a Part 2 entry")
    for f, n in filled.most_common():
        print(f"    {f:20} filled on {n} rows")
    leftover = [k for k in parsed if k not in used]
    print(f"  Part 2 entries with no audit-table row: {len(leftover)}")
    for k in leftover[:8]:
        print(f"    {parsed[k]['_name']}")
    print(f"  California rows with no Part 2 entry: {len(unmatched_rows)}")
    for n in unmatched_rows[:8]:
        print(f"    {n}")

    if args.report or args.dry_run:
        print("\n(nothing written)")
        return
    cols = list(rows[0].keys())
    with open(MASTER, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    print(f"\nwrote {MASTER.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
