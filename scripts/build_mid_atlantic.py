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
import argparse, collections, csv, html, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "clean" / "mid_atlantic_licences.csv"
NE = ROOT / "data" / "clean" / "new_england_licences.csv"
TODAY = "2026-11-12"

LOCAL_ID = "licence_id assigned locally — the regulator publishes no licence number in this source"


def cells(tr):
    return [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", c))).strip().strip("​")
            for c in re.findall(r"<t[dh].*?</t[dh]>", tr, re.S | re.I)]


def tables(path):
    t = (RAW / path).read_text(errors="replace")
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
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", d)
    if m:
        return f"{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}"
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
             "LICSURR": "Surrendered", "LICSUSPEN": "Suspended", "LICCAN": "Revoked"}
NY_SRC = "NY OCM, Current OCM Licenses (data.ny.gov jskf-tt3q)"
NY_URL = "https://data.ny.gov/d/jskf-tt3q"


def build_ny(blank, unmapped):
    rows = []
    with open(RAW / "new-york/jskf-tt3q_ocm_licences_2026-11-12.csv", encoding="utf-8-sig") as f:
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
            "source_url": NY_URL, "data_as_of": TODAY,
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
        d = json.loads((RAW / "district-of-columbia" / fname).read_text())
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
                "data_as_of": TODAY,
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
PA_SRC = ("PA DOH Medical Marijuana Dispensaries, republished by PASDA (Penn State) dataset 920"
          f" — {LOCAL_ID}")


def build_pa(blank):
    rows = []
    b = (RAW / "pennsylvania/pasda_DOH_MedicalMarijuanaDispensaries202501.csv").read_bytes()
    src = list(csv.DictReader(b.decode("cp1252").splitlines()))
    zips = collections.Counter((r["CITY"].strip(), r["ZIP_CODE"].strip()) for r in src)
    for r in src:
        listed = r["CITY"].strip()
        town = PA_TOWN_FIX.get(listed, listed)
        # The audit flagged one King of Prussia row carrying ZIP 19706 while its
        # siblings carry 19406. Flag it; do not silently rewrite a ZIP.
        zip_note = ""
        same_town = [z for (c, z) in zips if c == listed]
        if len(set(same_town)) > 1:
            zip_note = (f"ZIP {r['ZIP_CODE'].strip()} differs from other {listed} rows "
                        f"({', '.join(sorted(set(same_town) - {r['ZIP_CODE'].strip()}))}) — verify")
        row = dict(blank)
        row.update({
            "licence_id": f"PA-DISP-{int(r['OBJECTID']):04d}", "state": "PA",
            "program": "Medical", "category": "Retail Store",
            "licence_type": "Medical Marijuana Dispensary",
            "legal_name": r["FACILITY_N"].strip(), "holder_is_individual": "N",
            # DOH publishes no status in this layer. An empty standard_status is
            # the honest answer; it must not be read as Active.
            "status": "", "standard_status": "",
            "first_issue_date": mdy(r["OPENED_ON"]),
            "street_address": ", ".join(x for x in (r["STREET"].strip(), town, "PA",
                                                    r["ZIP_CODE"].strip()) if x),
            "town": town, "town_as_listed": listed,
            "location_basis": "Licensed premises (rooftop geocode)",
            "website": r["FACILITY_U"].strip(), "contact_phone": r["TELEPHONE_"].strip(),
            "source": PA_SRC, "source_url": "https://www.pasda.psu.edu/uci/DataSummary.aspx?dataset=920",
            "data_as_of": "2025-01-01",
            "extra_details": extras(
                product_available=r["PRODUCT_AV"].strip().capitalize(),
                opened_on=mdy(r["OPENED_ON"]), latitude=r["LATITUDE"].strip(),
                longitude=r["LONGITUDE"].strip(), geocoding_certainty=r["GEOCODING_"].strip(),
                town_typo="listed as 'Bulter'; facility name confirms Butler" if listed in PA_TOWN_FIX else "",
                zip_conflict=zip_note,
                note="DOH publishes no permit number, status or county in this layer. "
                     "Vintage Jan 2025 — do not compare its 181 locations with MMAB's 196 (1 June 2026)."),
        })
        rows.append(row)
    return rows


# ----------------------------------------------------------------- New Jersey
NJ_CAT = {"Retailer": "Retail Store", "Dispensing": "Retail Store",
          "Manufacturer": "Manufacturing", "Manufacturing": "Manufacturing",
          "Cultivator": "Cultivation", "Cultivating": "Cultivation",
          "Delivery": "Delivery", "Wholesaler": "Transport & Distribution",
          "Distributor": "Transport & Distribution", "Consumption Area": "Consumption Lounge"}
NJ_SRC = f"NJ CRC, Permitted & Licensed Cannabis Businesses — {LOCAL_ID}"
NJ_URL = "https://www.nj.gov/cannabis/businesses/permitted/"


def build_nj(blank, unmapped):
    rows, n = [], 0
    tabs = tables("new-jersey/crc_permitted_businesses_2026-11-12.html")
    for tb in tabs:
        header = cells(tb[0])[0] if tb else ""
        program = "Medical" if "Medicinal" in header else "Adult Use"
        for tr in tb[1:]:
            c = cells(tr)
            if len(c) < 4 or not c[0]:
                continue
            org, types_s, locs_s, year = c[0], c[1], c[2], c[3].strip()
            types = [t.strip() for t in re.split(r",\s*", types_s) if t.strip()]
            cats = []
            for t in types:
                if t in NJ_CAT:
                    if NJ_CAT[t] not in cats:
                        cats.append(NJ_CAT[t])
                else:
                    unmapped.append(("NJ business type", t))
            if year.upper() == "INACTIVE":
                std, expiry = "Expired", ""
            elif year.isdigit():
                # CRC publishes a year, not a date, so a 2026 expiry cannot be
                # resolved against today. Treated as current, and said so.
                std, expiry = ("Expired" if int(year) < 2026 else "Active"), year
            else:
                std, expiry = "", ""
            locs = [l.strip() for l in re.split(r",\s*", locs_s) if l.strip()] or [""]
            for loc in locs:
                n += 1
                row = dict(blank)
                row.update({
                    "licence_id": f"NJ-{'MED' if program == 'Medical' else 'AU'}-{n:04d}",
                    "state": "NJ", "program": program, "category": "; ".join(cats),
                    "licence_type": types_s, "legal_name": org, "holder_is_individual": "N",
                    "status": f"Permitted/licensed; expiration year {year}" if year else "Permitted/licensed",
                    "standard_status": std, "expiry_date": expiry,
                    "town": loc, "town_as_listed": loc,
                    "location_basis": "CRC listed location (CRC gives business types per organisation, not per location)",
                    "group_id": f"NJ-G{n:04d}" if len(locs) > 1 else "",
                    "linked_group": org if len(locs) > 1 else "",
                    "licences_in_group": str(len(locs)) if len(locs) > 1 else "",
                    "programs_in_group": program if len(locs) > 1 else "",
                    "source": NJ_SRC, "source_url": NJ_URL, "data_as_of": TODAY,
                    "extra_details": extras(
                        all_locations="; ".join(locs) if len(locs) > 1 else "",
                        business_types_as_listed=types_s, expiration_year=year,
                        note="CRC publishes organisations, not licences: no licence number, no per-location "
                             "activity, and only a year for expiry. Business types are the organisation's and "
                             "are NOT confirmed for this location."),
                })
                rows.append(row)
    return rows


# ------------------------------------------------------------------ Maryland
MD_SRC = f"MD MCA Dispensary Locator — {LOCAL_ID}"
MD_URL = "https://cannabis.maryland.gov/Pages/Dispensary-Locator.aspx"


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


MD_SRC = f"MD MCA Dispensary Locator — {LOCAL_ID}"
MD_URL = "https://cannabis.maryland.gov/Pages/Dispensary-Locator.aspx"


def build_md(blank):
    rows, unparsed = [], 0
    tb = tables("maryland/mca_dispensary_locator_2026-11-12.html")[0]
    for i, tr in enumerate(tb[1:], 1):
        c = cells(tr)
        if len(c) < 3 or not c[0]:
            continue
        # The header reads Dispensary | County | Address but the cells are
        # Dispensary | Address | County. Positions are used, never header names.
        name, addr, county = c[0], c[1], c[2]
        delivery = "delivery only" in name.lower() or county.upper() == "NA"
        if delivery:
            # Address cell holds a service region ("Central*"), not a place, and
            # the county cell holds "NA". Neither is a town or a county.
            street, town, zipc, why = "", "", "", ""
            region = addr
            county = ""
        else:
            region = ""
            street, town, zipc, why = md_town(addr)
            if why:
                unparsed += 1
        row = dict(blank)
        row.update({
            "licence_id": f"MD-DISP-{i:04d}", "state": "MD",
            "program": "Adult Use; Medical",
            "category": "Delivery" if delivery else "Retail Store",
            "licence_type": "Dispensary (delivery only)" if delivery else "Dispensary",
            "legal_name": name, "holder_is_individual": "N",
            "status": "", "standard_status": "",
            "street_address": "" if delivery else addr,
            "town": town, "town_as_listed": town,
            "county": county,
            "county_source": "MCA Dispensary Locator county column" if county else "",
            "location_basis": "Delivery service area (no storefront)" if delivery else "Licensed premises",
            "source": MD_SRC, "source_url": MD_URL, "data_as_of": TODAY,
            "extra_details": extras(
                zip_code=zipc, street=street, service_region=region,
                address_unparsed=why,
                note="MCA publishes no licence number or status in the locator, and the table's header "
                     "columns are mislabelled relative to its cells (cells are name, address, county). "
                     "Maryland dispensaries serve both medical patients and adult-use customers."),
        })
        rows.append(row)
    if unparsed:
        print(f"  MD: {unparsed} addresses could not be split into street and town — town left empty")
    return rows


# ------------------------------------------------------------------ Delaware
DE_SRC = f"DE OMC Dispensaries page — {LOCAL_ID}"
DE_URL = "https://omc.delaware.gov/dispensaries/"


def build_de(blank):
    t = (RAW / "delaware/omc_dispensaries_2026-11-12.html").read_text(errors="replace")
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
                "source": DE_SRC, "source_url": DE_URL, "data_as_of": TODAY,
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
    md = build_md(blank)
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
