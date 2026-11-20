#!/usr/bin/env python3
"""Download official licence files into data/raw/<state>/ and record provenance.

Every source is declared in scripts/sources.json, which carries the Part 5
reference it came from and the limitation the audit recorded for it. Nothing is
fetched that is not declared there: a URL that was never resolved from an
official page stays out, and is recorded as UNAVAILABLE instead of guessed.

Each attempt appends a row to data/raw/manifest.csv, successes and failures
alike, so a source that could not be fetched leaves a record of why rather than
silently going missing.

--refresh is the daily mode. Without it a file already on disk is left alone, which
is right for a first capture and wrong for keeping the data current. With it, every
source is downloaded again and:
  * the same bytes as the current file  -> logged "ok: unchanged", nothing written;
    the read date still moves, because the regulator was checked that day;
  * new bytes that pass the checks      -> saved as <declared name>__fetched-<date>,
    logged "ok", and the file it supersedes is removed from the working tree (git
    history keeps it);
  * a suspect or failed download        -> logged, NOT written, and the last good
    file stays current, so a bad day never replaces good data.
scripts/raw_files.py is how the builders find the current file and its read date.

A source may declare "drop_columns" (regular expressions matched against CSV
headers). Those columns are removed before the file is saved or hashed: CLAUDE.md
forbids keeping Massachusetts' EIN/TIN column at all.

Usage:
  python3 scripts/fetch_raw.py --list
  python3 scripts/fetch_raw.py --state new-york [--dry-run]
  python3 scripts/fetch_raw.py --id ny-ocm-licences
  python3 scripts/fetch_raw.py --refresh [--state ...]     # daily: re-download everything
"""
import argparse, csv, hashlib, io, json, os, pathlib, re, ssl, sys, time
import urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import raw_files  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES = ROOT / "scripts" / "sources.json"
MANIFEST = ROOT / "data" / "raw" / "manifest.csv"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
FIELDS = ["fetched_at", "id", "state", "part5_ref", "format", "filename", "bytes",
          "sha256", "status", "url_resolved", "note"]

# Markers that mean "the fetch succeeded but the content is not the data".
# A bot check or an unrendered dashboard returns HTTP 200 and looks like success.
# Matched against VISIBLE text only: scanning raw markup gives false positives,
# because a legitimate page may load recaptcha/api.js for an unrelated form.
BOT_MARKERS = ["just a moment", "enable javascript", "captcha", "are you a human",
               "access denied", "request unsuccessful", "loading data",
               "verifying you are human", "checking your browser"]


def visible_text(html_text):
    """Drop scripts, styles and tags so marker checks see what a reader sees."""
    out = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html_text, flags=re.S | re.I)
    out = re.sub(r"<[^>]+>", " ", out)
    return re.sub(r"\s+", " ", out).strip()


def ssl_context():
    """A verifying context, or nothing. These are government sources whose
    identity is the whole point of the primary-sources-only rule, so an
    unverified fallback is never offered — this python build just looks for its
    CA bundle somewhere macOS does not keep one."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    # macOS keeps its bundle at the first two; Debian/Ubuntu (a CI runner) at the third.
    for cafile in ("/etc/ssl/cert.pem", "/private/etc/ssl/cert.pem",
                   "/etc/ssl/certs/ca-certificates.crt"):
        if os.path.exists(cafile):
            return ssl.create_default_context(cafile=cafile)
    sys.exit("no CA bundle found - refusing to fetch without certificate verification")


CTX = ssl_context()


def build_url(src):
    url = src["url"]
    if src.get("params"):
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(src["params"])
    return url


def sniff(fmt, body, text):
    """Return None if the body looks like the declared format, else a reason."""
    if fmt == "pdf":
        if not body.startswith(b"%PDF"):
            return "not a PDF (no %PDF header)"
    elif fmt == "csv":
        if body.lstrip()[:1] in (b"<",):
            return "looks like HTML, not CSV"
        try:
            row = next(csv.reader(io.StringIO(text[:200000])))
        except Exception as exc:
            return f"CSV header unreadable: {exc}"
        if len(row) < 2:
            return "CSV has fewer than 2 columns"
    elif fmt == "json":
        try:
            json.loads(text)
        except Exception as exc:
            return f"invalid JSON: {exc}"
    elif fmt in ("html", "xlsx", "geojson"):
        if fmt == "xlsx" and not body.startswith(b"PK"):
            return "not an xlsx (no zip header)"
    shown = visible_text(text) if fmt in ("html", "geojson", "json") else text
    low = shown[:20000].lower()
    for mark in BOT_MARKERS:
        if mark in low:
            return f"content looks like a bot check or unrendered page ({mark!r})"
    # A real page has readable text. A block page or an unrendered dashboard
    # usually has almost none, however much markup it ships.
    if fmt == "html" and len(shown) < 1500:
        return f"only {len(shown)} chars of visible text - page may not have rendered"
    return None


def fetch_paged_json(src):
    """Walk a paged JSON API and concatenate its records into one CSV.

    Some regulators publish no file at all — their public licence search is a
    single-page app talking to an API. That API is the official source, but it
    serves a page at a time, so the pages are stitched here and the stitched
    row count is checked against the API's own totalCount.
    """
    cfg = src["paged"]
    rows, reported = [], 0
    for value in cfg.get("iterate", [None]):
        page = 1
        while True:
            params = dict(src.get("params") or {})
            if value is not None:
                params[cfg["iterate_param"]] = value
            params[cfg["page_param"]] = page
            params[cfg["size_param"]] = cfg.get("page_size", 1000)
            url = src["url"] + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json",
                                                       "Referer": cfg.get("referer", "")})
            with urllib.request.urlopen(req, timeout=src.get("timeout", 120), context=CTX) as r:
                payload = json.loads(r.read().decode("utf-8", "replace"))
            batch = payload
            for key in cfg.get("data_path", "data").split("."):
                batch = batch[key] if key else batch
            if page == 1:
                meta = payload
                for key in cfg.get("total_path", "metadata.totalCount").split("."):
                    meta = meta[key]
                reported += int(meta)
            rows.extend(batch)
            if not batch or len(rows) >= reported or page >= cfg.get("max_pages", 500):
                break
            page += 1
            time.sleep(cfg.get("delay", 0.4))
    if not rows:
        return b"", "no rows returned"
    fields, seen = [], set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k); fields.append(k)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields)
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fields})
    problem = ""
    if reported and len(rows) != reported:
        problem = f"stitched {len(rows)} rows but the API reported {reported}"
    return buf.getvalue().encode("utf-8"), problem


def drop_columns(src, body):
    """Remove declared columns from a CSV before it is saved or hashed."""
    pats = [re.compile(p, re.I) for p in src.get("drop_columns", [])]
    if not pats or src["format"] != "csv":
        return body
    rows = list(csv.reader(io.StringIO(body.decode("utf-8-sig", errors="replace"))))
    if not rows:
        return body
    keep = [i for i, h in enumerate(rows[0]) if not any(p.search(h) for p in pats)]
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    for r in rows:
        w.writerow([r[i] for i in keep if i < len(r)])
    return out.getvalue().encode("utf-8")


def dated_name(filename, day):
    stem, ext = os.path.splitext(filename)
    return f"{stem}__fetched-{day}{ext}"


def store(src, row, body, problem, refresh, state_dir, dest):
    """Save a download (or decide not to) and fill in the manifest row. Returns the
    one-line console note."""
    body = drop_columns(src, body)
    row["bytes"] = str(len(body))
    row["sha256"] = hashlib.sha256(body).hexdigest()
    if not refresh:
        state_dir.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(body)
        row["status"] = f"suspect: {problem}" if problem else "ok"
        return "saved"
    if problem:
        row["status"], row["filename"] = f"suspect: {problem}", ""
        return "NOT saved; the last good file stays current"
    current, _ = raw_files.current_by_id(src["id"])
    # A file saved under the declared name before the fetcher logged it (Massachusetts'
    # came with the initial commit) is the current file until something supersedes it.
    current = current or (dest if dest.exists() else None)
    if current and hashlib.sha256(current.read_bytes()).hexdigest() == row["sha256"]:
        row["status"], row["filename"] = "ok: unchanged", current.name
        return f"unchanged ({current.name})"
    day = row["fetched_at"][:10]
    name = src["filename"] if not current else dated_name(src["filename"], day)
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / name).write_bytes(body)
    row["status"], row["filename"] = "ok", name
    if current and current.name != name:
        current.unlink()
        row["note"] = "; ".join(x for x in (row["note"], f"supersedes {current.name}, "
                                            "removed from the working tree (kept in git history)") if x)
    return f"saved as {name}"


def fetch(src, dry_run=False, refresh=False):
    url = build_url(src)
    state_dir = ROOT / "data" / "raw" / src["state"]
    dest = state_dir / src["filename"]
    row = {"fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "id": src["id"], "state": src["state"], "part5_ref": src.get("part5_ref", ""),
           "format": src["format"], "filename": src["filename"], "bytes": "",
           "sha256": "", "status": "", "url_resolved": url, "note": src.get("note", "")}
    if dry_run:
        row["status"] = "dry-run"
        print(f"  [dry-run] {src['id']:28} -> {dest.relative_to(ROOT)}\n             {url}")
        return row
    if dest.exists() and not refresh:
        row["status"] = "skipped: already on disk"
        row["bytes"] = str(dest.stat().st_size)
        print(f"  = {src['id']:28} already on disk, left untouched")
        return row

    if src.get("paged"):
        try:
            body, paged_problem = fetch_paged_json(src)
        except Exception as exc:
            row["status"] = f"failed: {type(exc).__name__}: {exc}"
            print(f"  x {src['id']:28} {type(exc).__name__}: {exc}")
            return row
        how = store(src, row, body, paged_problem, refresh, state_dir, dest)
        n = max(0, len(body.decode("utf-8", "replace").splitlines()) - 1)
        mark = "!" if paged_problem else "+"
        print(f"  {mark} {src['id']:28} {how}  {len(body):>10,} B  {n} rows"
              + (f"  SUSPECT: {paged_problem}" if paged_problem else ""))
        return row

    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=src.get("timeout", 180), context=CTX) as resp:
            body = resp.read(src.get("max_bytes", 80 * 1024 * 1024))
            ctype = resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        row["status"] = f"failed: HTTP {exc.code}"
        print(f"  x {src['id']:28} HTTP {exc.code} — recorded, not guessed around")
        return row
    except Exception as exc:
        row["status"] = f"failed: {type(exc).__name__}: {exc}"
        print(f"  x {src['id']:28} {type(exc).__name__}: {exc}")
        return row

    text = body.decode("utf-8", errors="replace")
    problem = sniff(src["format"], body, text)
    if len(body) < src.get("min_bytes", 200):
        problem = problem or f"only {len(body)} bytes"
    # An API that returns exactly its row cap has almost certainly truncated the
    # result, and a truncated CSV parses perfectly - it just quietly lacks rows.
    cap = (src.get("params") or {}).get("$limit")
    if cap and src["format"] == "csv" and not problem:
        n = max(0, sum(1 for _ in csv.reader(io.StringIO(text))) - 1)
        if n >= int(cap):
            problem = f"returned {n} rows, exactly the $limit of {cap} - result is truncated"

    how = store(src, row, body, problem, refresh, state_dir, dest)
    if problem:
        print(f"  ! {src['id']:28} {how}  {len(body):>10,} B  SUSPECT: {problem}")
    else:
        print(f"  + {src['id']:28} {how}  {len(body):>10,} B  ({ctype.split(';')[0]})")
    return row


def write_manifest(rows):
    existing, header_needed = [], not MANIFEST.exists()
    if MANIFEST.exists():
        with open(MANIFEST, newline="", encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in existing + rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state"), ap.add_argument("--id")
    ap.add_argument("--list", action="store_true"), ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--refresh", action="store_true",
                    help="download every source again (the daily mode; see the module notes)")
    args = ap.parse_args()

    srcs = json.loads(SOURCES.read_text())
    if args.state:
        srcs = [s for s in srcs if s["state"] == args.state]
    if args.id:
        srcs = [s for s in srcs if s["id"] == args.id]
    if not srcs:
        sys.exit("no sources matched")

    if args.list:
        for s in srcs:
            print(f"{s['state']:22} {s['id']:28} {s['format']:8} {s.get('part5_ref','')}")
            print(f"{'':22} {build_url(s)}")
        return

    rows = []
    for s in srcs:
        rows.append(fetch(s, args.dry_run, args.refresh))
        if not args.dry_run:
            time.sleep(1.0)  # be a polite guest on state servers
    if not args.dry_run:
        write_manifest(rows)
        ok = sum(1 for r in rows if r["status"] in raw_files.GOOD)
        print(f"\n{ok}/{len(rows)} ok — manifest: {MANIFEST.relative_to(ROOT)}")
        for r in rows:
            if r["status"] not in raw_files.GOOD:
                print(f"  {r['status']:46} {r['id']}")


if __name__ == "__main__":
    main()
