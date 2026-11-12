#!/usr/bin/env python3
"""Build data/clean/regions_3_to_9_licences.csv from data/raw/, one spec per state.

Regions 3-9 are 39 jurisdictions and almost none of them publish data the same
way, so each state is a declarative spec — source file, column map, vocabulary
maps — rather than its own parser. Adding a state means adding a spec.

Two rules run through every spec:
  * A value that does not map is left empty and reported, never guessed.
  * HANDOFF defines 7 standard statuses. Several states use words that do not
    fit any of them (California's "Canceled" and "Limited Operations", Oregon's
    "Inactive"). Those get the nearest standard status AND an explicit
    `standard_status_approximate=yes` in extra_details, so an approximation can
    never be mistaken for the regulator's own word.

Usage: python3 scripts/build_states.py [--state CA] [--dry-run]
"""
import argparse, collections, csv, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "clean" / "regions_3_to_9_licences.csv"
NE = ROOT / "data" / "clean" / "new_england_licences.csv"
TODAY = "2026-11-12"
sys.path.insert(0, str(ROOT / "scripts"))

STANDARD = {"Active", "Provisional", "Pending", "Suspended", "Expired", "Surrendered", "Revoked"}
LOCAL_ID = "licence_id assigned locally — the regulator publishes no licence number in this source"


def iso(d):
    d = (d or "").strip()
    if not d or d == "Data Not Available":
        return ""
    if "T" in d:
        d = d.split("T")[0]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
        return d
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", d)
    if m:
        return f"{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}"
    return d


def clean(s):
    """Collapse the double spaces several regulators ship inside values."""
    return re.sub(r"\s+", " ", (s or "").strip())


def title(s):
    s = clean(s)
    return s.title() if s.isupper() else s


NA_TOKENS = {"data not available", "not published", "na", "n/a", "none", "unknown", "not available", "-"}


def na(s):
    """Blank the placeholder strings regulators ship instead of empty cells.
    Writing "Data Not Available" into a town column would publish it as a place."""
    s = clean(s)
    return "" if s.lower() in NA_TOKENS else s


SUFFIX = (r"(?:Ave|Avenue|Rd|Road|Blvd|Boulevard|Hwy|Highway|Pike|Pkwy|Parkway|St|Street|Dr|Drive|"
          r"Ln|Lane|Ct|Court|Pl|Place|Terrace|Ter|Way|Cir|Circle|Loop|Trail|Trl|Sq|Square|Row|Run|Crossing)")
UNIT = r"(?:Suite|Ste|Unit|Apt|Bldg|Bldng|Floor|Fl|Rm|#)\s*\S+"


def split_address(addr, state_abbr):
    """Split '<street> <TOWN> <ST> <ZIP>' into (street, town). Returns town ''
    when it cannot be determined — regulators write these inconsistently and a
    wrong town is worse than a blank one."""
    a = clean(addr)
    # "<street> <Town>, ST <zip>" — comma after the town rather than before it
    m2 = re.match(rf"^(.*?)\s+([A-Za-z][A-Za-z .'\-]*?),\s*{state_abbr}\s+[\d\-]+$", a)
    if m2 and "," not in m2.group(1):
        head, tail = m2.group(1).strip(), m2.group(2).strip()
        cut = None
        for mm in re.finditer(rf"\b{SUFFIX}\.?\b|{UNIT}", head, re.I):
            if head[mm.end():].strip(" ,."):
                cut = mm.end()
        if cut is not None:
            return head[:cut].strip(" ,"), (head[cut:].strip(" ,.") + " " + tail).strip()
        return head, tail
    m = re.match(rf"^(.*?),?\s*([A-Za-z .'\-]+?)\s+{state_abbr}\s+[\d\-]+$", a)
    if not m:
        return a, ""
    head, tail = m.group(1).strip(" ,"), m.group(2).strip()
    if "," in head:
        parts = [x.strip() for x in head.split(",") if x.strip()]
        return ", ".join(parts), tail
    # No comma: the town is the run of words after the last street suffix or unit.
    cut = None
    for mm in re.finditer(rf"\b{SUFFIX}\.?\b|{UNIT}", head, re.I):
        if head[mm.end():].strip(" ,."):
            cut = mm.end()
    if cut is None:
        return head, tail
    return head[:cut].strip(" ,"), (head[cut:].strip(" ,.") + " " + tail).strip()


# ===================================================================== CALIFORNIA
CA_CAT = [
    (r"^Cultivation -\s*Nursery", "Nursery"),
    (r"^Cultivation -\s*Processor", "Manufacturing"),
    (r"^Cultivation", "Cultivation"),
    (r"^Commercial -\s*Retailer - Non-Storefront", "Delivery"),
    (r"^Commercial -\s*Retailer", "Retail Store"),
    (r"^Commercial -\s*Distributor", "Transport & Distribution"),
    (r"^Commercial -\s*Microbusiness", "Microbusiness"),
    (r"^Commercial -\s*Testing Laboratory", "Testing Lab"),
    (r"^Commercial -\s*Event Organizer", "Event Organizer"),
    (r"^Manufacturer", "Manufacturing"),
]
CA_PROGRAM = {"Adult-Use": "Adult Use", "Medicinal": "Medical",
              "Adult-Use and Medicinal": "Adult Use; Medical", "Data Not Available": ""}
# (status, nearest standard, is_approximate)
CA_STATUS = {"Active": ("Active", False), "Expired": ("Expired", False),
             "Surrendered": ("Surrendered", False), "Revoked": ("Revoked", False),
             "Suspended": ("Suspended", False),
             "Canceled": ("Surrendered", True), "Limited Operations": ("Active", True)}


def build_ca(blank, warn):
    rows = []
    with open(RAW / "california/dcc_unified_licence_search_2026-11-12.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            ltype = clean(r["licenseType"])
            cat = next((c for pat, c in CA_CAT if re.match(pat, ltype)), "")
            if not cat:
                warn.append(("CA licenseType", ltype))
            if cat == "Event Organizer":
                warn.append(("CA category outside HANDOFF's 14 standard types", "Event Organizer"))
            std, approx = CA_STATUS.get(clean(r["licenseStatus"]), ("", True))
            if not std:
                warn.append(("CA licenseStatus", clean(r["licenseStatus"])))
            term = clean(r["licenseTerm"])
            # A provisional licence is an active licence on a provisional term.
            if std == "Active" and term == "Provisional":
                std, approx = "Provisional", False
            row = dict(blank)
            row.update({
                "licence_id": clean(r["licenseNumber"]), "state": "CA",
                "program": CA_PROGRAM.get(clean(r["licenseDesignation"]), ""),
                "category": cat, "licence_type": ltype, "tier": term,
                "legal_name": na(r["businessLegalName"]), "dba": na(r["businessDbaName"]),
                "holder_is_individual": "Y" if clean(r["businessStructure"]) in
                                        ("Sole Proprietor", "Individual") else "N",
                "status": "; ".join(x for x in (clean(r["licenseStatus"]), term) if x),
                "standard_status": std,
                "issue_date": iso(r["issueDate"]), "expiry_date": iso(r["expirationDate"]),
                "street_address": ", ".join(x for x in (na(r["premiseStreetAddress"]),
                                                        title(r["premiseCity"]), "CA",
                                                        na(r["premiseZipCode"])) if x),
                "town": title(na(r["premiseCity"])), "town_as_listed": na(r["premiseCity"]),
                "county": title(na(r["premiseCounty"])),
                "county_source": "DCC premiseCounty field" if na(r["premiseCounty"]) else "",
                "location_basis": "Licensed premises",
                "contact_email": na(r["businessEmail"]), "contact_phone": na(r["businessPhone"]),
                "contact_is_law_firm": "N",
                "owners": na(r["businessOwnerName"]),
                "owner_count": str(len([x for x in na(r["businessOwnerName"]).split(",") if x.strip()])),
                "source": "CA DCC Cannabis Unified License Search (the API behind search.cannabis.ca.gov)",
                "source_url": "https://search.cannabis.ca.gov/", "data_as_of": iso(r["dataRefreshedDate"]) or TODAY,
                "extra_details": "; ".join(x for x in (
                    f"licensing authority={clean(r['licensingAuthority'])}" if clean(r["licensingAuthority"]) else "",
                    f"local jurisdiction={clean(r['localJurisdictionName'])} ({clean(r['localJurisdictionType'])})"
                    if clean(r["localJurisdictionName"]) else "",
                    f"latitude={clean(r['premiseLatitude'])}" if na(r["premiseLatitude"]) else "",
                    f"longitude={clean(r['premiseLongitude'])}" if na(r["premiseLongitude"]) else "",
                    f"business structure={clean(r['businessStructure'])}" if na(r["businessStructure"]) else "",
                    "business name not published=the DCC returns 'Data Not Available' for both the legal "
                    "and DBA name on this licence" if not (na(r["businessLegalName"]) or na(r["businessDbaName"])) else "",
                    "premises address not published=the DCC withholds it for this licence"
                    if not na(r["premiseStreetAddress"]) else "",
                    "standard_status_approximate=yes — the DCC's own word is in `status`; it has no "
                    "exact match among HANDOFF's 7 standard statuses" if approx else "") if x),
            })
            rows.append(row)
    return rows


# ========================================================================= OREGON
OR_CAT = {"RECREATIONAL PRODUCER": "Cultivation", "RECREATIONAL RETAILER": "Retail Store",
          "RECREATIONAL PROCESSOR": "Manufacturing", "RECREATIONAL WHOLESALER": "Transport & Distribution",
          "LABORATORY": "Testing Lab", "SAMPLING LABORATORY": "Testing Lab",
          "HEMP HANDLER CERTIFICATE": "Hemp Processor", "HEMP GROWER CERTIFICATE": "Hemp Grower",
          "RESEARCH CERTIFICATE": "Research", "MARIJUANA PROMOTIONAL EVENT": "Event Organizer"}
OR_STATUS = {"ACTIVE": ("Active", False), "EXPIRED": ("Expired", False),
             "CANCELLED": ("Surrendered", True), "REVOKED": ("Revoked", False),
             "SUSPENDED": ("Suspended", False), "INACTIVE": ("Expired", True),
             "NOT APPROVED": ("Pending", True)}


def build_or(blank, warn):
    rows = []
    with open(RAW / "oregon/olcc_cannabis_licences_q32u-cmam_2026-11-12.csv", encoding="utf-8-sig") as f:
        src = list(csv.DictReader(f))
    # OLCC publishes a row per licence TERM, so a renewed licence appears more
    # than once. Keep the latest term as the licence's record and carry the
    # earliest effective date as first_issue_date rather than dropping history.
    by_num = collections.defaultdict(list)
    for r in src:
        by_num[clean(r["License Number"])].append(r)
    collapsed = []
    for num, group in by_num.items():
        group.sort(key=lambda x: iso(x["Effective Date"]))
        latest = dict(group[-1])
        latest["_first_effective"] = iso(group[0]["Effective Date"])
        latest["_terms"] = str(len(group))
        collapsed.append(latest)
    for r in collapsed:
            ltype = clean(r["License Type"])
            cat = OR_CAT.get(ltype, "")
            if not cat:
                warn.append(("OR License Type", ltype))
            std, approx = OR_STATUS.get(clean(r["License Status"]), ("", True))
            if not std:
                warn.append(("OR License Status", clean(r["License Status"])))
            program = "Hemp" if "HEMP" in ltype else "Adult Use"
            addr = clean(r["Physical Address"])
            # OLCC withholds the premises address of producers, processors and
            # wholesalers; only retailers and labs are public. That is a
            # statutory withholding, not a missing value.
            exempt = "Exempt from Public Disclosure" in addr
            if exempt:
                street, town = "", ""
            else:
                street, town = split_address(addr, "OR")
                town = title(town)
                if not town and addr:
                    warn.append(("OR address not parsed", addr[:40]))
            row = dict(blank)
            row.update({
                "licence_id": clean(r["License Number"]), "state": "OR",
                "program": program, "category": cat, "licence_type": title(ltype),
                "tier": clean(r["Tier"]), "legal_name": clean(r["Business Licensee"]) or clean(r["Business Name"]),
                "dba": clean(r["Business Name"]), "holder_is_individual": "N",
                "status": "; ".join(x for x in (title(r["License Status"]),
                                                "closed" if clean(r["License Closed?"]) == "Yes" else "") if x),
                "standard_status": std,
                "issue_date": iso(r["Effective Date"]), "expiry_date": iso(r["Expiration Date"]),
                "first_issue_date": r.get("_first_effective", ""),
                "street_address": "" if exempt else addr, "town": town, "town_as_listed": town,
                "county": clean(r["County"]),
                "county_source": "OLCC County field" if clean(r["County"]) else "",
                "location_basis": "Address exempt from public disclosure (OLCC)" if exempt else "Licensed premises",
                "source": "OR OLCC Cannabis Business Licenses & Endorsements (data.oregon.gov q32u-cmam)",
                "source_url": "https://data.oregon.gov/d/q32u-cmam", "data_as_of": "2026-10-05",
                "extra_details": "; ".join(x for x in (
                    f"canopy type={clean(r['Canopy Type'])}" if clean(r["Canopy Type"]) else "",
                    f"endorsements={clean(r['License Endorsements'])}" if clean(r["License Endorsements"]) else "",
                    f"sos registration={clean(r['SOS Registration Number'])}" if clean(r["SOS Registration Number"]) else "",
                    f"inactive date={iso(r['Inactive Date'])}" if clean(r["Inactive Date"]) else "",
                    f"licence terms published={r.get('_terms')} (OLCC lists one row per term; the latest "
                    f"is used here)" if r.get("_terms", "1") != "1" else "",
                    "address withheld=OLCC marks this premises 'Exempt from Public Disclosure'; "
                    "only retailer and laboratory addresses are public" if exempt else "",
                    "standard_status_approximate=yes — OLCC's own word is in `status`; it has no exact "
                    "match among HANDOFF's 7 standard statuses" if approx else "") if x),
            })
            rows.append(row)
    return rows


# ===================================================================== WASHINGTON
WA_STATUS = {"ACTIVE (ISSUED)": ("Active", False), "ACTIVE TITLE CERTIFICATE": ("Active", True),
             "CLOSED (PERMANENT)": ("Surrendered", True), "CLOSED (TEMPORARY)": ("Suspended", True),
             "EXPIRED": ("Expired", False), "ON HOLD": ("Suspended", True),
             "FORMER TITLE CERTIFICATE": ("Expired", True)}


def build_wa(blank, warn):
    from xlsx_reader import read
    raw = read(RAW / "washington/lcb_cannabis_applicants_2026-11-10.xlsx")
    hdr = raw[0]
    recs = [dict(zip(hdr, list(x) + [""] * (len(hdr) - len(x)))) for x in raw[1:]]
    # An LCB licence number belongs to the premises and survives an ownership
    # transfer, so one number can appear twice — once for the closed holder and
    # once for the current one. UBI (the business entity) is what distinguishes them.
    repeats = collections.Counter(clean(x.get("License")) for x in recs)

    def wa_key(x):
        """One licence can carry two privileges (a retailer and a former title
        certificate), so the privilege is part of the identity."""
        return (clean(x.get("License")), clean(x.get("UBI")),
                clean(x.get("Priv Desc")), clean(x.get("Privilege Status")))

    keys = collections.Counter(wa_key(x) for x in recs)
    seen = collections.Counter()
    rows = []
    for r in recs:
        priv = clean(r.get("Priv Desc"))
        cat = "Retail Store" if "RETAILER" in priv else "Retail Store" if "RETAIL" in priv else ""
        if not cat:
            warn.append(("WA Priv Desc", priv))
        std, approx = WA_STATUS.get(clean(r.get("Privilege Status")), ("", True))
        if not std:
            warn.append(("WA Privilege Status", clean(r.get("Privilege Status"))))
        lic = clean(r.get("License"))
        lid = f'{lic}#{clean(r.get("UBI"))}' if repeats[lic] > 1 else lic
        if repeats[lic] > 1:
            lid += "#" + re.sub(r"[^A-Za-z0-9]+", "-", clean(r.get("Priv Desc")) or "x").lower()
        k = wa_key(r)
        seen[k] += 1
        near_dup = ""
        if keys[k] > 1:
            lid = f"{lid}~{seen[k]}"
            near_dup = ("source near-duplicate=the LCB file holds more than one row for this licence, "
                        "UBI and privilege, differing only in ZIP+4 or phone; the id carries a local suffix")
        addr_raw = clean(r.get("Street Address"))
        placeholder_addr = addr_raw.upper() in ("RETAIL TITLE CERTIFICATE", "TITLE CERTIFICATE")
        row = dict(blank)
        row.update({
            "licence_id": lid,
            "state": "WA", "program": "Adult Use",
            "category": cat, "licence_type": title(priv),
            "legal_name": clean(r.get("Tradename")), "holder_is_individual": "N",
            "status": title(r.get("Privilege Status")), "standard_status": std,
            "street_address": "" if placeholder_addr else ", ".join(
                x for x in (addr_raw, clean(r.get("Suite Rm")), title(r.get("City")), "WA",
                            clean(r.get("Zip Code"))) if x),
            "town": title(r.get("City")), "town_as_listed": clean(r.get("City")),
            "county": title(r.get("county")),
            "county_source": "LCB county field" if clean(r.get("county")) else "",
            "location_basis": "Title certificate — no premises address published"
                              if placeholder_addr else "Licensed premises",
            "contact_phone": clean(r.get("Day Phone")), "contact_is_law_firm": "N",
            "source": "WA LCB Frequently Requested Lists, Cannabis License Applicants (10 Nov 2026)",
            "source_url": "https://lcb.wa.gov/records/frequently-requested-lists",
            "data_as_of": "2026-11-10",
            "extra_details": "; ".join(x for x in (
                f"ubi={clean(r.get('UBI'))}" if clean(r.get("UBI")) else "",
                near_dup,
                f"licence number shared={clean(r.get('License'))} is held by more than one UBI in this "
                "file — the number belongs to the premises and survives an ownership transfer"
                if repeats[clean(r.get("License"))] > 1 else "",
                "scope=RETAIL ONLY — this LCB file covers cannabis retailers and retail certificate "
                "holders; producer, processor and transport licences are NOT in it",
                "standard_status_approximate=yes — the LCB's own word is in `status`; it has no exact "
                "match among HANDOFF's 7 standard statuses" if approx else "") if x),
        })
        rows.append(row)
    return rows


# ========================================================================= NEVADA
NV_CAT = {"Retail Dispensary": "Retail Store", "Retail Cultivation": "Cultivation",
          "Retail Production": "Manufacturing", "Retail Distributor": "Transport & Distribution",
          "Retail Laboratory": "Testing Lab", "Retail Lounge": "Consumption Lounge",
          "Medical Dispensary": "Medical Dispensary"}
# The CCB's own key reads: Active = "Licensed", Non-Operational = "Licensed - No
# Operating". Both are current licences, so both are Active here and whether the
# business trades is kept separately, exactly as HANDOFF separates the two.
NV_STATUS = {"Active": ("Active", False), "Non-Operational": ("Active", False),
             "Suspended": ("Suspended", False)}


def build_nv(blank, warn):
    from xlsx_reader import read
    raw = read(RAW / "nevada/ccb_cannabis_establishment_list_2026-10-02.xlsx")
    hdr = raw[1]                      # row 0 is the report title
    rows = []
    for rec in raw[2:]:
        r = dict(zip(hdr, list(rec) + [""] * (len(hdr) - len(rec))))
        if not clean(r.get("LicenseNumber")):
            continue
        ltype = clean(r.get("LicenseType"))
        cat = NV_CAT.get(ltype, "")
        if not cat:
            warn.append(("NV LicenseType", ltype))
        std, approx = NV_STATUS.get(clean(r.get("LicenseStatus")), ("", True))
        if not std:
            warn.append(("NV LicenseStatus", clean(r.get("LicenseStatus"))))
        row = dict(blank)
        row.update({
            "licence_id": clean(r.get("LicenseNumber")), "state": "NV",
            "program": "Medical" if ltype.startswith("Medical") else "Adult Use",
            "category": cat, "licence_type": ltype,
            "legal_name": title(r.get("LicenseName")), "holder_is_individual": "N",
            "status": clean(r.get("LicenseStatus")), "standard_status": std,
            # County case is inconsistent in the source ('CLARK' and 'Clark' both appear).
            "county": title(r.get("County")),
            "county_source": "CCB County field" if clean(r.get("County")) else "",
            "location_basis": "No premises address published",
            "source": "NV CCB Cannabis Establishment List (2 Oct 2026)",
            "source_url": "https://ccb.nv.gov/", "data_as_of": "2026-10-02",
            "extra_details": "; ".join(x for x in (
                f"ce id={clean(r.get('CE ID'))}" if clean(r.get("CE ID")) else "",
                "operating=no — the CCB lists this licence as Non-Operational ('Licensed - No Operating')"
                if clean(r.get("LicenseStatus")) == "Non-Operational" else "",
                "scope=the CCB list carries no premises address, so there is no town or street for these rows",
                "note=Carson City is a consolidated city-county") if x),
        })
        rows.append(row)
    return rows


# ========================================================================== TEXAS
TX_FILES = [("texas/dshs_consumable_hemp_product_licensees_2026-11-02.xlsx", "Hemp Processor"),
            ("texas/dshs_retail_hemp_registrations_2026-11-02.xlsx", "Hemp Retail")]


def build_tx(blank, warn):
    from xlsx_reader import read
    rows, seen = [], collections.Counter()
    for rel, cat in TX_FILES:
        raw = read(RAW / rel)
        hdr = raw[0]
        for rec in raw[1:]:
            r = dict(zip(hdr, list(rec) + [""] * (len(hdr) - len(rec))))
            num = clean(r.get("LICENSE_NUMBER"))
            if not num:
                continue
            code = clean(r.get("LICENSE_TYPE_CDE"))
            status = clean(r.get("LIC_STATUS"))
            std = "Active" if status == "Current" else ""
            if not std:
                warn.append(("TX LIC_STATUS", status))
            # One registration covers many stores — a chain registers once and
            # lists each outlet — so the licence number alone is not unique.
            key = f"TX-{code}-{num}"
            seen[key] += 1
            lid = key if seen[key] == 1 else f"{key}#{seen[key]}"
            row = dict(blank)
            row.update({
                "licence_id": lid, "state": "TX", "program": "Hemp", "category": cat,
                "licence_type": clean(r.get("LICENSE_TYPE")),
                "legal_name": title(r.get("PRIMARY_NAME")), "dba": title(r.get("ADDR_NAME")),
                "holder_is_individual": "N",
                "status": status, "standard_status": std,
                "expiry_date": iso(r.get("EXPIRES_DATE")),
                "street_address": ", ".join(x for x in (clean(r.get("ADDRESS")), title(r.get("CITY")),
                                                        "TX", clean(r.get("ZIP"))) if x),
                "town": title(r.get("CITY")), "town_as_listed": clean(r.get("CITY")),
                "county": title(r.get("COUNTY_NAME")),
                "county_source": "DSHS COUNTY_NAME field" if clean(r.get("COUNTY_NAME")) else "",
                "location_basis": "Licensed premises",
                "contact_phone": clean(r.get("PHNE_NBR")), "contact_is_law_firm": "N",
                "source": "TX DSHS Consumable Hemp Product Program licence lists (2 Nov 2026)",
                "source_url": "https://www.dshs.texas.gov/consumable-hemp-program",
                "data_as_of": "2026-11-02",
                "extra_details": "; ".join(x for x in (
                    f"licence type code={code}" if code else "",
                    f"mailing town={title(r.get('MAIL_CITY'))}" if clean(r.get("MAIL_CITY")) else "",
                    "note=one registration can cover many outlets, so this row is one outlet of "
                    f"licence {num}; Texas licenses no adult-use or broad medical cannabis, so its "
                    "licence universe is hemp plus the Compassionate Use Programme") if x),
            })
            rows.append(row)
    return rows


# ======================================================================== ALABAMA
def build_al(blank, warn):
    from xlsx_reader import read
    raw = read(RAW / "alabama/alabc_active_consumable_hemp_licences.xlsx")
    hdr_i = next(i for i, r in enumerate(raw) if r and clean(r[0]) == "License Number")
    hdr = raw[hdr_i]
    rows = []
    for rec in raw[hdr_i + 1:]:
        r = dict(zip(hdr, list(rec) + [""] * (len(hdr) - len(rec))))
        num = clean(r.get("License Number"))
        if not num:
            continue
        addr = clean(r.get("Physical Address"))
        parts = [x.strip() for x in addr.split(",") if x.strip()]
        town = title(parts[-1]) if len(parts) > 1 else ""
        row = dict(blank)
        row.update({
            "licence_id": num, "state": "AL", "program": "Hemp", "category": "Hemp Retail",
            "licence_type": f"Consumable Hemp Licence (type {clean(r.get('Lic Type'))})",
            "legal_name": title(r.get("Owner Name")), "dba": title(r.get("Trade Name")),
            "holder_is_individual": "N",
            # The file is titled "Active Consumable Hemp Licenses" — every row in
            # it is active by construction, which is why no status column exists.
            "status": "Active (the file lists active licences only)", "standard_status": "Active",
            "street_address": addr, "town": town, "town_as_listed": town,
            "location_basis": "Licensed premises",
            "source": "AL ABC Board Active Consumable Hemp Licensee Listing (as of 8 Oct 2026)",
            "source_url": "https://alabcboard.gov/", "data_as_of": "2026-10-08",
            "extra_details": "note=Alabama's medical cannabis licences (AMCC) are litigation-delayed "
                             "and are NOT in this file; this is the consumable hemp programme only",
        })
        rows.append(row)
    return rows


# ======================================================================= COLORADO
CO_CAT = [(r"Store", "Retail Store"), (r"Cultivation Facility|Marijuana Cultivation", "Cultivation"),
          (r"Products Mfg", "Manufacturing"), (r"Delivery", "Delivery"),
          (r"Transporter", "Transport & Distribution"), (r"Hospitality", "Consumption Lounge"),
          (r"R&D Cultivation", "Research"), (r"Operator", "Operator"),
          (r"Optional Premises", "Cultivation")]


def build_co(blank, warn):
    import glob
    rows = []
    for path in sorted(glob.glob(str(RAW / "colorado/*.csv"))):
        with open(path, encoding="utf-8-sig") as f:
            recs = list(csv.DictReader(f))
        if not recs:
            continue
        cols = set(recs[0])
        testing = "Facility Type" not in cols          # the labs sheet has its own layout
        for r in recs:
            num = clean(r.get("License Number"))
            if not num:
                continue                               # the labs sheet carries a second header row
            if testing:
                ftype, cat = "Marijuana Testing Facility", "Testing Lab"
                name = clean(r.get("Licensee Name"))
                street = clean(r.get("Address"))
            else:
                ftype = clean(r.get("Facility Type"))
                cat = next((c for pat, c in CO_CAT if re.search(pat, ftype, re.I)), "")
                if not cat:
                    warn.append(("CO Facility Type", ftype))
                if cat == "Operator":
                    warn.append(("CO category outside HANDOFF's 14 standard types", "Operator"))
                name = clean(r.get("Facility Name"))
                street = clean(r.get("Street"))
            program = "Medical" if re.search(r"Medical|MMJ", ftype, re.I) else "Adult Use"
            town = title(r.get("City"))
            row = dict(blank)
            row.update({
                "licence_id": num, "state": "CO", "program": program, "category": cat,
                "licence_type": ftype, "legal_name": name, "dba": clean(r.get("DBA")),
                "holder_is_individual": "N",
                # These sheets are lists of CURRENTLY licensed facilities; the MED
                # publishes no status column, so every row in them is licensed.
                "status": "Licensed (the MED publishes current licensees only; no status column)",
                "standard_status": "Active",
                "expiry_date": iso(r.get("Expiration Date")),
                "street_address": ", ".join(x for x in (street, town, "CO", clean(r.get("ZIP Code"))) if x),
                "town": town, "town_as_listed": clean(r.get("City")),
                "location_basis": "Licensed premises",
                "source": "CO MED List of Licensed Facilities (public Google Sheets linked from med.colorado.gov)",
                "source_url": "https://med.colorado.gov/licensee-information-and-lookup-tool/licensed-facilities",
                "data_as_of": TODAY,
                "extra_details": "; ".join(x for x in (
                    f"elemental impurities certified until={clean(r.get('Elemental Impurities'))}"
                    if testing and clean(r.get("Elemental Impurities")) else "",
                    "note=the MED publishes no county in these lists, and each sheet has a medical tab "
                    "and a retail tab — both are included here",
                    "note=Denver and Broomfield are consolidated city-counties") if x),
            })
            rows.append(row)
    return rows


# ========================================================================= FLORIDA
def build_fl(blank, warn):
    """FDACS hemp cultivation licences. Florida's MEDICAL marijuana licensees
    (MMTCs) are published by OMMU as per-MMTC web pages, not as a list file, so
    they are not in this table yet."""
    from pypdf import PdfReader
    reader = PdfReader(RAW / "florida/fdacs_active_hemp_cultivation_licences_2026-09-10.pdf")
    text = "\n".join(pg.extract_text() or "" for pg in reader.pages)
    text = re.sub(r"[\u00a0\u2000-\u200b\u202f\u205f\u3000]", " ", text)
    row_re = re.compile(r"^(\d+_\d+)\s+(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)\s+"
                        r"(\d+[\w\-]*\s+.+?)\s+([A-Z][A-Z .'\-]*?)\s+(\d{5}(?:-\d{4})?)\s+"
                        r"FLORIDA\s*([A-Z][A-Z .'\-]*)?$")
    rows, unparsed = [], 0
    for line in (re.sub(r"[ \t]+", " ", l).strip() for l in text.splitlines()):
        m = row_re.match(line)
        if not m:
            if re.match(r"^\d+_\d+\s", line):
                unparsed += 1
            continue
        num, issued, rest, street, city, zipc, county = m.groups()
        county = (county or "").strip()   # FDACS leaves county blank on its 2026 records
        # `rest` is "<responsible person> <business name>"; FDACS writes the
        # person in caps and the business name mixed-case, so split on the
        # first token that is not all-caps.
        toks = rest.split()
        cut = next((i for i, w in enumerate(toks) if w != w.upper()), len(toks))
        person, business = " ".join(toks[:cut]).strip(), " ".join(toks[cut:]).strip()
        row = dict(blank)
        row.update({
            "licence_id": num, "state": "FL", "program": "Hemp", "category": "Hemp Grower",
            "licence_type": "Hemp Cultivation Licence",
            "legal_name": business or person, "holder_is_individual": "Y" if not business else "N",
            "status": "Active (FDACS publishes active licences only)", "standard_status": "Active",
            "issue_date": iso(issued),
            "street_address": ", ".join(x for x in (street, title(city), "FL", zipc) if x),
            "town": title(city), "town_as_listed": city,
            "county": title(county), "county_source": "FDACS COUNTY column" if county else "",
            "location_basis": "Licensed premises",
            "owners": person, "owner_count": "1" if person else "",
            "source": "FL FDACS Current List of Hemp Cultivation Licenses (10 Sept 2026)",
            "source_url": "https://www.fdacs.gov/Divisions-Offices/Plant-Industry/Hemp-Program",
            "data_as_of": "2026-09-10",
            "extra_details": "note=Florida's medical marijuana treatment centres (MMTCs) are published by "
                             "OMMU as individual web pages rather than a list, so they are not in this "
                             "table yet. FDACS names a Primary Responsible Person per licence; that is "
                             "kept in `owners`.",
        })
        rows.append(row)
    if unparsed:
        print(f"  FL: {unparsed} licence-number-leading lines did not match the row pattern")
        warn.append(("FL rows unparsed", str(unparsed)))
    return rows


# ======================================================================== VIRGINIA
def build_va(blank, warn):
    from pypdf import PdfReader
    rows = []
    # Registered industrial hemp processors under food-safety inspection
    txt = "\n".join(pg.extract_text() or "" for pg in
                    PdfReader(RAW / "virginia/vdacs_industrial_hemp_processors.pdf").pages)
    txt = re.sub(r"[\u00a0\u2000-\u200b\u202f\u205f\u3000]", " ", txt)
    proc = re.compile(r"^(.+?)\s+(\d+[\w\-]*\s+.+?)\s+([A-Za-z .'\-]+?)\s+VA\s+(\d{5})\s+(.+)$")
    for line in (re.sub(r"[ \t]+", " ", l).strip() for l in txt.splitlines()):
        m = proc.match(line)
        if not m:
            continue
        who, street, city, zipc, county = m.groups()
        # VDACS writes "Surname, Forename" then the firm name with no separator.
        mm = re.match(r"^([A-Z][a-z]+,\s*[A-Z][a-z]+)(.*)$", who)
        person, firm = (mm.group(1).strip(), mm.group(2).strip()) if mm else ("", who.strip())
        row = dict(blank)
        row.update({
            "licence_id": f"VA-HEMP-PROC-{len(rows) + 1:03d}", "state": "VA", "program": "Hemp",
            "category": "Hemp Processor", "licence_type": "Registered Industrial Hemp Processor",
            "legal_name": firm or person, "holder_is_individual": "N" if firm else "Y",
            "status": "Under VDACS food-safety inspection", "standard_status": "Active",
            "street_address": ", ".join(x for x in (street, title(city), "VA", zipc) if x),
            "town": title(city), "town_as_listed": city,
            "county": title(county), "county_source": "VDACS County column",
            "location_basis": "Licensed premises", "owners": person, "owner_count": "1" if person else "",
            "source": "VA VDACS Industrial Hemp Processors Under Food Safety Inspection (8 Oct 2026)",
            "source_url": "https://www.vdacs.virginia.gov/food-industrial-hemp.shtml",
            "data_as_of": "2026-10-08",
            "extra_details": f"{LOCAL_ID}; note=Virginia licenses no adult-use cannabis retail; its "
                             "pharmaceutical processors are a separate Board of Pharmacy programme not "
                             "in this table yet",
        })
        rows.append(row)
    # Approved hemp testing laboratories
    txt2 = "\n".join(pg.extract_text() or "" for pg in
                     PdfReader(RAW / "virginia/vdacs_hemp_approved_test_labs.pdf").pages)
    lab = re.compile(r"^(.+?)\s+(www\.[\w\.\-]+)\s+([\d\-\(\) ]{7,})$")
    for line in (re.sub(r"[ \t]+", " ", l).strip() for l in txt2.splitlines()):
        m = lab.match(line)
        if not m:
            continue
        name, site, phone = m.groups()
        row = dict(blank)
        row.update({
            "licence_id": f"VA-HEMP-LAB-{len(rows) + 1:03d}", "state": "VA", "program": "Hemp",
            "category": "Testing Lab", "licence_type": "VDACS-Approved Hemp Testing Laboratory",
            "legal_name": name.strip(), "holder_is_individual": "N",
            "status": "Approved", "standard_status": "Active",
            "location_basis": "No premises address published",
            "website": f"https://{site}", "contact_phone": phone.strip(), "contact_is_law_firm": "N",
            "source": "VA VDACS approved hemp testing laboratories",
            "source_url": "https://www.vdacs.virginia.gov/pdf/hemp-approved-test-labs.pdf",
            "data_as_of": TODAY,
            "extra_details": f"{LOCAL_ID}; note=VDACS publishes only lab name, website and phone",
        })
        rows.append(row)
    return rows


# ======================================================================== ILLINOIS
def build_il(blank, warn):
    """Illinois publishes no dispensary file — the page embeds a Tableau view,
    and this is that view's CSV export. IDOA's cultivation centres, craft
    growers, infusers and transporters are behind a separate portal that
    publishes only aggregate counts, so they are not in this table yet."""
    rows = []
    with open(RAW / "illinois/il_dispensary_locations_2026-11-10.csv", encoding="utf-8-sig") as f:
        for i, r in enumerate(csv.DictReader(f), 1):
            name = clean(r.get("Dispensary Name"))
            if not name:
                continue
            med = clean(r.get("Serves Medical Patients")).lower()   # the source mixes 'Yes' and 'yes'
            row = dict(blank)
            row.update({
                "licence_id": f"IL-DISP-{i:04d}", "state": "IL",
                "program": "Adult Use; Medical" if med == "yes" else "Adult Use",
                "category": "Retail Store", "licence_type": "Dispensary",
                "legal_name": name, "holder_is_individual": "N",
                "status": "Listed as an operating dispensary (no status column published)",
                "standard_status": "Active",
                "street_address": ", ".join(x for x in (clean(r.get("Street Address")),
                                                        title(r.get("City")), "IL") if x),
                "town": title(r.get("City")), "town_as_listed": clean(r.get("City")),
                "location_basis": "Licensed premises",
                "source": f"IL Dispensary Locations, Tableau view on public.data.illinois.gov — {LOCAL_ID}",
                "source_url": "https://cannabis.illinois.gov/about/locations.html",
                "data_as_of": "2026-11-10",
                "extra_details": "; ".join(x for x in (
                    f"bls region={clean(r.get('BLS Region'))}" if clean(r.get("BLS Region")) else "",
                    f"latitude={clean(r.get('Latitude'))}" if clean(r.get("Latitude")) else "",
                    f"longitude={clean(r.get('Longitude'))}" if clean(r.get("Longitude")) else "",
                    f"serves medical patients={clean(r.get('Serves Medical Patients'))}",
                    "note=no licence number, status or county is published; the source gives a BLS "
                    "region rather than a county, and repeats the dispensary-name column twice. "
                    "Cultivation centres, craft growers, infusers and transporters are not in this file") if x),
            })
            rows.append(row)
    return rows


# =========================================================================== OHIO
def build_oh(blank, warn):
    """DCC dispensaries from the ArcGIS feature service behind the dispensary
    map. Ohio's cultivators, processors and testing labs are only in the DCC
    eLicense portal, so they are not in this table yet."""
    d = json.loads((RAW / "ohio/oh_dcc_dispensaries.geojson").read_text())
    rows = []
    for ft in d.get("features", []):
        q = ft.get("properties", {})
        num = clean(str(q.get("user_licen") or ""))
        ltype = clean(str(q.get("user_type") or q.get("licensetype") or ""))
        if ltype.lower() in ("none", ""):
            ltype = ""
            warn.append(("OH licence type blank", "(none)"))
        g = ft.get("geometry") or {}
        lon, lat = (g.get("coordinates") or ["", ""])[:2] if g.get("type") == "Point" else ("", "")
        raw_status = clean(str(q.get("user_lic_1") or ""))
        row = dict(blank)
        row.update({
            "licence_id": num or f"OH-DISP-OBJ{q.get('objectid')}", "state": "OH",
            # "Dual Use" means the dispensary serves both medical patients and
            # adult-use customers, which is Ohio's only dispensary form.
            "program": "Adult Use; Medical" if "dual" in ltype.lower() else "Medical",
            "category": "Retail Store", "licence_type": ltype or "Dispensary",
            "legal_name": clean(str(q.get("user_busin") or "")),
            "dba": clean(str(q.get("user_dispe") or "")), "holder_is_individual": "N",
            "status": raw_status, "standard_status": "Active" if raw_status == "Active" else "",
            "street_address": ", ".join(x for x in (clean(str(q.get("user_stree") or "")),
                                                    title(str(q.get("user_city") or "")), "OH",
                                                    clean(str(q.get("user_zip") or ""))) if x),
            "town": title(str(q.get("user_city") or "")),
            "town_as_listed": clean(str(q.get("user_city") or "")),
            "county": title(str(q.get("user_count") or "")),
            "county_source": "DCC GIS county field" if clean(str(q.get("user_count") or "")) else "",
            "location_basis": "Licensed premises",
            "contact_phone": clean(str(q.get("user_phone") or "")), "contact_is_law_firm": "N",
            "source": "OH DCC Cannabis Dispensary Map, ArcGIS feature service on maps.ohio.gov",
            "source_url": "https://maps.ohio.gov/arcgis/rest/services/Hosted/Geocoded_Dispensaries_/FeatureServer/0",
            "data_as_of": TODAY,
            "extra_details": "; ".join(x for x in (
                f"latitude={lat}" if lat else "", f"longitude={lon}" if lon else "",
                f"hours={clean(str(q.get('hours') or ''))}" if clean(str(q.get("hours") or "")) else "",
                "note=the source spells its own licence type three ways (Dual, Dual Use, Dual Use "
                "Dispensary) and its state two ways (Ohio, OH). Ohio's cultivators, processors and "
                "testing labs are only in the DCC eLicense portal, not in this layer") if x),
        })
        rows.append(row)
    return rows


# ======================================================================= MISSOURI
def build_mo(blank, warn):
    """DCR verified dispensaries from the ArcGIS service behind the locator.
    Missouri's cultivation, manufacturing and testing licensees are not in this
    layer; the xlsx files on health.mo.gov are product-recall lists."""
    d = json.loads((RAW / "missouri/mo_dcr_verified_dispensaries.geojson").read_text())
    rows = []
    for ft in d.get("features", []):
        q = ft.get("properties", {})
        num = clean(str(q.get("License") or ""))
        names = [x.strip() for x in clean(str(q.get("Dispensary") or "")).split(";") if x.strip()]
        g = ft.get("geometry") or {}
        lon, lat = (g.get("coordinates") or ["", ""])[:2] if g.get("type") == "Point" else ("", "")
        row = dict(blank)
        row.update({
            "licence_id": num or f"MO-DISP-OBJ{q.get('ObjectId')}", "state": "MO",
            "program": "Adult Use; Medical", "category": "Retail Store",
            "licence_type": "Comprehensive Dispensary",
            "legal_name": names[0] if names else "", "dba": names[1] if len(names) > 1 else "",
            "holder_is_individual": "N",
            # DCR publishes this as a list of VERIFIED dispensaries; there is no
            # status column, so every row in it is a verified licensed facility.
            "status": "Verified (DCR publishes verified dispensaries only; no status column)",
            "standard_status": "Active",
            "street_address": ", ".join(x for x in (clean(str(q.get("Address") or "")),
                                                    title(str(q.get("City") or "")), "MO",
                                                    clean(str(q.get("Zip_code") or ""))) if x),
            "town": title(str(q.get("City") or "")),
            "town_as_listed": clean(str(q.get("City") or "")),
            "county": title(str(q.get("County") or "")),
            "county_source": "DCR GIS County field" if clean(str(q.get("County") or "")) else "",
            "location_basis": "Licensed premises",
            "website": clean(str(q.get("Website") or "")),
            "contact_phone": clean(str(q.get("Phone_Number") or "")), "contact_is_law_firm": "N",
            "source": "MO DCR Verified Dispensary Locator, ArcGIS feature service",
            "source_url": "https://health.mo.gov/business-professionals/cannabis-regulation/licensee-compliance-guidance/licensed-facilities",
            "data_as_of": TODAY,
            "extra_details": "; ".join(x for x in (
                f"latitude={lat}" if lat else "", f"longitude={lon}" if lon else "",
                f"source last updated={clean(str(q.get('Last_updated') or ''))}"
                if clean(str(q.get("Last_updated") or "")) else "",
                "note=the Dispensary field packs the licensee and its trading name into one "
                "semicolon-separated value; cultivation, manufacturing and testing licensees are "
                "not in this layer") if x),
        })
        rows.append(row)
    return rows


# ========================================================================= HAWAII
HI_REC = re.compile(
    r"^(?P<n>\d+)\.\s+(?P<body>.+?)\s+(?P<city>[A-Z][A-Za-z'\- ]*?)\s+HI\s+(?P<zip>\d{5})\s+"
    r"(?P<site>.+?)\s+(?P<reg>\d{2}-[0-9A-Za-z\-]+)\s+(?P<frm>\d{1,2}/\d{1,2}/\d{4})\s*-\s*"
    r"(?P<to>\d{1,2}/\d{1,2}/\d{4})")


# Online-only registrants have no street, city or zip — just a state and a site.
HI_REC_NOADDR = re.compile(
    r"^(?P<n>\d+)\.\s+(?P<body>.+?)\s+(?P<st>[A-Z]{2})\s+(?P<site>\S+)\s+"
    r"(?P<reg>\d{2}-[0-9A-Za-z\-]+)\s+(?P<frm>\d{1,2}/\d{1,2}/\d{4})\s*-\s*"
    r"(?P<to>\d{1,2}/\d{1,2}/\d{4})")


def build_hi(blank, warn):
    """DOH Manufactured Hemp Product retailer and distributor registry. The PDF
    wraps each record over several lines but numbers them, so records are
    reassembled on the numbering before parsing."""
    from pypdf import PdfReader
    text = "\n".join(pg.extract_text() or "" for pg in
                     PdfReader(RAW / "hawaii/hi_hemp_registry_public_2026-10.pdf").pages)
    text = re.sub(r"[\u00a0\u2000-\u200b\u202f\u205f\u3000]", " ", text)
    lines = [re.sub(r"[ \t]+", " ", l).strip() for l in text.splitlines() if l.strip()]
    # Reassemble: a record starts at "N." and runs until the next one.
    recs, cur = [], None
    for l in lines:
        if re.match(r"^\d+\.\s", l):
            if cur:
                recs.append(" ".join(cur))
            cur = [l]
        elif cur is not None:
            cur.append(l)
    if cur:
        recs.append(" ".join(cur))
    rows, unparsed = [], 0
    for rec in recs:
        # Page footers get glued onto the record above them.
        rec = re.split(r"Current as of", re.sub(r"\s+", " ", rec))[0].strip()
        m = HI_REC.match(rec)
        no_addr = False
        if not m:
            m = HI_REC_NOADDR.match(rec)
            no_addr = bool(m)
        if not m:
            unparsed += 1
            continue
        body = m.group("body").strip()
        # The address begins at the first number-led token; the name (and DBA,
        # where DOH gives one) is everything before it.
        if no_addr:
            who, street, city, zipc = body, "", "", ""
            home_state = m.group("st")
        else:
            am = re.search(r"(?:^|\s)(\d+[\w\-]*\s)", body)
            who, street = (body[:am.start()].strip(), body[am.start():].strip()) if am else (body, "")
            city, zipc, home_state = m.group("city"), m.group("zip"), "HI"
        site = m.group("site").strip()
        online = not re.search(r"(?i)not registered to sell\s*online", site)
        row = dict(blank)
        row.update({
            "licence_id": m.group("reg"), "state": "HI", "program": "Hemp",
            "category": "Hemp Retail", "licence_type": "MHP Retailer / Distributor Registration",
            "legal_name": who, "holder_is_individual": "N",
            "status": "Registered", "standard_status": "Active",
            "issue_date": iso(m.group("frm")), "expiry_date": iso(m.group("to")),
            "street_address": ", ".join(x for x in (street, title(city), home_state, zipc) if x),
            "town": title(city), "town_as_listed": city,
            "location_basis": "Online only — no premises address registered" if no_addr
                              else "Registered premises",
            "website": site if online else "",
            "source": "HI DOH Manufactured Hemp Product Retailer and Distributor Registry "
                      "(public list, current as of 26 Oct 2026)",
            "source_url": "https://health.hawaii.gov/hempprogram/", "data_as_of": "2026-10-26",
            "extra_details": "; ".join(x for x in (
                "registered to sell online=no" if not online else "registered to sell online=yes",
                f"registrant home state={home_state}" if home_state != "HI" else "",
                "no premises address=DOH records only a state and a website for this registrant"
                if no_addr else "",
                "note=DOH publishes no county; Hawaii has no municipal government below county "
                "level. This registry covers manufactured hemp product retailers and distributors, "
                "not Hawaii's medical dispensary licences") if x),
        })
        rows.append(row)
    if unparsed:
        print(f"  HI: {unparsed} numbered records did not match the row pattern")
        warn.append(("HI records unparsed", str(unparsed)))
    return rows


BUILDERS = {"CA": build_ca, "OR": build_or, "WA": build_wa, "NV": build_nv,
            "TX": build_tx, "AL": build_al, "CO": build_co, "FL": build_fl,
            "VA": build_va, "IL": build_il, "OH": build_oh, "MO": build_mo,
            "HI": build_hi}








def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state"), ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    with open(NE, encoding="utf-8") as f:
        cols = list(next(csv.DictReader(f)).keys())
    blank = {c: "" for c in cols}
    warn, rows = [], []
    todo = [a.state.upper()] if a.state else list(BUILDERS)
    for st in todo:
        if st not in BUILDERS:
            sys.exit(f"no spec for {st}; have {sorted(BUILDERS)}")
        got = BUILDERS[st](blank, warn)
        print(f"  {st}: {len(got)} rows")
        rows.extend(got)
    # Final safety net: whatever each spec does, a (state, licence_id) pair must
    # be unique or rows silently overwrite each other downstream. Any collision
    # left here gets a local suffix and says so on the row.
    counts = collections.Counter((r["state"], r["licence_id"]) for r in rows)
    seen, suffixed = collections.Counter(), 0
    for r in rows:
        k = (r["state"], r["licence_id"])
        if counts[k] > 1:
            seen[k] += 1
            r["licence_id"] = f'{r["licence_id"]}~{seen[k]}'
            note = ("id suffixed locally=the source holds more than one row with this identity; "
                    "the suffix keeps them distinct and is not part of the licence number")
            r["extra_details"] = "; ".join(x for x in (r["extra_details"], note) if x)
            suffixed += 1
    if suffixed:
        print(f"  note: {suffixed} rows needed a local id suffix to stay distinct")
    rows.sort(key=lambda r: (r["state"], r["licence_id"]))

    print(f"\ntotal {len(rows)} rows")
    print("  per state: rows | with county | with standard_status | approximated")
    for st in sorted({r["state"] for r in rows}):
        sr = [r for r in rows if r["state"] == st]
        print(f"     {st}: {len(sr):>6} | {sum(1 for r in sr if r['county']):>6} | "
              f"{sum(1 for r in sr if r['standard_status']):>6} | "
              f"{sum(1 for r in sr if 'approximate=yes' in r['extra_details']):>6}")
        d = collections.Counter(r["standard_status"] or "(none)" for r in sr)
        print(f"        {dict(d.most_common())}")
    if warn:
        print("\nUNMAPPED or flagged (left empty or approximated, never guessed):")
        for (kind, val), n in collections.Counter(warn).most_common(14):
            print(f"  {n:>6}  {kind}: {val!r}")
    if a.dry_run:
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
