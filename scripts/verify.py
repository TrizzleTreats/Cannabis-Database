#!/usr/bin/env python3
"""Check the build: private data, domain allowlist, raw provenance, master table.

Run after any fetch or rebuild. Every check prints what it found, not just
pass/fail, because a count that silently went to zero looks like a pass.

Usage: python3 scripts/verify.py
"""
import collections, csv, hashlib, io, json, pathlib, re, subprocess, sys

from standard_types import CATEGORY_TO_TYPES, STANDARD_TYPES, types_for

ROOT = pathlib.Path(__file__).resolve().parent.parent
fails = []


def head(t):
    print(f"\n{t}\n" + "-" * len(t))


def check(ok, label, detail=""):
    print(f"  {'ok ' if ok else 'XX '}{label}{'  ' + detail if detail else ''}")
    if not ok:
        fails.append(label)


def git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True).stdout


def pdf_pages(p):
    """Spotlight reads PDFs with compressed object streams; a regex does not."""
    out = subprocess.run(["mdls", "-raw", "-name", "kMDItemNumberOfPages", str(p)],
                         capture_output=True, text=True).stdout.strip()
    return out if out.isdigit() else "?"


# ------------------------------------------------------------ private data
head("Private data must not be tracked")
tracked = [l for l in git("ls-files").splitlines() if "private" in l]
check(not tracked, "no tracked path contains 'private'", f"({len(tracked)} found)" if tracked else "")
ignored = git("check-ignore", "-v", "data/private/ct_backers_private.csv").strip()
check(bool(ignored), "data/private/ is git-ignored", ignored.split("\t")[0] if ignored else "NOT IGNORED")
for name in ("businesses_master.csv", "national_businesses.csv", "new_england_businesses.csv"):
    p = ROOT / "data/clean" / name
    if p.exists():
        with open(p, encoding="utf-8") as f:
            cols = next(csv.reader(f))
        has = "key_people_private" in cols
        print(f"  -- {name}: key_people_private {'present - strip before deploy' if has else 'absent'}")

# ------------------------------------------------------------- allowlist
head("Domain allowlist matches the domain list")
hosts = [l.strip() for l in open(ROOT / "domains/all-domains.txt") if l.strip()]
allow = json.loads((ROOT / ".claude/settings.json").read_text())["permissions"]["allow"]
rules = [a for a in allow if a.startswith("WebFetch(domain:")]
check(len(rules) == len(hosts), "one WebFetch rule per host", f"{len(rules)} rules / {len(hosts)} hosts")
check(len(hosts) == len(set(hosts)), "no duplicate hosts")
check(not any("einpresswire" in a for a in allow), "no secondary news host in the allowlist")

# -------------------------------------------------------- raw provenance
head("Every captured raw file exists, hashes match and opens as declared")
declared = {s["id"] for s in json.loads((ROOT / "scripts/sources.json").read_text())}
latest, retired, members = {}, set(), {}
for r in csv.DictReader(open(ROOT / "data/raw/manifest.csv")):
    # The manifest is an append-only log. An id that is no longer declared in
    # sources.json was superseded (a source redefined, e.g. Colorado's sheets
    # re-declared per tab), so its rows describe files that no longer exist.
    #
    # One declared source can be a SET of files rather than one file: New
    # Jersey's 517 per-business permit PDFs are declared once and logged
    # per file as "<declared id>:<filename>", so each keeps its own bytes and
    # sha256. Those are grouped and checked as a set, not listed one by one.
    set_id = r["id"].split(":", 1)[0]
    if r["id"] in declared:
        latest[r["id"]] = r
    elif ":" in r["id"] and set_id in declared:
        members.setdefault(set_id, {})[r["id"]] = r
    else:
        retired.add(r["id"])
if retired:
    print(f"  -- {len(retired)} superseded source ids in the log, no longer declared: "
          f"{', '.join(sorted(retired)[:4])}{' …' if len(retired) > 4 else ''}")
captured = missing = 0
for r in sorted(latest.values(), key=lambda x: (x["state"], x["id"])):
    if not r["status"].startswith(("ok", "skipped")):
        print(f"  -- {r['id']:30} not captured: {r['status'][:48]}")
        missing += 1
        continue
    p = ROOT / "data/raw" / r["state"] / r["filename"]
    if not p.exists():
        check(False, f"{r['id']} file present")
        continue
    b = p.read_bytes()
    if r["sha256"] and hashlib.sha256(b).hexdigest() != r["sha256"]:
        check(False, f"{r['id']} sha256 matches manifest")
        continue
    fmt, detail = r["format"], ""
    if fmt == "csv":
        rd = list(csv.reader(io.StringIO(b.decode("utf-8", "replace"))))
        detail = f"{len(rd) - 1} rows x {len(rd[0])} cols"
        if len(rd) < 2:
            check(False, f"{r['id']} has data rows")
            continue
    elif fmt == "pdf":
        if not b.startswith(b"%PDF"):
            check(False, f"{r['id']} is a PDF")
            continue
        detail = f"{pdf_pages(p)} pages"
    elif fmt == "geojson":
        detail = f"{len(json.loads(b.decode())['features'])} features"
    elif fmt == "xlsx":
        if not b.startswith(b"PK"):
            check(False, f"{r['id']} is an xlsx")
            continue
        detail = "zip ok"
    else:
        txt = re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ",
                                             b.decode("utf-8", "replace"), flags=re.S | re.I))
        n = len(re.sub(r"\s+", " ", txt).strip())
        detail = f"{n} chars visible"
        if n < 1500:
            check(False, f"{r['id']} rendered real text", detail)
            continue
    print(f"  ok {r['id']:30} {int(r['bytes']):>10,} B  {detail}")
    captured += 1

# File sets: one declared source, many files. Each is checked for existence,
# hash and format; the set is reported as one line so 517 PDFs do not drown
# everything else, with any file that fails named individually.
for set_id, rows in sorted(members.items()):
    ok_n = total_bytes = 0
    problems = []
    for r in sorted(rows.values(), key=lambda x: x["id"]):
        if not r["status"].startswith(("ok", "skipped")):
            problems.append(f"{r['filename']}: {r['status'][:40]}")
            continue
        p = ROOT / "data/raw" / r["state"] / r["filename"]
        if not p.exists():
            problems.append(f"{r['filename']}: not on disk")
            continue
        b = p.read_bytes()
        if r["sha256"] and hashlib.sha256(b).hexdigest() != r["sha256"]:
            problems.append(f"{r['filename']}: sha256 does not match the manifest")
            continue
        if r["format"] == "pdf" and not b.startswith(b"%PDF"):
            problems.append(f"{r['filename']}: not a PDF")
            continue
        ok_n += 1
        total_bytes += len(b)
    check(not problems, f"{set_id} — all {len(rows)} files present, hashed and open",
          f"{ok_n}/{len(rows)} ok, {total_bytes:,} B")
    for why in problems[:10]:
        print(f"     -- {why}")
    if len(problems) > 10:
        print(f"     -- ... and {len(problems) - 10} more")
    captured += ok_n
print(f"  => {captured} captured and verified, {missing} not captured")

# --------------------------------------------------------- clean tables
TABLES = ["new_england_licences.csv", "mid_atlantic_licences.csv",
          "regions_3_to_9_licences.csv"]
shapes = {}
for name in TABLES:
    path = ROOT / "data/clean" / name
    if not path.exists():
        print(f"\n{name}: not built yet")
        continue
    head(name)
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    cols = list(rows[0].keys())
    shapes[name] = cols
    print(f"  {len(rows)} rows x {len(cols)} columns")
    check(not [c for c in cols if "EIN" in c.upper() or "TIN" in c.upper()], "no EIN/TIN column")
    check(not [r for r in rows if not r["source_url"]], "every row has a source_url")
    check(not [r for r in rows if not r["data_as_of"]], "every row has a data_as_of")
    check(not [r for r in rows if not r["source"]], "every row has a source")
    dup = [k for k, v in collections.Counter((r["state"], r["licence_id"]) for r in rows).items() if v > 1]
    check(not dup, "licence ids unique per state", str(dup[:3]) if dup else "")
    nameless = collections.Counter(r["state"] for r in rows if not r["legal_name"])
    if nameless:
        print(f"  -- rows whose regulator publishes no business name: {dict(nameless)} "
              f"(upstream gap, flagged per row in extra_details)")
    else:
        check(True, "every row has a name")
    contra = 0
    for r in rows:
        sw, st = r["status"].lower(), r.get("standard_status", "")
        if st == "Active" and any(w in sw for w in ("revoked", "surrender", "denied", "suspended")):
            contra += 1
        if st in ("Expired", "Revoked", "Surrendered", "Suspended") and "operating" in sw and "not" not in sw:
            contra += 1
    check(contra == 0, "no row contradicts its own state wording", f"({contra})" if contra else "")

    # standard_type is the column one search spans every state with, so an
    # unknown value in it is worse than a missing row: a facet would quietly
    # drop the licence. Every row must carry exactly one of HANDOFF's 16, and
    # the tag list must agree with it. The builders do not write these columns
    # (scripts/add_standard_type.py does), so this is also the guard that
    # catches a rebuild having dropped them.
    allowed = set(STANDARD_TYPES)
    if "standard_type" not in cols:
        check(False, "standard_type column present",
              "run python3 scripts/add_standard_type.py --apply")
    else:
        bad_t = collections.Counter()
        bad_all, not_canon, lead_not_in = 0, 0, 0
        for r in rows:
            t, every = r["standard_type"], r.get("standard_types_all", "")
            if t not in allowed:
                bad_t[(r["state"], r["category"], t or "(blank)")] += 1
            parts = [p for p in (x.strip() for x in every.split(";")) if p]
            if not parts or any(p not in allowed for p in parts):
                bad_all += 1
            elif parts != [s for s in STANDARD_TYPES if s in parts]:
                not_canon += 1
            if t in allowed and t not in parts:
                lead_not_in += 1
        check(not bad_t, f"every standard_type is one of the {len(STANDARD_TYPES)} standard types",
              "" if not bad_t else f"{sum(bad_t.values())} rows, e.g. {list(bad_t.items())[:3]}")
        check(bad_all == 0, "every standard_types_all entry is a standard type",
              f"({bad_all} rows)" if bad_all else "")
        check(not_canon == 0, "standard_types_all is in canonical HANDOFF order",
              f"({not_canon} rows)" if not_canon else "")
        check(lead_not_in == 0, "the leading standard_type is one of the row's own types",
              f"({lead_not_in} rows)" if lead_not_in else "")
        # Recompute from the mapping: catches a hand-edited table, and a
        # partial re-run that left some rows on an older mapping.
        drift = collections.Counter()
        for r in rows:
            lead, every = types_for(r["category"], r["licence_type"])
            if lead is None:
                drift[(r["state"], r["category"], "no mapping")] += 1
            elif (lead, every) != (r["standard_type"], r.get("standard_types_all")):
                drift[(r["state"], r["category"], f"{r['standard_type']} != {lead}")] += 1
        check(not drift, "every standard_type still matches the recorded mapping",
              "" if not drift else f"{sum(drift.values())} rows, e.g. {list(drift.items())[:3]}")
        multi = sum(1 for r in rows if "; " in r.get("standard_types_all", ""))
        print(f"  -- type spread: {dict(collections.Counter(r['standard_type'] for r in rows).most_common())}")
        print(f"  -- {multi} rows authorise more than one activity "
              f"(the full set is in standard_types_all; standard_type is the lead)")

    # A blank standard_status is legitimate where a regulator publishes none,
    # but it must never be read as Active - so report it, loudly, per state.
    print("  -- per state:  rows | no standard_status | no county | status spread")
    for st in sorted({r["state"] for r in rows}):
        sr = [r for r in rows if r["state"] == st]
        nos = sum(1 for r in sr if not r.get("standard_status"))
        noc = sum(1 for r in sr if not r["county"])
        d = collections.Counter(r.get("standard_status") or "(none)" for r in sr)
        print(f"     {st}: {len(sr):>5} | {nos:>5} | {noc:>5} | {dict(d.most_common())}")
    print(f"  -- default search set (Active + Provisional): "
          f"{sum(1 for r in rows if r.get('standard_status') in ('Active', 'Provisional'))}")

if len(shapes) > 1:
    first = shapes[TABLES[0]]
    same = all(v == first for v in shapes.values())
    check(same, f"all {len(shapes)} regional tables share one column set, in order",
          f"{len(first)} columns" if same else str({k: len(v) for k, v in shapes.items()}))
    if not same:
        for n, v in shapes.items():
            print(f"     {n}: {len(v)} columns")
            odd = [c for c in v if c not in first] + [c for c in first if c not in v]
            if odd:
                print(f"       differs by: {odd}")
    # The standard type is what one search spans every state with, so the
    # combined spread is the number the database page will actually serve.
    allrows = [r for n in shapes
               for r in csv.DictReader(open(ROOT / 'data/clean' / n, encoding='utf-8'))]
    print(f"  -- combined rows across the regional tables: {len(allrows)}")
    if all("standard_type" in v for v in shapes.values()):
        spread = collections.Counter(r["standard_type"] for r in allrows)
        print(f"  -- combined standard_type spread across {len(STANDARD_TYPES)} standard types:")
        for t in STANDARD_TYPES:
            print(f"     {spread.get(t, 0):>7,}  {t}" + ("   <- none built yet" if not spread.get(t) else ""))
        unused = [t for t in STANDARD_TYPES if not spread.get(t)]
        if unused:
            print(f"     {len(unused)} standard types lead no row in the 26 built jurisdictions: "
                  f"{', '.join(unused)}")
        print(f"  -- {len(CATEGORY_TO_TYPES)} regulator/build category values map onto them "
              f"({len({r['category'] for r in allrows})} of them in use)")

# ------------------------------------------------- county validation
head("Counties must exist in their state")
cpath = ROOT / "data/raw/census_counties_by_state.csv"
if cpath.exists():
    official = collections.defaultdict(set)
    for r in csv.DictReader(open(cpath, encoding="utf-8")):
        official[r["state"]].add(r["county_basename"])
    # Connecticut uses its traditional eight counties by project decision
    # (12 Nov 2026), not the nine Planning Regions that replaced them as Census
    # county-equivalents in 2022. Current TIGER lists only the Planning
    # Regions, so the traditional names are the CORRECT value here and a
    # Planning Region is the error.
    CT_TRADITIONAL = {"Fairfield", "Hartford", "Litchfield", "Middlesex",
                      "New Haven", "New London", "Tolland", "Windham"}
    bad, ct_trad, offstate, known_bad = collections.Counter(), 0, 0, 0
    for name in TABLES:
        path = ROOT / "data/clean" / name
        if not path.exists():
            continue
        for r in csv.DictReader(open(path, encoding="utf-8")):
            c = r["county"].strip()
            if not c:
                continue
            if "premises outside the licensing state=" in r["extra_details"]:
                offstate += 1
                continue
            if r["state"] == "CT" and c in CT_TRADITIONAL:
                ct_trad += 1
                continue
            if c not in official.get(r["state"], set()):
                # A row that already says its county is wrong is a known gap,
                # not a regression. An UNflagged bad county is what must fail.
                if "county not valid for this state=" in r["extra_details"]:
                    known_bad += 1
                else:
                    bad[(r["state"], c)] += 1
    print(f"  official county list: {sum(len(v) for v in official.values())} counties "
          f"across {len(official)} states (Census TIGERweb)")
    print(f"  -- {ct_trad} CT rows use the traditional eight counties, the vocabulary this "
          f"project chose")
    ct_regions = 0
    for name in TABLES:
        path = ROOT / "data/clean" / name
        if path.exists():
            for r in csv.DictReader(open(path, encoding="utf-8")):
                if r["state"] == "CT" and "Planning Region" in r["county"]:
                    ct_regions += 1
    check(ct_regions == 0, "no CT row uses a Census Planning Region",
          "" if not ct_regions else f"{ct_regions} rows do")
    print(f"  -- {offstate} rows are flagged as premises outside their licensing state")
    print(f"  -- {known_bad} rows carry a county that is not their state's and say so on the row "
          f"(ambiguous names inherited from the 24 Oct 2026 table)")
    check(not bad, "every county exists in its own state",
          "" if not bad else f"{sum(bad.values())} rows, e.g. {list(bad.items())[:5]}")
else:
    print("  (county reference not built yet)")

# ------------------------------------------------------ NY reconciliation
head("New Jersey: every licence number traces to a published permit")
njp = ROOT / "data/clean/nj_crc_permits.csv"
if not njp.exists():
    print("  -- nj_crc_permits.csv not built; New Jersey carries no licence numbers")
else:
    recs = list(csv.DictReader(open(njp, encoding="utf-8")))
    permits = [r for r in recs if r["record_kind"] == "licence"]
    ends = [r for r in recs if r["record_kind"] != "licence"]
    numbers = {r["permit_number"] for r in permits}
    njrows = [r for r in csv.DictReader(open(ROOT / "data/clean/mid_atlantic_licences.csv",
                                             encoding="utf-8")) if r["state"] == "NJ"]
    # A number printed on two permits at one premises carries a ~n suffix, the
    # same discriminator NY's duplicate Location IDs use.
    bases = {r["licence_id"].split("~")[0] for r in njrows}
    real = [r for r in njrows if not r["licence_id"].startswith("NJ-")]
    invented = [r["licence_id"] for r in real if r["licence_id"].split("~")[0] not in numbers]
    absent = sorted(n for n in numbers if n not in bases)
    print(f"  permits parsed from the PDFs       {len(permits)} ({len(numbers)} distinct numbers)")
    print(f"  consumption-area endorsements      {len(ends)}  <- endorsements, NOT licences:"
          f" they are named on the licence they attach to and counted separately")
    print(f"  NJ rows carrying a real number     {len(real)} of {len(njrows)}")
    check(not invented, "every NJ licence number appears on a published permit",
          f"({len(invented)} invented: {invented[:3]})" if invented else "")
    check(not absent, "every published permit reaches the table",
          f"({len(absent)} absent: {absent[:3]})" if absent else "")
    nopermit = [r for r in njrows if r["licence_id"].startswith("NJ-NOPERMIT")]
    check(all(not r["standard_status"] for r in nopermit),
          "CRC-listed locations with no permit carry an EMPTY standard_status",
          f"{len(nopermit)} rows — empty must never be read as Active")
    stale = [r for r in njrows if r["county_source"].startswith("US Census geocoder")]
    check(not stale, "no NJ county_source invites a fill_counties revisit",
          f"({len(stale)} rows would be re-processed and relabelled)" if stale else "")
    # Against each row's own capture date, so this number does not drift with
    # the clock while the underlying PDFs sit unchanged.
    past = [r for r in njrows if len(r["expiry_date"]) == 10 and r["expiry_date"] < r["data_as_of"]]
    flagged = [r for r in past if "expiry had passed" in r["extra_details"]]
    check(len(past) == len(flagged),
          "every NJ row with a lapsed expiry says so on the row",
          f"{len(past)} lapsed as of capture, {len(flagged)} flagged")
    print(f"  -- those {len(past)} print an expiry that had already passed when captured, while "
          f"the CRC still lists the business as active; never reconciled")

head("New York: row count is not a licence count")
p = ROOT / "data/raw/new-york/jskf-tt3q_ocm_licences_2026-11-12.csv"
if p.exists():
    ny = list(csv.DictReader(open(p, encoding="utf-8-sig")))
    nums = {r["License Number"] for r in ny if r["License Number"].strip()}
    blank = sum(1 for r in ny if not r["License Number"].strip())
    print(f"  dataset rows                       {len(ny)}")
    print(f"  distinct licence numbers           {len(nums)}")
    print(f"  rows with NO licence number        {blank}   <- applicants under proximity protection")
    print(f"  rows with status Active            {sum(1 for r in ny if r['License Status'] == 'Active')}")
    print(f"  OCM 2025 Annual Report, 30 Nov 2025: 2,008 active across the five headline categories")
    print("  These figures are NOT expected to agree: the dataset is a year later, counts")
    print("  one row per location rather than per licence, and includes mere applicants.")
    print("  Do not reconcile them into a single number.")

head("Result")
if fails:
    print("  FAILED: " + "; ".join(fails))
    sys.exit(1)
print("  all checks passed")
