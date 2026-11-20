#!/usr/bin/env python3
"""Write data/clean/market.csv from scripts/market_data.py, and check it.

Two facts per jurisdiction for the state page's Market tab: the size of the legal
market (in whatever official measure the state publishes) and registered patients.

Checks, each of which refuses to write:
  * all 51 jurisdictions, each with both facts;
  * a confirmed fact has text and either an official link (a host in
    domains/all-domains.txt) or a note saying why there is none;
  * an unconfirmed fact has NO text and a reason (CLAUDE.md: unverified figures stay
    off the public site);
  * every number in a fact's text (three or more digits, or a decimal) appears, as
    written, in that state's own audited report. This is the guard against a figure
    typed from memory or mistyped: "$1,315,678,364" must be in the Colorado report.

Usage:
  python3 scripts/build_market.py [--dry-run]
"""
import argparse, csv, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_legal_status import is_official, official_hosts  # noqa: E402
from build_quick_reference import report_text  # noqa: E402
from market_data import FIELDS, MARKET  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEGAL = ROOT / "data" / "clean" / "legal_status.csv"
OUT = ROOT / "data" / "clean" / "market.csv"
COLUMNS = ["state", "fact", "text", "cite", "source_url", "confirmed", "note", "report_last_audited"]
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def numbers(text):
    out = []
    for m in NUMBER.finditer(text or ""):
        tok = m.group(0).rstrip(",.")
        digits = re.sub(r"\D", "", tok)
        if len(digits) >= 3 or "." in tok:
            out.append(tok)
    return out


def present(tok, text):
    return re.search(r"(?<![\d.,])" + re.escape(tok) + r"(?![\d]|[.,]\d)", text) is not None


def build():
    hosts = official_hosts()
    with open(LEGAL, encoding="utf-8") as f:
        legal = {r["state"]: r for r in csv.DictReader(f)}
    problems, rows = [], []
    for code in sorted(set(legal) | set(MARKET)):
        if code not in legal:
            problems.append(f"{code}: not one of the 51 jurisdictions")
            continue
        facts = MARKET.get(code)
        if not facts:
            problems.append(f"{code}: no market facts")
            continue
        text_of_report = report_text(legal[code]["report"])
        for field in FIELDS:
            f, where = facts.get(field), f"{code}.{field}:"
            if not f:
                problems.append(f"{where} missing")
                continue
            if f["confirmed"]:
                if not (f["text"] or "").strip():
                    problems.append(f"{where} confirmed but has no text")
                if f["url"] and not is_official(f["url"], hosts):
                    problems.append(f"{where} link is not on an official host: {f['url']}")
                if not f["url"] and not f["note"]:
                    problems.append(f"{where} no link and no note saying why")
                for tok in numbers(f["text"]):
                    if not present(tok, text_of_report):
                        problems.append(f"{where} {tok!r} is not in the audited report")
            else:
                if f["text"]:
                    problems.append(f"{where} unconfirmed facts must carry no text")
                if not f["note"]:
                    problems.append(f"{where} unconfirmed with no reason")
            rows.append({"state": code, "fact": field, "text": f["text"] or "", "cite": f["cite"],
                         "source_url": f["url"], "confirmed": "Y" if f["confirmed"] else "N",
                         "note": f["note"], "report_last_audited": legal[code]["report_last_audited"]})
    return rows, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    rows, problems = build()
    if problems:
        sys.exit("REFUSING TO WRITE market.csv:\n  " + "\n  ".join(problems))
    for field in FIELDS:
        sub = [r for r in rows if r["fact"] == field]
        print(f"  {field:9} {sum(r['confirmed'] == 'Y' for r in sub):>2} published, "
              f"{sum(r['confirmed'] == 'N' for r in sub):>2} held back as not yet confirmed")
    if args.dry_run:
        print("(nothing written)")
        return
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
