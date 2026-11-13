#!/usr/bin/env python3
"""Download New Jersey's per-business permit PDFs and record their provenance.

New Jersey's CRC publishes no licence number in any list. Its permitted-
businesses page gives organisation, business types, locations and an expiration
YEAR; the licence numbers live one hop deeper, in a permit PDF linked from each
table row. Those PDFs are the only published source for them.

Every URL here is READ OUT OF the saved copy of that page (the `urls_from` file
in the source declaration) and must match the declared `url_must_match` pattern.
Nothing is constructed from a business name, so a row that carries no link stays
unfetched and is recorded as a gap rather than guessed at.

Alongside the PDFs this writes _link_index.csv: the table-row context for each
link (section, organisation, business types, locations, expiration year), which
is what the parse step reconciles the extracted permits against.

Usage:
  python3 scripts/fetch_nj_permits.py --index-only    # resolve links, no fetch
  python3 scripts/fetch_nj_permits.py --limit 5       # fetch the first 5
  python3 scripts/fetch_nj_permits.py                 # fetch all
"""
import argparse, csv, hashlib, html, json, pathlib, re, sys, time
import urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fetch_raw as fr  # shared UA, verifying SSL context, manifest writer

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE_ID = "nj-crc-permit-pdfs"
LINK_FIELDS = ["section", "organisation", "business_types", "locations", "expiration_year",
               "href", "filename", "table_index", "row_index"]

# A permit PDF must look like one. Checked on content, not on HTTP status:
# nj.gov answers a missing document with a 200 and an HTML error page.
MUST_CONTAIN = ["CANNABIS REGULATORY COMMISSION", "NUMBER:"]


def declaration():
    for src in json.loads((ROOT / "scripts" / "sources.json").read_text()):
        if src["id"] == SOURCE_ID:
            return src
    sys.exit(f"{SOURCE_ID} is not declared in scripts/sources.json")


def strip_tags(fragment):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def section_for(offset, sections):
    """The section heading this table sits under, by document position."""
    name = ""
    for at, title in sections:
        if at < offset:
            name = title
    return name


def resolve_links(src):
    """Read every permit link out of the saved page, with its row context."""
    page = ROOT / src["urls_from"]
    if not page.exists():
        sys.exit(f"saved page missing: {src['urls_from']} — fetch_raw.py first")
    doc = page.read_text(encoding="utf-8", errors="replace")
    must = re.compile(src["url_must_match"])

    sections = [(m.start(), strip_tags(m.group(1)))
                for m in re.finditer(r'aria-controls="\d+"[^>]*>(.*?)<i class', doc, re.S)]
    sections = [(at, t) for at, t in sections if t]

    links, skipped = [], []
    for ti, tm in enumerate(re.finditer(r"<table.*?</table>", doc, re.S | re.I)):
        section = section_for(tm.start(), sections)
        for ri, row in enumerate(re.finditer(r"<tr.*?</tr>", tm.group(0), re.S | re.I)):
            cells = [strip_tags(c) for c in
                     re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row.group(0), re.S | re.I)]
            hrefs = [html.unescape(h) for h in
                     re.findall(r'href="([^"]+\.pdf)"', row.group(0), re.I)]
            if not hrefs:
                continue
            for href in hrefs:
                absolute = href if href.startswith("http") else "https://www.nj.gov" + href
                # Space-vs-%20 is inconsistent across the page's own links; the
                # pattern allows either, and the request is sent percent-encoded.
                if not must.match(absolute):
                    skipped.append((absolute, "does not match the declared pattern"))
                    continue
                links.append({
                    "section": section,
                    "organisation": cells[0] if cells else "",
                    "business_types": cells[1] if len(cells) > 1 else "",
                    "locations": cells[2] if len(cells) > 2 else "",
                    "expiration_year": cells[3] if len(cells) > 3 else "",
                    "href": absolute,
                    "filename": local_name(absolute),
                    "table_index": str(ti),
                    "row_index": str(ri),
                })
    return links, skipped


def local_name(url):
    """A stable, filesystem-safe name that keeps the regulator's own filename."""
    base = urllib.parse.unquote(url.rsplit("/", 1)[-1])
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("_")
    return base


def encoded(url):
    """Percent-encode the path exactly once.

    The page's own links are inconsistent: the same directory appears as
    "Permits and Renewals" on some rows and "Permits%20and Renewals" on others.
    Encoding without unquoting first turns an existing %20 into %2520 and the
    server answers 404, so each segment is unquoted before it is quoted.
    """
    head, _, tail = url.rpartition("/cannabis/documents/")
    path, _, name = tail.rpartition("/")
    quote = lambda part: urllib.parse.quote(urllib.parse.unquote(part))
    return f"{head}/cannabis/documents/{quote(path)}/{quote(name)}"


def check(body):
    """None if this is a permit PDF, else the reason it is not."""
    if not body.startswith(b"%PDF"):
        return "not a PDF (no %PDF header)"
    if len(body) < 2000:
        return f"only {len(body)} bytes"
    try:
        from pypdf import PdfReader
        import io
        reader = PdfReader(io.BytesIO(body))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception as exc:
        return f"PDF will not open: {type(exc).__name__}: {exc}"
    if not text.strip():
        return "no text layer — would need OCR, not parsing"
    missing = [m for m in MUST_CONTAIN if m not in text]
    if missing:
        return f"text lacks {missing} — not a CRC permit"
    return None


def fetch_one(link, dest_dir, src):
    url = encoded(link["href"])
    dest = dest_dir / link["filename"]
    row = {"fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "id": f'{SOURCE_ID}:{link["filename"]}', "state": src["state"],
           "part5_ref": src.get("part5_ref", ""), "format": "pdf",
           "filename": f'{src["dest_subdir"]}/{link["filename"]}', "bytes": "",
           "sha256": "", "status": "", "url_resolved": url,
           "note": f'{link["section"]} | {link["organisation"]}'}
    if dest.exists():
        body = dest.read_bytes()
        row["bytes"], row["sha256"] = str(len(body)), hashlib.sha256(body).hexdigest()
        row["status"] = "skipped: already on disk"
        return row, "skip"

    req = urllib.request.Request(url, headers={"User-Agent": fr.UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=120, context=fr.CTX) as resp:
            body = resp.read(40 * 1024 * 1024)
    except urllib.error.HTTPError as exc:
        row["status"] = f"failed: HTTP {exc.code}"
        return row, "fail"
    except Exception as exc:
        row["status"] = f"failed: {type(exc).__name__}: {exc}"
        return row, "fail"

    row["bytes"], row["sha256"] = str(len(body)), hashlib.sha256(body).hexdigest()
    problem = check(body)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body)
    row["status"] = f"suspect: {problem}" if problem else "ok"
    return row, ("suspect" if problem else "ok")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index-only", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--delay", type=float, default=0.6)
    args = ap.parse_args()

    src = declaration()
    dest_dir = ROOT / "data" / "raw" / src["state"] / src["dest_subdir"]
    links, skipped = resolve_links(src)

    by_section = {}
    for l in links:
        by_section[l["section"]] = by_section.get(l["section"], 0) + 1
    print(f"resolved {len(links)} permit links from {src['urls_from']}")
    for name, n in by_section.items():
        print(f"  {n:4}  {name}")
    for url, why in skipped:
        print(f"  skipped (not fetched): {why}: {url}")
    dupes = len(links) - len({l["href"] for l in links})
    if dupes:
        print(f"  note: {dupes} duplicate hrefs across rows")

    dest_dir.mkdir(parents=True, exist_ok=True)
    index = dest_dir / "_link_index.csv"
    with open(index, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LINK_FIELDS)
        w.writeheader()
        for l in links:
            w.writerow(l)
    print(f"wrote {index.relative_to(ROOT)}")
    if args.index_only:
        return

    todo = links[: args.limit] if args.limit else links
    rows, tally = [], {"ok": 0, "suspect": 0, "fail": 0, "skip": 0}
    for i, link in enumerate(todo, 1):
        row, outcome = fetch_one(link, dest_dir, src)
        rows.append(row)
        tally[outcome] += 1
        if outcome != "ok":
            print(f"  {outcome:8} {link['filename']}  {row['status']}")
        if i % 50 == 0 or i == len(todo):
            print(f"  ... {i}/{len(todo)}  ok={tally['ok']} suspect={tally['suspect']} "
                  f"fail={tally['fail']} skip={tally['skip']}")
        if outcome not in ("skip",):
            time.sleep(args.delay)  # be a polite guest on state servers

    fr.write_manifest(rows)
    print(f"\n{tally['ok']} ok, {tally['suspect']} suspect, {tally['fail']} failed, "
          f"{tally['skip']} already on disk — logged to data/raw/manifest.csv")


if __name__ == "__main__":
    main()
