#!/usr/bin/env python3
"""Build data/clean/mid_atlantic_licences.csv from the raw files in data/raw/.

Same columns as the New England table plus `extra_details`, the state-specific
slot HANDOFF's schema calls for, so the two tables union cleanly later.

What each jurisdiction actually publishes differs enormously, and the table says
so per row rather than papering over it:

  NY  OCM Socrata dataset — licence numbers, statuses, counties. The only
      jurisdiction here that publishes a real registry. One row per licence and
      location; 385 rows are live applications with no licence number at all.
  DC  Two ArcGIS layers — licence numbers (ABCA_NUMBER), statuses, wards.
  PA  PASDA's DOH dispensary layer — locations only. No permit numbers, no
      statuses, no counties, and a Jan 2025 vintage.
  MD  MCA dispensary locator table — names, addresses, counties. Dispensaries
      only; no numbers, no statuses.
  NJ  CRC permitted-businesses page — organisations, not licences. Business
      types are given per organisation, never per location.
  DE  OMC dispensaries page — storefront addresses only.

Where a regulator publishes no licence number, the id is assigned locally and
`source` says so, the same convention the New England table uses for New
Hampshire. Counties are left empty wherever no source supplies one — never
inferred from a town name.

Usage: python3 scripts/build_mid_atlantic.py [--dry-run]
"""
import argparse, collections, csv, html, json, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from nj_towns import norm_org, norm_town, resolve_town, same_town
import xlsx_reader
from verify_nj_permit_counties import (AGREES, DIFFERS_CONFIRMED,
                                      DIFFERS_UNRESOLVED)

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "clean" / "mid_atlantic_licences.csv"
NE = ROOT / "data" / "clean" / "new_england_licences.csv"
TODAY = "2026-11-12"   # the date the files declared below were read; see raw_files.resolve

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from raw_files import current, resolve  # noqa: E402

LOCAL_ID = "licence_id assigned locally — the regulator publishes no licence number in this source"


def cells(tr):
    return [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", c))).strip().strip("​")
            for c in re.findall(r"<t[dh].*?</t[dh]>", tr, re.S | re.I)]


def tables(path):
    t = current(path)[0].read_text(errors="replace")
    return [re.findall(r"<tr.*?</tr>", tb, re.S | re.I)
            for tb in re.findall(r"<table.*?</table>", t, re.S | re.I)]


def mdy(d):
    d = (d or "").strip()
    if not d:
        return ""
    if "T" in d:
        d = d.split("T")[0]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
        return d
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})", d)
    if m:
        y = m.group(3)
        if len(y) == 2:                     # the DOH list writes 2/15/18
            y = ("20" if int(y) < 70 else "19") + y
        return f"{y}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}"
    if re.fullmatch(r"\d{13}", d):          # epoch milliseconds (ArcGIS)
        from datetime import datetime, timezone
        return datetime.fromtimestamp(int(d) / 1000, timezone.utc).strftime("%Y-%m-%d")
    return d


def extras(**kw):
    return "; ".join(f"{k.replace('_', ' ')}={v}" for k, v in kw.items() if v not in ("", None))


# ------------------------------------------------------------------ New York
NY_MAP = {
    "Adult-Use Retail Dispensary License": ("Adult Use", "Retail Store"),
    "Adult-Use Conditional Retail Dispensary License": ("Adult Use", "Retail Store"),
    "Adult-Use Registered Organization Dispensary License": ("Adult Use; Medical", "Retail Store"),
    "Adult-Use Microbusiness License": ("Adult Use", "Microbusiness"),
    "Adult-Use Processor License": ("Adult Use", "Manufacturing"),
    "Adult-Use Processor Type Three-Branding": ("Adult Use", "Manufacturing"),
    "Adult-Use Processor Type Three-Flower": ("Adult Use", "Manufacturing"),
    "Adult-Use Cultivator License": ("Adult Use", "Cultivation"),
    "Adult-Use Distributor License": ("Adult Use", "Transport & Distribution"),
    "Registered Organization": ("Medical", "Medical Dispensary"),
}
# The status CODE is more specific than the label: "Inactive" covers expired,
# surrendered, suspended and cancelled, which must never be merged.
NY_STATUS = {"LICACT": "Active", "Pending": "Pending", "LICEXP": "Expired",
             "LICSURR": "Surrendered", "LICSUSPEN": "Suspended", "LICCAN": "Canceled"}
NY_SRC = "NY OCM, Current OCM Licenses (data.ny.gov jskf-tt3q)"
NY_URL = "https://data.ny.gov/d/jskf-tt3q"


def build_ny(blank, unmapped):
    rows = []
    path, asof = resolve("new-york/jskf-tt3q_ocm_licences_2026-11-12.csv", TODAY)
    with open(path, encoding="utf-8-sig") as f:
        src = list(csv.DictReader(f))
    repeats = collections.Counter(r["License Number"] for r in src if r["License Number"].strip())
    # One application can cover several proposed locations, so its number is not
    # a unique key either.
    app_repeats = collections.Counter(r["Application Number"].strip() for r in src
                                      if not r["License Number"].strip() and r["Application Number"].strip())
    # OCM attaches one Location ID to two different addresses on a handful of
    # applicant rows, so even (application, location) is not unique. Record the
    # defect rather than letting rows collide silently.
    app_loc = collections.Counter((r["Application Number"].strip(), r["Location ID"].strip())
                                  for r in src if not r["License Number"].strip())
    app_loc_n = collections.Counter()
    seen = collections.Counter()
    for i, r in enumerate(src, 1):
        num, loc = r["License Number"].strip(), r["Location ID"].strip()
        ltype = r["License Type"].strip()
        program, category = NY_MAP.get(ltype, ("", ""))
        if ltype not in NY_MAP:
            unmapped.append(("NY License Type", ltype))
        code = r["License Status Code"].strip()
        std = NY_STATUS.get(code, "")
        if code and not std:
            unmapped.append(("NY License Status Code", code))
        if num:
            # A licence with several locations needs the location in its key.
            lid = f"{num}#{loc}" if repeats[num] > 1 and loc else num
            note = dup_loc = ""
        else:
            # A live application, not a licence. Pending keeps it out of the
            # default Active+Provisional search by design.
            app = r["Application Number"].strip()
            seen["app"] += 1
            dup_loc = ""
            if app:
                lid = f"NY-APP-{app}#{loc}" if app_repeats[app] > 1 and loc else f"NY-APP-{app}"
                if app_loc[(app, loc)] > 1:
                    app_loc_n[(app, loc)] += 1
                    lid = f"{lid}~{app_loc_n[(app, loc)]}"
                    dup_loc = ("OCM attaches this Location ID to more than one address in its own "
                               "dataset — source defect; the id carries a local suffix to keep rows distinct")
            else:
                lid = f"NY-APP-ROW{i:04d}"
            if not app:
                seen["app_no_number"] += 1
            note = ("APPLICATION, NOT A LICENCE — OCM publishes proposed adult-use retail and "
                    "medical dispensary applicants under proximity protection. No licence number exists.")
        row = dict(blank)
        row.update({
            "licence_id": lid, "state": "NY", "program": program, "category": category,
            "licence_type": ltype, "tier": r["Tier Type"].strip(),
            "legal_name": r["Entity Name"].strip(), "dba": r["DBA"].strip(),
            "holder_is_individual": "N",
            "status": "; ".join(x for x in (r["License Status"].strip(),
                                            r["Operational Status"].strip()) if x),
            "standard_status": std,
            "issue_date": mdy(r["Issued Date"]), "expiry_date": mdy(r["Expiration Date"]),
            "street_address": ", ".join(x for x in (r["Address Line 1"].strip(), r["Address Line 2"].strip(),
                                                    r["City"].strip(), r["State"].strip(),
                                                    r["Zip Code"].strip()) if x),
            "town": r["City"].strip(), "town_as_listed": r["City"].strip(),
            "county": r["County"].strip(),
            "county_source": "OCM dataset County field" if r["County"].strip() else "",
            "location_basis": "Licensed premises" if num else "Proposed location (application)",
            "website": r["Business Website"].strip(),
            "contact_name": r["Primary Contact Name"].strip(), "contact_is_law_firm": "",
            "source": NY_SRC + (f" — {LOCAL_ID}" if not num else ""),
            "source_url": NY_URL, "data_as_of": asof,
            "extra_details": extras(
                location_id=loc, region=r["Region"].strip(),
                application_number=r["Application Number"].strip(),
                see_category=r["SEE Category"].strip(), processor_type=r["Processor Type"].strip(),
                business_purpose=r["Business Purpose"].strip(),
                effective_date=mdy(r["Effective Date"]),
                retail_opened=mdy(r["Retail Date Opened to Public"]),
                state_status_code=code, location_id_defect=dup_loc if not num else "",
                activity_tags=",".join(k for k, v in (
                    ("Extraction", r["Processing Activities Extraction"]),
                    ("Infusion/Edibles", r["Processing Activities Blending and Infusing"]),
                    ("Packaging", r["Processing Activities Packaging and Labeling"]),
                    ("Branding", r["Processing Activities Branding"]),
                ) if v.strip().lower() in ("yes", "y", "true")),
                note=note),
        })
        rows.append(row)
    return rows, seen


# ---------------------------------------------------- District of Columbia
DC_LAYERS = [("dc_licensed_medical_cannabis_facilities_non_retailer.geojson", 33),
             ("dc_licensed_medical_cannabis_retailer.geojson", 31)]
DC_CAT = {"Retailer": "Retail Store", "Courier": "Delivery", "Testing Laboratory": "Testing Lab"}
DC_STATUS = {"Active": "Active", "Safekeeping with Location": "Suspended",
             "Safekeeping": "Suspended", "Emergency Closure": "Suspended"}


def build_dc(blank, unmapped):
    rows = []
    for fname, layer in DC_LAYERS:
        path, asof = resolve(f"district-of-columbia/{fname}", TODAY)
        d = json.loads(path.read_text())
        for ft in d["features"]:
            p = ft["properties"]
            ftype = (p.get("FACILITY_TYPE") or "").strip()
            cat = DC_CAT.get(ftype) or ("Cultivation" if "Cultivation" in ftype
                                        else "Manufacturing" if "Manufacturer" in ftype else "")
            if not cat:
                unmapped.append(("DC FACILITY_TYPE", ftype))
            raw_status = (p.get("STATUS") or "").strip()
            std = DC_STATUS.get(raw_status, "")
            if raw_status and not std:
                unmapped.append(("DC STATUS", raw_status))
            num = (p.get("ABCA_NUMBER") or "").strip()
            g = ft.get("geometry") or {}
            lon, lat = (g.get("coordinates") or ["", ""])[:2] if g.get("type") == "Point" else ("", "")
            row = dict(blank)
            row.update({
                "licence_id": num or f"DC-L{layer}-OBJ{p.get('OBJECTID')}",
                "state": "DC", "program": "Medical", "category": cat,
                "licence_type": ftype or (p.get("LICENSE_TYPE") or "").strip(),
                "legal_name": (p.get("ENTITY_NAME") or p.get("NAME") or "").strip(),
                "dba": (p.get("TRADE_NAME") or "").strip(), "holder_is_individual": "N",
                "status": raw_status, "standard_status": std,
                "issue_date": mdy(str(p.get("ISSUE_DATE") or "")),
                "expiry_date": mdy(str(p.get("EXPIRATION_DATE") or "")),
                "street_address": (p.get("ADDRESS") or "").strip(),
                "town": "Washington", "town_as_listed": "",
                # DC is a single county-equivalent (FIPS 11001); wards are the
                # local tier below it and are kept in extra_details.
                "county": "District of Columbia", "county_source": "DC is coextensive with its county-equivalent",
                "location_basis": "Licensed premises",
                "source": f"DC ABCA via DC Open Data, Health_WebMercator MapServer layer {layer}"
                          + ("" if num else f" — {LOCAL_ID}"),
                "source_url": f"https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Health_WebMercator/MapServer/{layer}",
                "data_as_of": asof,
                "extra_details": extras(ward=p.get("WARD"), anc=p.get("ANC"), smd=p.get("SMD"),
                                        endorsements=p.get("ENDORSEMENTS"),
                                        applicant_type=p.get("APPLICANT_TYPE"),
                                        latitude=lat, longitude=lon,
                                        gis_last_edited=mdy(str(p.get("LAST_EDITED_DATE") or "")),
                                        note="GIS metadata records the non-retailer layer as supplied by ABCA on 31 Oct 2025; it is not a live registry."),
            })
            rows.append(row)
    return rows


# -------------------------------------------------------------- Pennsylvania
PA_TOWN_FIX = {"Bulter": "Butler"}   # audit-documented typo; original kept in town_as_listed
PA_SRC = ("PA DOH, Medical Marijuana Dispensaries in Pennsylvania with Product "
          f"(product availability as of 10 Nov 2026) — {LOCAL_ID}")
PA_URL = "https://www.pa.gov/agencies/health/programs/medical-marijuana/dispensaries"
# Each row: <available from> <open on> <product Y/N> <name + street + city> Pennsylvania <zip> <phone> [website]
PA_ROW = re.compile(r"^(\d{1,2}/\d{1,2}/\d{2,4})\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(Yes|No)\s+"
                    r"(.+?)\s+Pennsylvania\s+(\d{5}[\d\-]*)\s+([\d\-\(\)\. ]{7,})\s*(\S*)$")
PA_SUFFIX = (r"(?:Ave|Avenue|Rd|Road|Blvd|Boulevard|Hwy|Highway|Pike|Pkwy|Parkway|St|Street|Dr|Drive|"
             r"Ln|Lane|Ct|Court|Pl|Place|Terrace|Ter|Way|Cir|Circle|Loop|Trail|Trl|Sq|Square|Row|Run|"
             r"Mall|Plaza|Commons|Crossing|Centre|Center|Ext|Extension|Turnpike|Tpke|Bypass)")
PA_UNIT = r"(?:Suite|Ste|Unit|Apt|Bldg|Floor|Fl|Rm|#)\.?\s*[\w\-]+"


def pa_split(blob):
    """'Sunnyside - Butler County 201 Pillow Street Bulter' ->
       (name, street, city). The street starts at the first number-led token;
       the city follows the last street suffix or unit. Some rows run the name
       and street together with no space ('...Plymouth Meeting420 Plymouth Rd'),
       and some streets have no suffix at all ('20269 Route 19'), so the city
       falls back to the trailing part of the dispensary's own name, which DOH
       writes as 'Brand - City'."""
    blob = re.sub(r"([A-Za-z])(\d{2,})", r"\1 \2", blob)   # re-space a run-together row
    m = re.search(r"(?:^|\s)(\d+[\w\-]*\s)", blob)
    if not m:
        return blob.strip(), "", ""
    name = blob[:m.start()].strip()
    rest = blob[m.start():].strip()
    cut = None
    for mm in re.finditer(rf"\b{PA_SUFFIX}\.?\b|{PA_UNIT}", rest, re.I):
        if rest[mm.end():].strip(" ,."):
            cut = mm.end()
    if cut is not None:
        street, city = rest[:cut].strip(" ,"), rest[cut:].strip(" ,.")
        # A bare unit designator can sit between the suffix and the city
        # ('...High Street A Pottstown'); keep it with the street.
        mu = re.match(r"^((?:Ste\.?|Suite|Unit|#)?\s*[A-Z0-9][A-Z0-9\-]{0,3})\s+(?=[A-Z][a-z])", city)
        if mu:
            street, city = f"{street} {mu.group(1)}".strip(), city[mu.end():].strip()
        return name, street, city
    # No street suffix: take the city from the name's own ' - City' tail and
    # strip that city off the end of the address blob.
    tail = name.rsplit(" - ", 1)[-1].strip() if " - " in name else ""
    if tail and rest.endswith(tail):
        return name, rest[: -len(tail)].strip(" ,"), tail
    return name, rest, tail


def build_pa(blank):
    """Parse the DOH dispensary PDF. It supersedes the PASDA layer, which is a
    Jan 2025 vintage; PASDA is kept in data/raw/ for its coordinates."""
    from pypdf import PdfReader
    path, asof = resolve("pennsylvania/pa_doh_dispensaries_with_product_current.pdf", "2026-11-10")
    reader = PdfReader(path)
    text = "\n".join(pg.extract_text() or "" for pg in reader.pages)
    rows, unparsed = [], 0
    # The PDF uses non-breaking and other unicode spaces; normalise them or the
    # row pattern fails on lines that look identical to the eye.
    text = re.sub(r"[\u00a0\u2000-\u200b\u202f\u205f\u3000]", " ", text)
    for line in (re.sub(r"[ \t]+", " ", l).strip() for l in text.splitlines()):
        m = PA_ROW.match(line)
        if not m:
            # Header and legend lines are expected; count anything that looks
            # like a data row but did not parse.
            if re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}\s", line):
                unparsed += 1
            continue
        avail, opened, product, blob, zipc, phone, site = m.groups()
        name, street, city = pa_split(blob)
        listed = city.strip()
        if not listed:
            unparsed += 1
            continue
        town = PA_TOWN_FIX.get(listed, listed)
        row = dict(blank)
        row.update({
            "licence_id": f"PA-DISP-{len(rows) + 1:04d}", "state": "PA",
            "program": "Medical", "category": "Retail Store",
            "licence_type": "Medical Marijuana Dispensary",
            "legal_name": name.strip(), "holder_is_individual": "N",
            # DOH publishes no status in this list; every entry is an operating
            # dispensary, which is what "open on" records.
            "status": "Open (DOH lists operating dispensaries only; no status column)",
            "standard_status": "Active",
            "first_issue_date": mdy(opened),
            "street_address": ", ".join(x for x in (street.strip(), town, "PA", zipc) if x),
            "town": town, "town_as_listed": listed,
            "location_basis": "Licensed premises",
            "website": site.strip(), "contact_phone": phone.strip(), "contact_is_law_firm": "N",
            "source": PA_SRC, "source_url": PA_URL, "data_as_of": asof,
            "extra_details": extras(
                product_available=product, medical_available_from=mdy(avail), opened_on=mdy(opened),
                zip_code=zipc,
                town_typo="listed as 'Bulter'; the facility name confirms Butler" if listed in PA_TOWN_FIX else "",
                zip_conflict=("ZIP 19706 for a King of Prussia address — its sibling King of Prussia rows "
                              "carry 19406, and 19706 is a Delaware ZIP. The audit flagged this; DOH "
                              "publishes it, so it is recorded as published and not rewritten")
                             if (listed == "King of Prussia" and zipc.startswith("19706")) else "",
                note="DOH publishes no permit number, licence status or county in this list. It supersedes "
                     "the PASDA DOH-2025 layer (181 locations, Jan 2025 vintage), which is kept in "
                     "data/raw/ for its coordinates. 196 rows here matches MMAB's own count of 196 "
                     "dispensary locations as of 1 June 2026."),
        })
        rows.append(row)
    if unparsed:
        print(f"  PA: {unparsed} date-leading lines did not match the row pattern")
    return rows


# ----------------------------------------------------------------- New Jersey
# NJ is built from the per-business permit PDFs, NOT from the HTML table. The
# table publishes organisations - business types per organisation, locations in
# one cell, and an expiration YEAR - so a row built from it is an
# organisation-by-location guess with no licence number. Each table row also
# links the issued permit, and that document is the licence: it carries the
# number, the Commission's own class wording, the facility address with its
# county, and a full expiry date. See scripts/parse_nj_permits.py.
#
# REQUIRES data/clean/nj_crc_permits.csv. Pipeline order:
#   fetch_nj_permits.py -> parse_nj_permits.py -> verify_nj_permit_counties.py
#   -> build_mid_atlantic.py -> add_standard_type.py --apply -> verify.py
NJ_PERMITS = ROOT / "data" / "clean" / "nj_crc_permits.csv"

# CRC class -> this table's `category`. Every value is one standard_types.py
# already knows, so no new vocabulary enters the table: a medical retailer is
# Retail Store with program=Medical (the same call PA's 197 medical-only
# dispensaries already get here), and wholesaler and distributor are both
# Transport & Distribution, which NJ's rows already used.
NJ_PERMIT_CAT = {
    "CLASS 1 - CULTIVATOR": "Cultivation",
    "CLASS 2 - MANUFACTURER": "Manufacturing",
    "CLASS 3 - WHOLESALER": "Transport & Distribution",
    "CLASS 4 - DISTRIBUTOR": "Transport & Distribution",
    "CLASS 5 - RETAILER": "Retail Store",
    "CLASS 6 - DELIVERY": "Delivery",
    "MEDICAL CULTIVATOR": "Cultivation",
    "MEDICAL MANUFACTURER": "Manufacturing",
    "MEDICAL RETAILER": "Retail Store",
}
# For a CRC-listed location with no permit of its own, the only activity the CRC
# publishes is the ORGANISATION's business-type list, which it gives per
# organisation and never per location. Those rows therefore take the
# organisation's types, exactly as this table did for every NJ row before the
# permits were read, with the row saying the types are not confirmed for that
# location. Leaving `category` empty instead is not the safer option: it empties
# a search column, and standard_types.py refuses to write a blank standard_type
# because a blank reads as "no such licence" rather than "not classified".
NJ_CAT = {"Retailer": "Retail Store", "Dispensing": "Retail Store",
          "Manufacturer": "Manufacturing", "Manufacturing": "Manufacturing",
          "Cultivator": "Cultivation", "Cultivating": "Cultivation",
          "Delivery": "Delivery", "Wholesaler": "Transport & Distribution",
          "Distributor": "Transport & Distribution", "Consumption Area": "Consumption Lounge"}
NJ_SRC = ("NJ CRC, Office of Licensing — issued permit PDF linked from the Permitted & "
          "Licensed Cannabis Businesses page")
NJ_URL = "https://www.nj.gov/cannabis/businesses/permitted/"
# The CRC's own heading over both tables. It is the only status wording the CRC
# publishes for these businesses, and it is what standard_status Active rests
# on - never a reading of the expiry date.
NJ_ACTIVE = "Active Cannabis Business Permits & Licenses"


def nj_permit_rows():
    """The parsed permits, split into licences and endorsements."""
    if not NJ_PERMITS.exists():
        raise SystemExit(
            f"{NJ_PERMITS.relative_to(ROOT)} is missing — New Jersey is built from the "
            f"permit PDFs.\n  Run: python3 scripts/fetch_nj_permits.py && "
            f"python3 scripts/parse_nj_permits.py")
    with open(NJ_PERMITS, newline="", encoding="utf-8") as f:
        recs = list(csv.DictReader(f))
    if "county_check" not in (recs[0] if recs else {}):
        raise SystemExit(
            f"{NJ_PERMITS.relative_to(ROOT)} has no county_check column — the permit "
            f"counties have not been checked against the Census geocoder.\n"
            f"  Run: python3 scripts/verify_nj_permit_counties.py")
    return ([r for r in recs if r["record_kind"] == "licence"],
            [r for r in recs if r["record_kind"] != "licence"])


def nj_county(r, flags):
    """(county, county_source). Both counties stay on the row when they differ.

    The Census result only displaces the permit's own printed county where the
    two agree on the address and differ on nothing but the county field - which
    the permit's own ZIP is what establishes. Where the geocoder matched a
    different address it settles nothing, and the permit's value stands, flagged.
    """
    printed, census, check = r["county"].strip(), r["county_geocoded"].strip(), r["county_check"]
    if check == AGREES:
        return printed, ("NJ CRC permit PDF (facility address), confirmed at address level "
                         "by the US Census geocoder")
    if check == DIFFERS_CONFIRMED:
        flags["county as printed on the permit"] = (
            f"{printed} — wrong: the permit's own ZIP {r['zip']} and the US Census geocoder "
            f"agree this address is in {census}. Published as {census}, original kept here")
        # Deliberately led by the permit, not by "US Census geocoder":
        # fill_counties.py revisits any row whose county_source starts with that
        # phrase, and this county is already adjudicated — a second pass keyed
        # on the full town name can miss the cache and relabel it.
        return census, ("NJ CRC permit PDF (facility address) with its county field corrected "
                        "by the US Census geocoder at address level, which the permit's own "
                        "ZIP corroborates")
    if check == DIFFERS_UNRESOLVED:
        flags["county disputed"] = (
            f"the permit prints {printed}; the US Census geocoder returned {census} but "
            f"matched a different address ({r['geocoded_address']}), so the two are NOT "
            f"reconciled. The regulator's printed value stands until a person checks it")
        return printed, ("NJ CRC permit PDF (facility address); disputed by the Census "
                         "geocoder and unresolved — see extra_details")
    flags["county not confirmed"] = (
        f"the US Census geocoder returned no match for this address, so the permit's "
        f"printed county is unverified")
    return printed, "NJ CRC permit PDF (facility address); not confirmed by the Census geocoder"


def build_nj(blank, unmapped):
    licences, endorsements = nj_permit_rows()
    with open(RAW / "new-jersey" / "permits" / "_link_index.csv", newline="",
              encoding="utf-8") as f:
        links = list(csv.DictReader(f))

    # Each organisation's municipalities and business types, as the CRC's HTML
    # spells them - the only place the full town names and the organisation's
    # own type list exist.
    listed, types_of = {}, {}
    for l in links:
        key = norm_org(l["organisation"])
        for town in (t.strip() for t in l["locations"].split(",")):
            if town:
                listed.setdefault(key, set()).add(town)
        if l["business_types"]:
            types_of.setdefault(key, set()).add(l["business_types"])

    endorsed = {}
    for e in endorsements:
        endorsed.setdefault(e["associated_licence_number"], []).append(e)

    # A licence number belongs to the premises and can carry two holders, so a
    # repeated number takes NY's own discriminator (~1, ~2) to stay distinct.
    repeats = collections.Counter(r["permit_number"] for r in licences)
    seen = collections.Counter()
    by_org = collections.Counter(norm_org(r["link_organisation"]) for r in licences)

    rows, claimed = [], set()
    for r in licences:
        cls = r["licence_class_state"].strip()
        category = NJ_PERMIT_CAT.get(cls.upper())
        if not category:
            unmapped.append(("NJ permit class", cls))
            category = ""
        num = r["permit_number"]
        if repeats[num] > 1:
            seen[num] += 1
            licence_id = f"{num}~{seen[num]}"
        else:
            licence_id = num

        key = norm_org(r["link_organisation"])
        full_town, why = resolve_town(r["town"], sorted(listed.get(key, set())))
        town = full_town or r["town"].title()
        if full_town:
            claimed.add((key, norm_town(full_town)))
        claimed.add((key, norm_town(r["town"])))

        flags = {}
        county, county_source = nj_county(r, flags)
        if not full_town:
            flags["town spelling not matched"] = (
                f"the permit prints '{r['town']}'; the CRC's HTML lists "
                f"{sorted(listed.get(key, set())) or 'no locations'} for this organisation ({why})")
        # Judged against the data's own capture date, not the clock: the row is a
        # snapshot, so "has passed" has to mean "had passed when this was
        # captured". Comparing with today would make the built file say something
        # different every day it is rebuilt from the same unchanged PDFs.
        if r["expiration_date"] and r["expiration_date"] < r["data_as_of"]:
            flags["permit expiry had passed when this was captured"] = (
                f"expired {r['expiration_date']}, captured {r['data_as_of']}, yet the CRC "
                f"still publishes this business under '{NJ_ACTIVE}' — the two are not "
                f"reconciled and neither is read off the other")
        ends = endorsed.get(num, [])

        row = dict(blank)
        row.update({
            "licence_id": licence_id, "state": "NJ",
            "program": r["program"], "category": category,
            "licence_type": cls.title().replace(" - ", " — "),
            "legal_name": r["facility_name"], "holder_is_individual": "N",
            "status": f"Listed by the CRC under '{NJ_ACTIVE}'",
            "standard_status": "Active",
            "expiry_date": r["expiration_date"],
            "street_address": r["street_address"], "town": town,
            "county": county, "town_as_listed": r["town"],
            "location_basis": "Facility address as printed on the CRC's issued permit",
            "county_source": county_source,
            "group_id": f"NJ-ORG-{key.replace(' ', '-')[:28]}" if by_org[key] > 1 else "",
            "linked_group": r["link_organisation"] if by_org[key] > 1 else "",
            "licences_in_group": str(by_org[key]) if by_org[key] > 1 else "",
            "source": NJ_SRC, "source_url": r["source_url"], "data_as_of": r["data_as_of"],
            "extra_details": extras(
                licence_class_as_printed=cls,
                issuing_document=r["issuing_document"],
                term=r["term"],
                programme_basis=r["program_basis"],
                zip_code=r["zip"],
                address_line_2=r["address_line_2"],
                endorsements="; ".join(f'Consumption Area ({e["permit_number"]}, expires '
                                       f'{e["expiration_date"]})' for e in ends),
                organisation_as_listed=r["link_organisation"],
                business_types_as_listed="; ".join(sorted(types_of.get(key, set()))),
                shared_premises_number=(
                    f"{num} is printed on {repeats[num]} permits at this address under "
                    f"different holders; an NJ licence number belongs to the premises, so "
                    f"the rows keep a ~n suffix and must not be merged"
                    if repeats[num] > 1 else ""),
                source_pdf=r["pdf_filename"], source_pdf_sha256=r["pdf_sha256"],
                **flags),
        })
        rows.append(row)

    # A location the CRC lists for an organisation but publishes no permit for
    # is still something the CRC publishes. Kept, with no licence number, so a
    # rebuild cannot quietly lose it.
    n = 0
    for l in links:
        key = norm_org(l["organisation"])
        program = "Medical" if "Medicinal" in l["section"] else "Adult Use"
        for town in (t.strip() for t in l["locations"].split(",")):
            if not town or (key, norm_town(town)) in claimed:
                continue
            if any(same_town(town, t) for k, t in claimed if k == key):
                continue
            n += 1
            cats = []
            for t in (x.strip() for x in l["business_types"].split(",")):
                if not t:
                    continue
                if t in NJ_CAT:
                    if NJ_CAT[t] not in cats:
                        cats.append(NJ_CAT[t])
                else:
                    unmapped.append(("NJ business type", t))
            row = dict(blank)
            row.update({
                "licence_id": f"NJ-NOPERMIT-{n:03d}", "state": "NJ", "program": program,
                "category": "; ".join(cats), "licence_type": l["business_types"], "legal_name": l["organisation"],
                "holder_is_individual": "N",
                "status": f"Listed by the CRC under '{NJ_ACTIVE}'",
                "standard_status": "", "expiry_date": "",
                "town": town, "town_as_listed": town,
                "location_basis": "CRC listed location (no permit published for it)",
                "source": f"NJ CRC, Permitted & Licensed Cannabis Businesses — {LOCAL_ID}",
                # NJ's permit PDFs are a file set fetched by scripts/fetch_nj_permits.py, not by
                # the daily fetch, so their read date stays the documented one.
                "source_url": NJ_URL, "data_as_of": TODAY,
                "extra_details": extras(
                    business_types_as_listed=l["business_types"],
                    expiration_year=l["expiration_year"],
                    all_locations=l["locations"],
                    note="the CRC lists this location for the organisation but publishes no "
                         "permit PDF naming it, so there is no licence number, no county and "
                         "no expiry date, and the business types are the ORGANISATION's and "
                         "are NOT confirmed for this location. standard_status is EMPTY, "
                         "which must never be read as Active"),
            })
            rows.append(row)
    if n:
        print(f"  NJ: {n} CRC-listed locations have no permit of their own — kept without a number")
    return rows


# ------------------------------------------------------------------ Maryland
# Maryland DOES publish licence numbers. Part 5 recorded the MCA data dashboard
# as 404 and concluded otherwise, and the dashboard's own XLSX extract then sat
# in data/raw/ unparsed because openpyxl was missing. Its "License Data" sheet
# carries all 214 credentials with the MCA's own numbers, record types and start
# and expiry dates, which the dispensary locator does not.
MD_XLSX = "maryland/mca_dashboard_data_download_sep_2026.xlsx"
MD_SRC = ("MD MCA Data Dashboard, Accessible Data Extract (Sept 2026) — the MCA's own "
          "licence numbers, record types and licence dates")
MD_URL = "https://cannabis.maryland.gov/Pages/Data-Dashboard.aspx"
MD_LOCATOR_SRC = f"MD MCA Dispensary Locator — {LOCAL_ID}"
MD_LOCATOR_URL = "https://cannabis.maryland.gov/Pages/Dispensary-Locator.aspx"

# The MCA's Record Type -> this table's category. An "Ancillary Business
# Registration" for a security guard agency or a waste hauler is a service
# business, and HANDOFF puts those in the business directory rather than the
# licence database, so they are counted and excluded rather than given a
# standard type that does not exist for them. The five that are also an
# Independent Testing Lab do have one.
MD_RECORD_TYPE = {
    "Dispensary Business": ("Retail Store", "Dispensary"),
    "Grower Business": ("Cultivation", "Grower"),
    "Processor Business": ("Manufacturing", "Processor"),
    "Ancillary Business Registration; Independent Testing Lab":
        ("Testing Lab", "Independent Testing Lab"),
}
MD_ANCILLARY = "Ancillary Business Registration"


def md_sheet(name):
    rows = xlsx_reader.read(str(resolve(MD_XLSX, TODAY)[0]), name)
    header = [c.strip() for c in rows[0]]
    out = []
    for r in rows[1:]:
        if not any(c.strip() for c in r):
            continue
        out.append({header[i]: (r[i].strip() if i < len(r) else "")
                    for i in range(len(header))})
    return out


# MCA writes addresses inconsistently: sometimes the town is comma-delimited,
# sometimes it simply follows the street suffix with no punctuation at all
# ("9315 Ocean Highway Delmar, Maryland 21875" vs "213 S Walnut Pl Cumberland").
MD_SUFFIX = (r"(?:Ave|Avenue|Rd|Road|Blvd|Boulevard|Hwy|Highway|Pike|Pkwy|Parkway|St|Street|"
             r"Dr|Drive|Ln|Lane|Ct|Court|Pl|Place|Terrace|Ter|Way|Gateway|Circle|Cir|Crossing|Sq|Square)")
MD_UNIT = r"(?:Suite|Ste|Unit|Apt|Bldg|Floor|Fl)\s+\S+"


def md_town(addr):
    """Return (street, town, zip, unparsed_reason)."""
    m = re.search(r"^(.*?),?\s*Maryland,?\s*(\d{5})?\s*$", addr, re.I)
    if not m:
        return addr, "", "", "no 'Maryland' in the address"
    head, zipc = m.group(1).strip(" ,"), m.group(2) or ""
    parts = [x.strip() for x in head.split(",") if x.strip()]
    if len(parts) > 1:
        # Last comma-separated segment is the town, unless it is a unit number.
        tail = parts[-1]
        if re.fullmatch(MD_UNIT, tail, re.I) and len(parts) > 2:
            tail, parts = parts[-2], parts[:-1]
        return ", ".join(parts[:-1]), tail, zipc, ""
    # No commas: the town starts after the last street suffix or unit number.
    # The suffix must leave something after it — "3518 Conowingo Rd. Street" is
    # in the real town of Street, Maryland, so the trailing "Street" is the town
    # and not the suffix.
    cut = None
    for mm in re.finditer(rf"\b{MD_SUFFIX}\.?\b|{MD_UNIT}", head, re.I):
        if head[mm.end():].strip(" ,."):
            cut = mm.end()
    if cut is None:
        return head, "", zipc, "no comma and no recognisable street suffix"
    return head[:cut].strip(" ,"), head[cut:].strip(" ,."), zipc, ""




def md_name_key(value):
    """Match a dispensary to its locator row by trading name."""
    v = re.sub(r"\(.*?\)", " ", (value or "").upper())
    v = re.sub(r"[^A-Z0-9 ]", " ", v)
    v = re.sub(r"\b(LLC|L L C|INC|LP|LLP|THE|DISPENSARY|CANNABIS|MARYLAND|MD|CO|CORP)\b", " ", v)
    return re.sub(r"\s+", " ", v).strip()


def build_md(blank, unmapped):
    _, md_asof = resolve(MD_XLSX, TODAY)
    licences = md_sheet("License Data")
    addresses = {r["License Number"]: r for r in md_sheet("Dispensaries Address Data")}
    # 197 social-equity records, but only 45 carry a licence number: the other
    # 152 read "Pending" in BOTH the number and the address, and their
    # Region/Jurisdiction is a broad region ("Southern"), not a county. A
    # conditional award is not a licence — CLAUDE.md forbids mixing approved
    # with licensed — so they are counted here and not built as licence rows.
    social, pending = {}, []
    for r in md_sheet("Social Equity License Data"):
        (social.setdefault(r["License Number"], r) if r["License Number"].lower() != "pending"
         else pending.append(r))

    # The locator is the only source for a dispensary's street address.
    locator, unparsed = {}, 0
    for tr in tables("maryland/mca_dispensary_locator_2026-11-12.html")[0][1:]:
        c = cells(tr)
        if len(c) < 3 or not c[0]:
            continue
        # Header reads Dispensary | County | Address; cells are name, address,
        # county. Positions are used, never header names.
        locator.setdefault(md_name_key(c[0]), {"name": c[0], "addr": c[1], "county": c[2]})

    rows, excluded, no_address = [], [], 0
    for r in licences:
        record = r["Record Type"]
        if record == MD_ANCILLARY:
            excluded.append(f'{r["Business Name"]} ({r["Registration Type"]})')
            continue
        mapped = MD_RECORD_TYPE.get(record)
        if not mapped:
            unmapped.append(("MD Record Type", record))
            continue
        category, own_name = mapped
        tier = r["Business Type"] if r["Business Type"] in ("Standard", "Micro") else ""
        # Maryland's "Micro" is the same activity at a smaller cap, not a
        # microbusiness covering several activities — the call already settled
        # for Connecticut's micro-cultivator. It belongs in `tier`.
        dba = r["Location Name (Dispensary Only)"] or r["Trade Name"]
        se = social.get(r["License #"], {})
        extra = addresses.get(r["License #"], {})

        street = town = county = ""
        flags = {}
        if record == "Dispensary Business":
            hit = (locator.get(md_name_key(r["Location Name (Dispensary Only)"]))
                   or locator.get(md_name_key(r["Trade Name"]))
                   or locator.get(md_name_key(r["Business Name"])))
            if hit:
                street, town, zipc, why = md_town(hit["addr"])
                county = "" if hit["county"].upper() == "NA" else hit["county"]
                if why:
                    unparsed += 1
                    flags["address unparsed"] = why
                flags["zip code"] = zipc
            else:
                no_address += 1
                flags["no address"] = ("this licence is in the MCA's licence extract but its "
                                       "trading name does not appear in the MCA's dispensary "
                                       "locator, which is the only source for a street address")
        else:
            no_address += 1
            flags["no address"] = (f"the MCA publishes no premises address for a {own_name.lower()} "
                                   f"in either the licence extract or the locator")

        if se.get("Operational?"):
            # Operating is NOT a licence status. CLAUDE.md: never mix issued,
            # approved, licensed, pending renewal and operating in one count.
            flags["operational per MCA"] = (
                f'{se["Operational?"]} — the MCA\'s own operational flag for this social-equity '
                f'licence. A different measure from being licensed; not read as a status')

        row = dict(blank)
        row.update({
            "licence_id": r["License #"], "state": "MD",
            "program": "Adult Use; Medical",
            "category": category,
            "licence_type": f"{own_name}{' (micro)' if tier == 'Micro' else ''}",
            "tier": tier,
            "legal_name": r["Business Name"], "dba": dba if dba != r["Business Name"] else "",
            "holder_is_individual": "N",
            # The extract carries no status column at all, so standard_status is
            # EMPTY and must never be read as Active.
            "status": "", "standard_status": "",
            "issue_date": r["License Start Date"], "expiry_date": r["License Expiration Date"],
            "street_address": street, "town": town, "town_as_listed": town,
            "county": county,
            "county_source": "MCA Dispensary Locator county column" if county else "",
            "location_basis": "Licensed premises" if street else "",
            "website": extra.get("URL", ""),
            "source": MD_SRC, "source_url": MD_URL, "data_as_of": md_asof,
            "extra_details": extras(
                record_type=record,
                registration_type=r["Registration Type"],
                business_type=r["Business Type"] if r["Business Type"] != "N/A" else "",
                latitude=extra.get("Lat", ""), longitude=extra.get("Long", ""),
                social_equity_round=se.get("Licensing Round", ""),
                social_equity_award=se.get("License Award Category", ""),
                conditional_licence_issued=se.get("Date of Conditional License Issuance", ""),
                address_source="MCA Dispensary Locator (the licence extract publishes none)"
                               if street else "",
                note="the MCA's licence extract publishes no status column, so standard_status is "
                     "EMPTY — it must never be read as Active",
                **flags),
        })
        rows.append(row)

    print(f"  MD: {len(rows)} licences from the MCA extract "
          f"({sum(1 for r in rows if r['street_address'])} with a street address, "
          f"{no_address} without)")
    if unparsed:
        print(f"  MD: {unparsed} locator addresses could not be split into street and town")
    print(f"  MD: {len(excluded)} ancillary business registrations EXCLUDED from the licence "
          f"table — a security guard agency or waste hauler is a service business, which HANDOFF "
          f"puts in the directory")
    print(f"  MD: {len(pending)} conditional social-equity awards NOT built as licences — they "
          f"carry no licence number, no address and a region rather than a county")
    return rows


# ------------------------------------------------------------------ Delaware
DE_SRC = f"DE OMC Dispensaries page — {LOCAL_ID}"
DE_URL = "https://omc.delaware.gov/dispensaries/"


def build_de(blank):
    path, asof = resolve("delaware/omc_dispensaries_2026-11-12.html", TODAY)
    t = path.read_text(errors="replace")
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h\d>", "\n", t, flags=re.I)
    lines = [l.strip() for l in html.unescape(re.sub(r"<[^>]+>", "", t)).splitlines() if l.strip()]
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith("Best Buds"))
        end = next(i for i, l in enumerate(lines) if "Share Your Feedback" in l)
    except StopIteration:
        return []
    rows, brand, n = [], "", 0
    addr_re = re.compile(r"^(.*?),\s*([A-Za-z .'\-]+),\s*DE\s+(\d{5})$")
    for l in lines[start:end]:
        m = addr_re.match(l)
        if m and brand:
            n += 1
            row = dict(blank)
            row.update({
                "licence_id": f"DE-DISP-{n:02d}", "state": "DE",
                "program": "Adult Use; Medical", "category": "Retail Store",
                "licence_type": "Dispensary", "legal_name": brand, "holder_is_individual": "N",
                "status": "", "standard_status": "",
                "street_address": l, "town": m.group(2).strip(), "town_as_listed": m.group(2).strip(),
                "location_basis": "Licensed premises",
                "source": DE_SRC, "source_url": DE_URL, "data_as_of": asof,
                "extra_details": extras(
                    zip_code=m.group(3),
                    note="OMC publishes operator brand and address only — no licence number, type, status, "
                         "county, or medical-vs-adult-use flag. No searchable OMC licensee registry exists. "
                         "Delaware hemp producer names are excluded from the public record by 29 Del.C. 10002(l)."),
            })
            rows.append(row)
        elif not m and len(l) < 70:
            brand = l
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(NE, encoding="utf-8") as f:
        cols = list(next(csv.DictReader(f)).keys())
    if "extra_details" not in cols:
        cols.append("extra_details")
    blank = {c: "" for c in cols}
    unmapped = []

    ny, ny_seen = build_ny(blank, unmapped)
    dc = build_dc(blank, unmapped)
    pa = build_pa(blank)
    nj = build_nj(blank, unmapped)
    md = build_md(blank, unmapped)
    de = build_de(blank)
    rows = ny + dc + pa + nj + md + de
    rows.sort(key=lambda r: (r["state"], r["licence_id"]))

    print("jurisdiction   rows   licence numbers published   counties   statuses")
    for st, rs in (("NY", ny), ("PA", pa), ("NJ", nj), ("DE", de), ("MD", md), ("DC", dc)):
        has_num = sum(1 for r in rs if LOCAL_ID not in r["source"] and "APPLICATION" not in r["extra_details"])
        cty = sum(1 for r in rs if r["county"])
        sts = sum(1 for r in rs if r["standard_status"])
        print(f"  {st:11} {len(rs):>5}   {has_num:>23}   {cty:>8}   {sts:>8}")
    print(f"  {'total':11} {len(rows):>5}")

    print(f"\nNY: {ny_seen['app']} rows are live applications with no licence number "
          f"({ny_seen['app_no_number']} of those have no application number either)")
    print("    standard_status Pending keeps them out of the default Active+Provisional search.")

    if unmapped:
        print("\nUNMAPPED values (left empty, never guessed):")
        for (kind, val), n in collections.Counter(unmapped).most_common():
            print(f"  {n:>4}  {kind}: {val!r}")
    else:
        print("\nNo unmapped licence types or statuses.")

    if args.dry_run:
        print("\n[dry-run] nothing written")
        return
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    print(f"\nwrote {OUT.relative_to(ROOT)} — {len(rows)} rows, {len(cols)} columns")


if __name__ == "__main__":
    main()
