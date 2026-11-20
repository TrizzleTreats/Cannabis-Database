#!/usr/bin/env python3
"""Write data/clean/legal_status.csv from scripts/legal_status_data.py, and check it.

The home-page map colours each jurisdiction by this table, so the colour is a statement
about the law. It must come from the audited reports and an official link, never from
whether this project holds licence data for a state.

Checks, each of which refuses to write:
  * exactly the 51 jurisdictions, once each, with a status from the fixed four;
  * every link is on an official host from domains/all-domains.txt (CLAUDE.md: primary
    sources only), and every row with no link says why (source_kind = none);
  * the audited report the row restates exists, and its "Last audited" date is read from
    the report itself rather than typed in, so the date cannot drift from the source.

Usage:
  python3 scripts/build_legal_status.py [--dry-run]
"""
import argparse, csv, pathlib, re, sys
from urllib.parse import urlparse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from legal_status_data import ROWS, STATUSES  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "clean" / "legal_status.csv"
REPORTS = ROOT / "reports" / "regions"
COLUMNS = ["state", "state_name", "legal_status", "citation", "source_url", "source_kind",
           "note", "report", "report_last_audited"]
KINDS = {"statute", "regulator", "court", "none"}
MONTHS = {m: i for i, m in enumerate(
    "January February March April May June July August September October November December"
    .split(), 1)}
MONTHS.update({m[:3]: i for m, i in list(MONTHS.items())})


def official_hosts():
    with open(ROOT / "domains" / "all-domains.txt", encoding="utf-8") as f:
        return {line.strip().lower() for line in f if line.strip()}


def is_official(url, hosts):
    host = (urlparse(url).hostname or "").lower()
    return host in hosts or any(host.endswith("." + h) for h in hosts)


def audited_date(report):
    text = report.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"<[^>]+>", " ", text).replace("&nbsp;", " ")
    m = re.search(r"(?:Last audited|Audited):?\s*(\d{1,2})\s+([A-Z][a-z]+)\s+(20\d\d)", text)
    if not m or m.group(2) not in MONTHS:
        return None
    return f"{m.group(3)}-{MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}"


def build():
    hosts = official_hosts()
    problems, out, seen = [], [], set()
    for code, name, slug, status, citation, url, kind, note in ROWS:
        where = f"{code}:"
        if code in seen:
            problems.append(f"{where} listed twice")
        seen.add(code)
        if status not in STATUSES:
            problems.append(f"{where} unknown status {status!r}")
        if kind not in KINDS:
            problems.append(f"{where} unknown source_kind {kind!r}")
        if not citation.strip():
            problems.append(f"{where} no citation")
        if url and not is_official(url, hosts):
            problems.append(f"{where} link is not on an official host: {url}")
        if (kind == "none") != (not url):
            problems.append(f"{where} source_kind 'none' if and only if there is no link")
        if kind == "none" and not note:
            problems.append(f"{where} a row with no link must say why in its note")
        reports = sorted((REPORTS / slug).glob("*-audited.html"))
        if len(reports) != 1:
            problems.append(f"{where} expected one audited report in {slug}, found {len(reports)}")
            continue
        date = audited_date(reports[0])
        if not date:
            problems.append(f"{where} no 'Last audited' date in {reports[0].name}")
        out.append({
            "state": code, "state_name": name, "legal_status": status, "citation": citation,
            "source_url": url, "source_kind": kind, "note": note,
            "report": str(reports[0].relative_to(ROOT)), "report_last_audited": date or "",
        })
    if len(seen) != 51:
        problems.append(f"expected 51 jurisdictions, have {len(seen)}")
    return out, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    rows, problems = build()
    if problems:
        sys.exit("REFUSING TO WRITE legal_status.csv:\n  " + "\n  ".join(problems))
    rows.sort(key=lambda r: r["state"])
    counts = {s: sum(r["legal_status"] == s for r in rows) for s in STATUSES}
    for s, n in counts.items():
        print(f"  {n:>2}  {s}")
    missing = [r["state"] for r in rows if r["source_kind"] == "none"]
    print(f"  official link captured for {51 - len(missing)} of 51"
          + (f" (none yet: {', '.join(missing)})" if missing else ""))
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
