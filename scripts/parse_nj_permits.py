#!/usr/bin/env python3
"""Read New Jersey's permit PDFs into data/clean/nj_crc_permits.csv.

One row per permit, which is one page: the CRC issues a separate document per
licence, and a multi-class operator's packet holds several (Verano's five are
RE000001, RE000030, RE000002, C000009, M000007).

Each permit gives what the CRC's HTML list does not: the licence number, the
Commission's own class wording, the facility address with its county, and a full
expiration date rather than a year.

Two things this deliberately does NOT do:
  * It does not read a status off the document. A permit PDF is an issued
    licence with an expiry, not a statement that the business is open, and a
    past expiry is not proof the licence is dead - the CRC may simply not have
    posted the renewal. The expiry is recorded; any reading of it is flagged,
    never asserted.
  * It does not repair the regulator's values. A field that will not parse is
    left empty and the reason goes in parse_flags.

Usage:
  python3 scripts/parse_nj_permits.py [--out data/clean/nj_crc_permits.csv]
"""
import argparse, csv, hashlib, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PERMIT_DIR = ROOT / "data" / "raw" / "new-jersey" / "permits"
LINK_INDEX = PERMIT_DIR / "_link_index.csv"
COUNTIES = ROOT / "data" / "raw" / "census_counties_by_state.csv"
SOURCE_PAGE = "https://www.nj.gov/cannabis/businesses/permitted/"
SOURCE_ID = "nj-crc-permit-pdfs"

FIELDS = ["record_kind", "permit_number", "licence_class_state", "term", "program",
          "program_basis", "facility_name", "street_address", "address_line_2", "town",
          "county", "zip", "expiration_date", "endorsements", "associated_licence_number",
          "issuing_document", "link_section", "link_organisation",
          "link_business_types", "link_locations", "link_expiration_year",
          "pdf_filename", "pdf_page", "pdf_pages", "pdf_sha256", "source", "source_url",
          "data_as_of", "parse_flags"]

# Not every page is a licence. A Class 5 retailer that runs a consumption area
# gets a second page: an ENDORSEMENT, with its own number formed from the
# retailer's licence number plus -CA000n. Five exist (CA0001-CA0005). They are
# kept as their own record_kind and also named on the licence they attach to,
# because counting an endorsement as a licence would inflate the licence count.
CONSUMPTION_AREA = "consumption area endorsement"
LICENCE = "licence"

# The statute a permit cites is what settles medical vs adult-use. Both names are
# the Commission's own; neither is inferred from the licence class.
PROGRAMS = [
    ("Adult Use", "NJ Cannabis Regulatory, Enforcement Assistance, and Marketplace "
                  "Modernization Act, P.L.2021, C.16 (C.24:6I-31 et al.)",
     re.compile(r"MARKETPLACE\s+MODERNIZATION", re.I)),
    ("Medical", "Jake Honig Compassionate Use Medical Cannabis Act, P.L.2019, C.153 "
                "(N.J.S.A. 24:6I-1 et seq)",
     re.compile(r"JAKE\s+HONIG|24:6I-1\s+ET\s+SEQ", re.I)),
]


def captured_on():
    """The date this data is "as of" — the day the CRC list was captured.

    NOT date.today(): a parse is not a capture, and stamping the clock would
    silently move every row's date to whenever someone last re-ran this script,
    which is exactly the drift CLAUDE.md's "every fact carries a source and a
    date" rule exists to prevent. Nor the manifest's fetched_at, which is UTC
    and so reads a day later than the local session that captured these files,
    putting New Jersey a day out of step with the rest of a table built in one
    sitting.

    The vintage of a permit is the vintage of the list it was linked from, and
    that date is declared in sources.json as part of the saved page's filename.
    """
    for src in json.loads((ROOT / "scripts" / "sources.json").read_text()):
        if src["id"] == SOURCE_ID:
            found = re.search(r"(\d{4}-\d{2}-\d{2})", src["urls_from"])
            if not found:
                sys.exit(f"no capture date in the declared urls_from: {src['urls_from']}")
            return found.group(1)
    sys.exit(f"{SOURCE_ID} is not declared in scripts/sources.json")


def official_counties():
    out = {}
    with open(COUNTIES, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["state"] == "NJ":
                out[row["county_basename"].upper()] = row["county_basename"]
    if not out:
        sys.exit("no NJ counties in data/raw/census_counties_by_state.csv")
    return out


NJ_COUNTIES = None  # filled in main()


def pages_of(path):
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    return [(p.extract_text() or "") for p in reader.pages]


def squash(text):
    """Collapse the PDF's hard-wrapped label/value layout onto single lines.

    pypdf emits the permit's table as "LICENSE\n \nNUMBER: W000018", because the
    label is drawn in two cells. Joining the lines first means one regex can
    read it, instead of one regex per layout quirk.
    """
    lines = [l.strip() for l in text.splitlines()]
    return re.sub(r"\s+", " ", " ".join(l for l in lines if l))


def grab(pattern, text, flags=re.I):
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else ""


def parse_address(blob, flags):
    """FACILITY ADDRESS: <street>, <line2>, <town>, <COUNTY> NJ - <zip>

    The second slot is an address line that is usually empty, so the town is
    found by position from the end rather than by index from the start.
    """
    street = line2 = town = county = zipcode = ""
    tail = re.search(r"([A-Z][A-Z .'\-]*?)\s+NJ\s*-\s*(\d{5}(?:-\d{4})?)", blob)
    if tail:
        county_raw, zipcode = tail.group(1).strip(), tail.group(2)
        county = NJ_COUNTIES.get(county_raw.upper(), "")
        if not county:
            flags.append(f"county '{county_raw}' is not one of New Jersey's 21 counties")
        head = blob[: tail.start()].rstrip().rstrip(",")
    else:
        flags.append("address does not end in '<COUNTY> NJ - <zip>'")
        head = blob
    parts = [p.strip() for p in head.split(",")]
    parts = [p for p in parts] or [""]
    if len(parts) >= 2:
        street, town = parts[0], parts[-1]
        line2 = ", ".join(p for p in parts[1:-1] if p)
    else:
        street = parts[0]
        flags.append("no town could be separated from the street address")
    if not town:
        flags.append("town empty after splitting the address")
    return street, line2, town, county, zipcode


def parse_endorsement(flat, page_no, total):
    """A consumption-area endorsement page.

    Read before the licence path on purpose: this page also carries the words
    "LICENSE NUMBER:", inside "ASSOCIATED RETAILER AND LICENSE NUMBER: <holder>
    <number>", so a licence-shaped read of it captures the holder's first word
    as the licence number.
    """
    flags = []
    number = grab(r"ENDORSEMENT NUMBER:\s*([A-Z0-9][A-Z0-9\-]*)", flat)
    if not number:
        flags.append("no ENDORSEMENT NUMBER")
    associated = number.split("-CA")[0] if "-CA" in number else ""
    if not associated:
        flags.append(f"endorsement number '{number}' does not carry a licence number")

    holder = grab(r"ASSOCIATED RETAILER AND LICENSE NUMBER:\s*(.*?)\s*"
                  + (re.escape(number) if number else r"[A-Z0-9\-]+$"), flat)
    if not holder:
        flags.append("no associated retailer name")

    addr_blob = grab(r"CONSUMPTION AREA ADDRESS:\s*(.*?)\s*ENDORSEMENT NUMBER:", flat)
    street = line2 = town = county = zipcode = ""
    if addr_blob:
        street, line2, town, county, zipcode = parse_address(addr_blob, flags)
    else:
        flags.append("no CONSUMPTION AREA ADDRESS")

    expiry = iso_date(grab(r"EXPIRATION DATE:\s*(\d{1,2}/\d{1,2}/\d{4})", flat), flags)
    program, basis = programme_of(flat, flags)
    return {
        "record_kind": CONSUMPTION_AREA,
        "permit_number": number,
        "licence_class_state": "Consumption Area",
        "term": "",
        "program": program,
        "program_basis": basis,
        "facility_name": holder,
        "street_address": street,
        "address_line_2": line2,
        "town": town,
        "county": county,
        "zip": zipcode,
        "expiration_date": expiry,
        "endorsements": "",
        "associated_licence_number": associated,
        "issuing_document": "FINAL RECOMMENDATION FOR: CONSUMPTION AREA — "
                            "THIS ENDORSEMENT TO OPERATE A CONSUMPTION AREA",
        "pdf_page": str(page_no),
        "pdf_pages": str(total),
        "parse_flags": "; ".join(flags),
    }, None


def iso_date(raw, flags):
    if not raw:
        flags.append("no EXPIRATION DATE")
        return ""
    mm, dd, yyyy = raw.split("/")
    return f"{yyyy}-{int(mm):02d}-{int(dd):02d}"


def programme_of(flat, flags):
    for name, cite, pattern in PROGRAMS:
        if pattern.search(flat):
            return name, cite
    flags.append("no statute cited that identifies the programme")
    return "", ""


def parse_page(text, page_no, total):
    """One licence or one endorsement, or None if this page is neither."""
    flat = squash(text)
    if "CANNABIS REGULATORY COMMISSION" not in flat.upper():
        return None, "page carries no CRC heading"
    if re.search(r"ENDORSEMENT TO OPERATE A CONSUMPTION\s*AREA|ENDORSEMENT NUMBER:",
                 flat, re.I):
        return parse_endorsement(flat, page_no, total)
    flags = []

    number = grab(r"\bNUMBER:\s*([A-Z0-9][A-Z0-9\-]*)", flat)
    if not number:
        return None, "page has no LICENSE/PERMIT NUMBER"

    # "FINAL RECOMMENDATION FOR: ANNUAL CLASS 3 - WHOLESALER LEGISLATION STATEMENT..."
    head = grab(r"FINAL RECOMMENDATION FOR:\s*(.*?)\s*LEGISLATION STATEMENT", flat)
    term, licence_class = "", ""
    if head:
        m = re.match(r"(ANNUAL|CONDITIONAL|TESTING|INITIAL|RENEWAL)\s+(.*)$", head, re.I)
        if m:
            term, licence_class = m.group(1).upper(), m.group(2).strip()
        else:
            licence_class = head
            flags.append(f"no term word recognised in 'FINAL RECOMMENDATION FOR: {head}'")
    else:
        flags.append("no 'FINAL RECOMMENDATION FOR:' block")

    program, basis = programme_of(flat, flags)

    name = grab(r"FACILITY NAME:\s*(.*?)\s*(?:LICENSE|PERMIT)?\s*FACILITY ADDRESS:", flat)
    if not name:
        name = grab(r"FACILITY NAME:\s*(.*?)\s{2,}", flat)
        if not name:
            flags.append("no FACILITY NAME")

    addr_blob = grab(r"FACILITY ADDRESS:\s*(.*?)\s*(?:LICENSE|PERMIT)\s*NUMBER:", flat)
    if not addr_blob:
        addr_blob = grab(r"FACILITY ADDRESS:\s*(.*?)\s*NUMBER:", flat)
    street = line2 = town = county = zipcode = ""
    if addr_blob:
        street, line2, town, county, zipcode = parse_address(addr_blob, flags)
    else:
        flags.append("no FACILITY ADDRESS")

    expiry = iso_date(grab(r"EXPIRATION DATE:\s*(\d{1,2}/\d{1,2}/\d{4})", flat), flags)

    return {
        "record_kind": LICENCE,
        "permit_number": number,
        "licence_class_state": licence_class,
        "term": term,
        "program": program,
        "program_basis": basis,
        "facility_name": name,
        "street_address": street,
        "address_line_2": line2,
        "town": town,
        "county": county,
        "zip": zipcode,
        "expiration_date": expiry,
        "endorsements": "",
        "associated_licence_number": "",
        "issuing_document": f"FINAL RECOMMENDATION FOR: {head}" if head else "",
        "pdf_page": str(page_no),
        "pdf_pages": str(total),
        "parse_flags": "; ".join(flags),
    }, None


def main():
    global NJ_COUNTIES
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/clean/nj_crc_permits.csv")
    args = ap.parse_args()
    NJ_COUNTIES = official_counties()

    if not LINK_INDEX.exists():
        sys.exit(f"{LINK_INDEX.relative_to(ROOT)} missing — run fetch_nj_permits.py first")
    with open(LINK_INDEX, newline="", encoding="utf-8") as f:
        links = list(csv.DictReader(f))

    today = captured_on()
    rows, missing, unparsed = [], [], []
    for link in links:
        path = PERMIT_DIR / link["filename"]
        if not path.exists():
            missing.append(link)
            continue
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        try:
            pages = pages_of(path)
        except Exception as exc:
            unparsed.append((link["filename"], f"{type(exc).__name__}: {exc}"))
            continue
        found = 0
        for i, text in enumerate(pages, 1):
            permit, why = parse_page(text, i, len(pages))
            if permit is None:
                if why != "page carries no CRC heading" or len(pages) == 1:
                    unparsed.append((f'{link["filename"]} p{i}', why))
                continue
            permit.update({
                "link_section": link["section"],
                "link_organisation": link["organisation"],
                "link_business_types": link["business_types"],
                "link_locations": link["locations"],
                "link_expiration_year": link["expiration_year"],
                "pdf_filename": link["filename"],
                "pdf_sha256": sha,
                "source": "NJ CRC, Office of Licensing — issued permit PDF linked from the "
                          "Permitted & Licensed Cannabis Businesses page. The number, class "
                          "wording, address, county and expiry are the Commission's own; the "
                          "document states no status and none is inferred from it",
                "source_url": link["href"],
                "data_as_of": today,
            })
            rows.append(permit)
            found += 1
        if not found:
            unparsed.append((link["filename"], "no permit found on any page"))

    # Name each endorsement on the licence it attaches to, so the licence row
    # says it carries one without the endorsement being counted as a licence.
    licences = {r["permit_number"]: r for r in rows if r["record_kind"] == LICENCE}
    orphans = []
    for e in (r for r in rows if r["record_kind"] == CONSUMPTION_AREA):
        parent = licences.get(e["associated_licence_number"])
        if parent is None:
            orphans.append(e)
            e["parse_flags"] = "; ".join(filter(None, [
                e["parse_flags"],
                f"no licence row for associated number '{e['associated_licence_number']}'"]))
            continue
        parent["endorsements"] = "; ".join(filter(None, [
            parent["endorsements"], f'Consumption Area ({e["permit_number"]})']))

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})

    shown = out.relative_to(ROOT) if out.is_relative_to(ROOT) else out
    print(f"{len(rows)} records from {len(links) - len(missing)} PDFs -> {shown}")
    lic = [r for r in rows if r["record_kind"] == LICENCE]
    end = [r for r in rows if r["record_kind"] == CONSUMPTION_AREA]
    print(f"  licences                     {len(lic)}")
    print(f"  consumption-area endorsements {len(end)}"
          + (f" ({len(orphans)} not matched to a licence)" if orphans else " (all matched)"))
    print(f"  distinct licence numbers     {len({r['permit_number'] for r in lic})}")

    # A repeated number is a finding, not a parse error: in New Jersey as in
    # Washington the number belongs to the premises, so one number can carry
    # two holders. Printed in full so the difference is visible, never merged.
    seen = {}
    for r in lic:
        seen.setdefault(r["permit_number"], []).append(r)
    for num, group in sorted(seen.items()):
        if len(group) > 1:
            print(f"    {num} appears on {len(group)} permits:")
            for g in group:
                print(f"       {g['facility_name']} | {g['street_address']}, {g['town']} "
                      f"({g['county']}) | expires {g['expiration_date']} | {g['pdf_filename']}")
    flagged = [r for r in rows if r["parse_flags"]]
    print(f"  rows carrying a parse flag: {len(flagged)}")
    for r in flagged[:15]:
        print(f"    {r['permit_number']:12} {r['parse_flags']}  [{r['pdf_filename']}]")
    if missing:
        print(f"  PDFs declared but not on disk: {len(missing)}")
        for m in missing[:10]:
            print(f"    {m['filename']}  ({m['organisation']})")
    if unparsed:
        print(f"  pages that yielded no permit: {len(unparsed)}")
        for f_, why in unparsed[:15]:
            print(f"    {f_}  {why}")
    print(f"  no county: {sum(1 for r in rows if not r['county'])}"
          f" | no expiry: {sum(1 for r in rows if not r['expiration_date'])}"
          f" | no programme: {sum(1 for r in rows if not r['program'])}")


if __name__ == "__main__":
    main()
