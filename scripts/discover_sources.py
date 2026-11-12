#!/usr/bin/env python3
"""Find the downloadable licence data behind each state's regulator pages.

The audited reports mostly cite landing pages, not files. In the Mid-Atlantic the
real data was consistently one click deeper — Maryland's dashboard XLSX and
Pennsylvania's PASDA spreadsheet were both found this way, and both were
recorded in Part 5 as UNAVAILABLE or VERIFY. This walks every candidate
licensee page in the remaining reports and records what it actually links to.

It discovers; it does not decide. Output is a candidate list for
scripts/sources.json, so a URL still reaches data/raw/ only once declared.

Usage:
  python3 scripts/discover_sources.py [--region 5-great-lakes] [--limit N]
"""
import argparse, collections, csv, html, json, os, pathlib, re, ssl, sys, time
import urllib.error, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "discovered_sources.csv"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")

WANT = re.compile(r'(?i)licen[cs]ee|licen[cs]e\s*(list|search|lookup|report|data)|'
                  r'list\s*of\s*(licen|dispensar|permit|cultivat|establish)|'
                  r'dispensar(y|ies)\s*(list|locat|search)|permit\s*(list|holder)|registry|'
                  r'registrant|approved\s*(facilit|dispensar|center|centre)|'
                  r'business(es)?\s*(list|search)|facility\s*list|current\s*licen|active\s*licen')
SKIP = re.compile(r'(?i)justia|lawserver|findlaw|legiscan|wikipedia|facebook|twitter|linkedin|'
                  r'youtube|instagram|mailto:|\.(jpg|jpeg|png|gif|svg|ico|css|js)(\?|$)')


def ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    for ca in ("/etc/ssl/cert.pem", "/private/etc/ssl/cert.pem"):
        if os.path.exists(ca):
            return ssl.create_default_context(cafile=ca)
    sys.exit("no CA bundle found - refusing to fetch without certificate verification")


CTX = ssl_context()


def classify(u):
    ul = u.lower()
    if re.search(r"/resource/[a-z0-9]{4}-[a-z0-9]{4}|/api/views/[a-z0-9]{4}-[a-z0-9]{4}|"
                 r"/d/[a-z0-9]{4}-[a-z0-9]{4}|/api/v\d/views/", ul):
        return "socrata"
    if re.search(r"(feature|map)server|/arcgis/rest|arcgis\.com/home/item|\.geojson(\?|$)", ul):
        return "arcgis"
    if re.search(r"\.csv(\?|$)", ul):
        return "csv"
    if re.search(r"\.xlsx?(\?|$)", ul):
        return "xlsx"
    if re.search(r"\.zip(\?|$)", ul):
        return "zip"
    if re.search(r"\.pdf(\?|$)", ul):
        return "pdf"
    if re.search(r"powerbi|public\.tableau|lookerstudio|datastudio", ul):
        return "bi-dashboard"
    if re.search(r"opendata\.|/dataset/|data\.[a-z]{2}\.gov|socrata", ul):
        return "open-data-portal"
    return None


def candidates():
    """Candidate licensee pages per state, taken from the audited reports."""
    out = collections.OrderedDict()
    for f in sorted(ROOT.glob("reports/regions/*/*/*.html")):
        region, state = f.parts[-3], f.parts[-2]
        if region in ("1-new-england", "2-mid-atlantic"):
            continue
        t = f.read_text(errors="replace")
        seen = collections.OrderedDict()
        for m in re.finditer(r'<a\b[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', t, re.S | re.I):
            u = html.unescape(m.group(1)).rstrip(".,;")
            txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m.group(2)))).strip()
            if SKIP.search(u):
                continue
            pre = re.sub(r"<[^>]+>", " ", t[max(0, m.start() - 220):m.start()])
            if WANT.search(txt) or WANT.search(u) or WANT.search(pre):
                seen.setdefault(u, txt[:90])
        out[f"{region}/{state}"] = seen
    return out


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read(6 * 1024 * 1024), r.headers.get("Content-Type", ""), r.geturl()


def data_links(page_url, body, ctype):
    """Links and embedded references on this page that look like data."""
    found = collections.OrderedDict()
    kind = classify(page_url)
    if kind and kind != "open-data-portal":
        found[page_url] = (kind, "(the page itself is a data file)")
        return found
    if "html" not in ctype.lower() and not body[:200].lstrip().startswith(b"<"):
        return found
    text = body.decode("utf-8", "replace")
    for m in re.finditer(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', text, re.S | re.I):
        u = urllib.parse.urljoin(page_url, html.unescape(m.group(1))).rstrip(".,;")
        if SKIP.search(u):
            continue
        k = classify(u)
        if k:
            txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m.group(2)))).strip()
            found.setdefault(u, (k, txt[:90]))
    # Endpoints referenced from scripts rather than anchors (ArcGIS apps, Socrata widgets)
    for m in re.finditer(r'https?://[^\s"\'<>()]+', text):
        u = html.unescape(m.group(0)).rstrip(".,;\\")
        if SKIP.search(u):
            continue
        k = classify(u)
        if k in ("socrata", "arcgis", "csv", "xlsx", "bi-dashboard"):
            found.setdefault(u, (k, "(referenced in page script)"))
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region"), ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    cands = candidates()
    if args.region:
        cands = {k: v for k, v in cands.items() if k.startswith(args.region)}
    rows, n, failed = [], 0, collections.Counter()
    total = sum(len(v) for v in cands.values())
    print(f"walking {total} candidate pages across {len(cands)} states", flush=True)

    for key, pages in cands.items():
        region, state = key.split("/")
        for page, anchor in pages.items():
            if args.limit and n >= args.limit:
                break
            n += 1
            try:
                body, ctype, final = fetch(page)
            except urllib.error.HTTPError as e:
                failed[f"HTTP {e.code}"] += 1
                rows.append(dict(state=state, region=region, page_url=page, page_anchor=anchor,
                                 data_url="", kind="", link_text="", status=f"failed: HTTP {e.code}"))
                continue
            except Exception as e:
                failed[type(e).__name__] += 1
                rows.append(dict(state=state, region=region, page_url=page, page_anchor=anchor,
                                 data_url="", kind="", link_text="", status=f"failed: {type(e).__name__}"))
                continue
            links = data_links(final, body, ctype)
            if not links:
                rows.append(dict(state=state, region=region, page_url=page, page_anchor=anchor,
                                 data_url="", kind="", link_text="", status="ok: no data links found"))
            for u, (k, txt) in links.items():
                rows.append(dict(state=state, region=region, page_url=page, page_anchor=anchor,
                                 data_url=u, kind=k, link_text=txt, status="ok"))
            print(f"  [{n}/{total}] {state:16} {len(links):>3} links  {page[:76]}", flush=True)
            time.sleep(0.8)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["region", "state", "kind", "data_url", "link_text",
                                          "page_url", "page_anchor", "status"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    kinds = collections.Counter(r["kind"] for r in rows if r["kind"])
    print(f"\nwrote {OUT.relative_to(ROOT)} — {len(rows)} rows")
    print("  data links by kind:", dict(kinds.most_common()))
    print("  fetch failures:", dict(failed.most_common()))


if __name__ == "__main__":
    main()
