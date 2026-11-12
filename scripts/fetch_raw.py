#!/usr/bin/env python3
"""Download official licence files into data/raw/<state>/ and record provenance.

Every source is declared in scripts/sources.json, which carries the Part 5
reference it came from and the limitation the audit recorded for it. Nothing is
fetched that is not declared there: a URL that was never resolved from an
official page stays out, and is recorded as UNAVAILABLE instead of guessed.

Each attempt appends a row to data/raw/manifest.csv, successes and failures
alike, so a source that could not be fetched leaves a record of why rather than
silently going missing.

Usage:
  python3 scripts/fetch_raw.py --list
  python3 scripts/fetch_raw.py --state new-york [--dry-run]
  python3 scripts/fetch_raw.py --id ny-ocm-licences
"""
import argparse, csv, hashlib, io, json, os, pathlib, re, ssl, sys, time
import urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

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
    for cafile in ("/etc/ssl/cert.pem", "/private/etc/ssl/cert.pem"):
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


def fetch(src, dry_run=False):
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
    if dest.exists():
        row["status"] = "skipped: already on disk"
        row["bytes"] = str(dest.stat().st_size)
        print(f"  = {src['id']:28} already on disk, left untouched")
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
    row["bytes"] = str(len(body))
    row["sha256"] = hashlib.sha256(body).hexdigest()
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

    state_dir.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body)
    if problem:
        row["status"] = f"suspect: {problem}"
        print(f"  ! {src['id']:28} saved {len(body):>10,} B  SUSPECT: {problem}")
    else:
        row["status"] = "ok"
        print(f"  + {src['id']:28} saved {len(body):>10,} B  ({ctype.split(';')[0]})")
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
        rows.append(fetch(s, args.dry_run))
        if not args.dry_run:
            time.sleep(1.0)  # be a polite guest on state servers
    if not args.dry_run:
        write_manifest(rows)
        ok = sum(1 for r in rows if r["status"] == "ok")
        print(f"\n{ok}/{len(rows)} ok — manifest: {MANIFEST.relative_to(ROOT)}")
        for r in rows:
            if r["status"] != "ok":
                print(f"  {r['status']:46} {r['id']}")


if __name__ == "__main__":
    main()
