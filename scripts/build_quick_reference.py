#!/usr/bin/env python3
"""Write data/clean/quick_reference.csv from scripts/quick_reference_data.py, and check it.

One row per state per fact (FIELDS in quick_reference_data.py: possession, home grow,
the state's cannabis tax, the regulator, where it may be used, employment, driving).
The state page's quick-reference boxes and its Laws and Taxes tabs read it.

Checks, each of which refuses to write:
  * all 51 jurisdictions, each with every fact in FIELDS;
  * a confirmed fact has text, and either an official link (a host in
    domains/all-domains.txt) or a note saying why there is none;
  * an unconfirmed fact has NO text (CLAUDE.md: unverified facts stay off the public
    site) and a note saying why it is unconfirmed;
  * every statute or section number in a citation appears in that state's own
    audited report, as a whole token: "41-137-3" does not count as found inside
    "41-137-35", and a bare "§4177" must be there too. This is the guard against a
    citation written from memory;
  * every figure in a published fact's text or note (three or more digits, or a
    decimal: "$1,000", "5.00 ng/mL", "17.38.020") appears, as written, in that same
    report. The guard against a figure typed from memory (added 20 Nov 2026, after a
    hand check of all 357 facts found none astray).

The date of every fact is its report's "Last audited" date, taken from
data/clean/legal_status.csv, which reads it from the report itself.

Usage:
  python3 scripts/build_quick_reference.py [--dry-run]
"""
import argparse, csv, html, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_legal_status import is_official, official_hosts  # noqa: E402
from quick_reference_data import FIELDS, QUICK  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEGAL = ROOT / "data" / "clean" / "legal_status.csv"
OUT = ROOT / "data" / "clean" / "quick_reference.csv"
COLUMNS = ["state", "fact", "text", "cite", "source_url", "confirmed", "note", "report_last_audited"]

# A section-like token: digits, then at least one separator and more digits/letters.
# "17.38.020", "36-2852", "21a-279a", "71-24,105", "§1501" is too short to test alone.
TOKEN = re.compile(r"\b\d+[A-Za-z]{0,2}(?:[-.:,]\d+[A-Za-z]{0,3})+")


def report_text(path):
    t = (ROOT / path).read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"<[^>]+>", " ", t)
    return html.unescape(t)


def tokens(cite):
    """Section-like tokens in a citation, plus bare section or volume numbers of three or
    more digits ("§4177", "271 Ga. 398"), which the token pattern alone would skip."""
    out = [m.group(0) for m in re.finditer(r"(?<![\w.,:-])\d{3,}[A-Za-z]?(?![\w]|[-.:,]\d)", cite)]
    for m in TOKEN.finditer(cite):
        tok = m.group(0).rstrip(".,:-")
        if re.fullmatch(r"\d{1,2}[.:]\d{1,2}", tok):
            continue  # times and small decimals, not sections
        if re.fullmatch(r"\d{4}", tok.split(",")[0]) and "," in tok:
            tok = tok.split(",")[0]
        out.append(tok)
    return out


def present(tok, text):
    pat = r"(?<![0-9A-Za-z])" + re.escape(tok) + r"(?![0-9A-Za-z]|[-.,][0-9])"
    return re.search(pat, text) is not None


FIGURE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def stray_figures(text, report):
    """Figures in `text` that are not in `report`. A section-like token found whole in
    the report is set aside first, so "AS 17.38.020(2)" is not read as the figure 020."""
    rest = TOKEN.sub(lambda m: " " if present(m.group(0).rstrip(".,:-"), report) else m.group(0),
                     text or "")
    out = []
    for m in FIGURE.finditer(rest):
        tok = m.group(0).rstrip(",.")
        if (len(re.sub(r"\D", "", tok)) >= 3 or "." in tok) and not re.search(
                r"(?<![\d.,])" + re.escape(tok) + r"(?![\d]|[.,]\d)", report):
            out.append(tok)
    return out


def build():
    hosts = official_hosts()
    with open(LEGAL, encoding="utf-8") as f:
        legal = {r["state"]: r for r in csv.DictReader(f)}
    problems, rows, texts = [], [], {}
    for code in sorted(set(legal) | set(QUICK)):
        if code not in legal:
            problems.append(f"{code}: not one of the 51 jurisdictions")
            continue
        facts = QUICK.get(code)
        if not facts:
            problems.append(f"{code}: no quick-reference facts")
            continue
        if code not in texts:
            texts[code] = report_text(legal[code]["report"])
        for field in FIELDS:
            f = facts.get(field)
            where = f"{code}.{field}:"
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
                for tok in stray_figures(f"{f['text']} {f['note']}", texts[code]):
                    problems.append(f"{where} the figure {tok!r} is not in the audited report")
            else:
                if f["text"]:
                    problems.append(f"{where} unconfirmed facts must carry no text")
                if not f["note"]:
                    problems.append(f"{where} unconfirmed with no reason")
            for tok in tokens(f["cite"]):
                if not present(tok, texts[code]):
                    problems.append(f"{where} cites {tok!r}, which is not in the audited report")
            rows.append({"state": code, "fact": field, "text": f["text"] or "",
                         "cite": f["cite"], "source_url": f["url"],
                         "confirmed": "Y" if f["confirmed"] else "N", "note": f["note"],
                         "report_last_audited": legal[code]["report_last_audited"]})
    return rows, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    rows, problems = build()
    if problems:
        sys.exit("REFUSING TO WRITE quick_reference.csv:\n  " + "\n  ".join(problems))
    states = {r["state"] for r in rows}
    unconfirmed = [f'{r["state"]}.{r["fact"]}' for r in rows if r["confirmed"] == "N"]
    nolink = [f'{r["state"]}.{r["fact"]}' for r in rows if r["confirmed"] == "Y" and not r["source_url"]]
    print(f"  {len(rows)} facts for {len(states)} jurisdictions")
    print(f"  {len(unconfirmed)} not yet confirmed (kept off the site): {', '.join(unconfirmed)}")
    print(f"  {len(nolink)} confirmed with no official link captured: {', '.join(nolink)}")
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
