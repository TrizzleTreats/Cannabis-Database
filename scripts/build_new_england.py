#!/usr/bin/env python3
"""Rebuild data/clean/new_england_licences.csv from the official files in data/raw/.

This is a MERGE, not a replace. The existing master table carries enrichment the
raw downloads do not have — county and its source, group linkage, municipal
opt-in, owners, location basis — so a straight rebuild from raw would quietly
downgrade the table. Enrichment is carried forward by licence id; genuinely new
rows get what raw supplies and leave the rest empty rather than guessed.

Connecticut and Massachusetts are rebuilt from raw because raw has materially
more: CT gained 280 hemp and THC-beverage credentials the old snapshot omitted,
and MA has 127 licence numbers plus real Expired/Surrendered/Revoked/Suspended
statuses the old snapshot flattened. Maine, Vermont, Rhode Island and New
Hampshire are carried forward unchanged — their raw files hold nothing the
table does not already have, so churning them would add risk and no data.

Usage: python3 scripts/build_new_england.py [--dry-run]
"""
import argparse, csv, collections, pathlib, sys
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
MASTER = ROOT / "data" / "clean" / "new_england_licences.csv"
TODAY = date.today().isoformat()

# Fields the raw downloads cannot supply. Carried forward from the prior table
# for rows that already existed; left empty for new rows.
ENRICHMENT = ["county", "county_source", "location_basis", "town_opted_in_adult_use",
              "town_allows_this_activity", "website", "contact_name", "contact_is_law_firm",
              "owners", "owner_count", "group_id", "linked_group", "licences_in_group",
              "programs_in_group", "grow_town", "grow_county", "retail_town",
              "retail_county", "first_issue_date"]

# ---------------------------------------------------------------- Connecticut
CT_MAP = {
    "CANNABIS CULTIVATOR": ("Adult Use", "Cultivation", "Cannabis Cultivator"),
    "CANNABIS ACCE EXTENDED LOCATION": ("Adult Use", "Cultivation", "Cannabis ACCE Extended Location"),
    "CANNABIS MICRO-CULTIVATOR": ("Adult Use", "Micro-Cultivation", "Cannabis Micro-Cultivator"),
    "CANNABIS DELIVERY SERVICE": ("Adult Use", "Delivery", "Cannabis Delivery Service"),
    "CANNABIS FOOD AND BEVERAGE MANUFACTURER": ("Adult Use", "Manufacturing", "Cannabis Food And Beverage Manufacturer"),
    "CANNABIS PRODUCT MANUFACTURER": ("Adult Use", "Manufacturing", "Cannabis Product Manufacturer"),
    "CANNABIS PRODUCT PACKAGER": ("Adult Use", "Packager", "Cannabis Product Packager"),
    "CANNABIS RETAILER": ("Adult Use", "Retail Store", "Cannabis Retailer"),
    "CANNABIS TRANSPORTER": ("Adult Use", "Transporter", "Cannabis Transporter"),
    "CANNABIS TESTING LABORATORY": ("Testing", "Testing Lab", "Cannabis Testing Laboratory"),
    "MEDICAL CANNABIS HYBRID RETAILER": ("Adult Use; Medical", "Hybrid Retailer", "Medical Cannabis Hybrid Retailer"),
    "MEDICAL CANNABIS DISPENSARY FACILITY": ("Medical", "Medical Dispensary", "Medical Cannabis Dispensary Facility"),
    "MEDICAL CANNABIS PRODUCER": ("Medical", "Cultivation", "Medical Cannabis Producer"),
    "MEDICAL CANNABIS RESEARCH PROGRAM": ("Medical", "Research", "Medical Cannabis Research Program"),
    "HEMP PRODUCER": ("Hemp", "Hemp Grower", "Hemp Producer"),
    "MANUFACTURER OF HEMP CONSUMABLES": ("Hemp", "Hemp Manufacturer", "Manufacturer Of Hemp Consumables"),
    "MANUFACTURER OF THC-INFUSED BEVERAGES": ("Hemp", "THC Beverage Manufacturer", "Manufacturer Of Thc-Infused Beverages"),
    "WHOLESALER OF THC-INFUSED BEVERAGES": ("Hemp", "THC Beverage Wholesaler", "Wholesaler Of Thc-Infused Beverages"),
    "MODERATE-THC HEMP PRODUCT VENDOR": ("Hemp", "Hemp Retailer", "Moderate-Thc Hemp Product Vendor"),
}

# An application that never became a licence is not a licence. The distinction
# lives in statusreason, not status: "EXPIRED APPLICATION / NSF PAYMENT DUE" is a
# dead application, while "EXPIRED APPLICATION / PROVISIONAL LICENSE EXPIRED" was
# a real provisional licence. Keyed (status, statusreason); None = exclude.
CT_STATUS = {
    ("ACTIVE", "*"): "Active",
    ("ACTIVE IN RENEWAL", "*"): "Active",
    ("ACTIVE BY PROVISIONAL", "*"): "Provisional",
    ("PENDING", "*"): "Pending",
    ("APPROVED", "*"): "Pending",
    ("REVOKED", "*"): "Revoked",
    ("LAPSED", "*"): "Expired",
    ("DENIED", "*"): None,
    ("EXPIRED APPLICATION", "PROVISIONAL LICENSE EXPIRED"): "Expired",
    ("EXPIRED APPLICATION", "*"): None,
    ("INACTIVE", "DUE TO NON-RENEWAL OF CREDENTIAL"): "Expired",
    ("INACTIVE", "OUT OF BUSINESS"): "Surrendered",
    ("INACTIVE", "APPLICATION EXPIRED"): None,
    ("INACTIVE", "WITHDRAWN"): None,
    ("INACTIVE", "*"): "Expired",
    ("CLOSED", "WITHDRAWN"): None,
    ("CLOSED", "INSPECTION INCOMPLETE"): None,
    ("CLOSED", "*"): "Surrendered",
}
CT_SRC = "CT DCP eLicensing — State Licenses and Credentials (data.ct.gov ngch-56tr)"
CT_URL = "https://data.ct.gov/d/ngch-56tr"


def ct_standard_status(status, reason):
    if (status, reason) in CT_STATUS:
        return CT_STATUS[(status, reason)], False
    if (status, "*") in CT_STATUS:
        # Fell through to the catch-all: the reason wording was not one we have
        # decided on, so the mapping is a default, not a reading of the record.
        return CT_STATUS[(status, "*")], (status, reason) not in CT_STATUS
    return "UNMAPPED", True


def iso(d):
    """CT and MA date fields arrive in several shapes. Never invent a date."""
    d = (d or "").strip()
    if not d:
        return ""
    if "T" in d:
        d = d.split("T")[0]
    if len(d) == 10 and d[4] == "-":
        return d
    for sep in ("-", "/"):
        p = d.split(sep)
        if len(p) == 3 and len(p[2]) == 4:
            return f"{p[2]}-{p[0].zfill(2)}-{p[1].zfill(2)}"
    return d


def title(s):
    s = (s or "").strip()
    return s.title() if s.isupper() or s.islower() else s


# Regulator test records are not licences. Connecticut's DCP leaves its own test
# credentials in the public file, named "TEST RECORD" and registered to its own
# office (450 Columbus Blvd, Hartford) — 28 of them on 12 Nov 2026, several with
# real-looking numbers (ACRE.0015712, CSW.0005793-TIB), so they are matched by
# name, which also catches any new ones a daily refresh brings in. Vermont's
# three carry no such marker beyond the name, so they are named by licence id.
CT_TEST_NAME = "TEST RECORD"
TEST_RECORD_IDS = {
    ("VT", "MANU0073"): "High Society - Test - Manufacturing",
    ("VT", "MANU0123"): "Test - MANU0123",
    ("VT", "RTLR0086"): "Test - RTLR0086",
}


def is_test_record(state, licence_id, legal_name, dba):
    if (state, licence_id) in TEST_RECORD_IDS:
        return True
    return state == "CT" and CT_TEST_NAME in (legal_name.upper(), dba.upper())


CT_READ_ON = "2026-11-12"   # the fetch date in the raw file's name and manifest row


def build_ct(prior, town_county, blank):
    src = ROOT / "data/raw/connecticut/ngch-56tr_business_credentials_2026-11-12.csv"
    rows, excluded, unmapped = [], collections.Counter(), []
    with open(src, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            std, defaulted = ct_standard_status(r["status"], r["statusreason"])
            if std is None:
                excluded[f'{r["status"]} / {r["statusreason"] or "(blank)"}'] += 1
                continue
            if std == "UNMAPPED":
                unmapped.append((r["status"], r["statusreason"]))
                std = ""
            cred = r["credential"]
            program, category, ltype = CT_MAP.get(cred, ("", "", title(cred)))
            if cred not in CT_MAP:
                unmapped.append(("credential", cred))
            # CT publishes no credentialnumber for some hemp producers, so their
            # fullcredentialcode collapses to a bare type stub ("HEMP.CT") shared
            # by many holders. credentialid is the unique key in that case.
            lid = r["fullcredentialcode"]
            if not (r.get("credentialnumber") or "").strip():
                lid = f"{lid}#{r['credentialid']}"
            town = title(r.get("city", ""))
            row = dict(blank)
            row.update({
                "licence_id": lid, "state": "CT", "program": program, "category": category,
                "licence_type": ltype,
                "legal_name": r.get("businessname") or r.get("name", ""),
                "dba": r.get("dba", ""),
                "holder_is_individual": "Y" if (r.get("name") and not r.get("businessname")) else "N",
                # The state's own wording is kept beside the standard status, never replaced.
                "status": "; ".join(x for x in (title(r["status"]), title(r["statusreason"])) if x),
                "standard_status": std,
                "issue_date": iso(r.get("issuedate")), "expiry_date": iso(r.get("expirationdate")),
                "street_address": ", ".join(x for x in (r.get("address", "").strip(), town,
                                                        r.get("state", ""), r.get("zip", "")) if x),
                "town": town, "town_as_listed": r.get("city", ""),
                "source": CT_SRC, "source_url": CT_URL,
                "data_as_of": iso(r.get("recordrefreshedon")) or CT_READ_ON,
            })
            carry(row, prior.get(("CT", lid)), town_county, "CT", town)
            if std == "Provisional":
                row["licence_type"] = row["licence_type"]
            rows.append(row)
    return rows, excluded, unmapped


# -------------------------------------------------------------- Massachusetts
MA_MAP = {
    "Marijuana Retailer": ("Adult Use", "Retail Store", "Marijuana Retailer"),
    "Marijuana Cultivator": ("Adult Use", "Cultivation", "Marijuana Cultivator"),
    "Craft Marijuana Cooperative": ("Adult Use", "Cultivation", "Craft Marijuana Cooperative"),
    "Marijuana Product Manufacturer": ("Adult Use", "Manufacturing", "Marijuana Product Manufacturer"),
    "Independent Testing Laboratory": ("Testing", "Testing Lab", "Independent Testing Laboratory"),
    "Marijuana Microbusiness": ("Adult Use", "Microbusiness", "Marijuana Microbusiness"),
    "Marijuana Courier": ("Adult Use", "Delivery", "Marijuana Courier"),
    "Marijuana Delivery Operator": ("Adult Use", "Delivery", "Marijuana Delivery Operator"),
    "Microbusiness Delivery": ("Adult Use", "Delivery", "Microbusiness Delivery"),
    "Third Party Marijuana Transporter": ("Adult Use", "Transporter", "Third Party Marijuana Transporter"),
    "Marijuana Transporter with Other Existing ME License": ("Adult Use", "Transporter", "Marijuana Transporter with Other Existing ME License"),
    "Medical Marijuana Treatment Center": ("Medical", "Medical Dispensary", "Medical Marijuana Treatment Center"),
}
MA_STATUS = {"Active": "Active", "Expired": "Expired", "Surrendered": "Surrendered",
             "Revoked": "Revoked", "Suspended": "Suspended", "Payment Pending": "Pending"}
MA_SRC = "Mass. Cannabis Control Commission, all licences (public) — EIN/TIN column dropped"
MA_URL = "https://masscannabiscontrol.com/resource/l_licenses_all_details_public.csv"
# The date the MA raw files were read. They predate scripts/fetch_raw.py and have no
# manifest row; they arrived in the initial commit on 12 Nov 2026, which is the date
# every MA row carried until a rebuild stamped the run date instead. A data_as_of
# must say when the regulator's file was read, never when this script last ran.
MA_READ_ON = "2026-11-12"


def build_ma(prior, town_county, blank):
    raw, unmapped = {}, []
    for name in ("l_licenses_all_details_public.csv", "l_licenses_commence_ops.csv"):
        with open(ROOT / "data/raw/massachusetts" / name, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if r.get("LICENSE_NUMBER"):
                    # all_details is read first and wins; commence_ops only adds rows.
                    raw.setdefault(r["LICENSE_NUMBER"], r)
    assert not any("EIN" in k.upper() or "TIN" in k.upper() for k in next(iter(raw.values()))), \
        "MA raw carries an EIN/TIN column — CLAUDE.md forbids using it"
    rows = []
    for lid, r in raw.items():
        # The CCC export ships some values with trailing whitespace.
        ltype = (r.get("LICENSE_TYPE") or "").strip()
        program, category, name = MA_MAP.get(ltype, ("", "", ltype))
        if ltype not in MA_MAP:
            unmapped.append(("LICENSE_TYPE", ltype))
        env = (r.get("CULTIVATION_ENVIRONMNET") or "").strip()
        if env and category in ("Cultivation",):
            name = f"{name} ({env.title()})"
        raw_status = r.get("LICENSE_STATUS", "")
        std = MA_STATUS.get(raw_status, "")
        if raw_status and not std:
            unmapped.append(("LICENSE_STATUS", raw_status))
        stage = (r.get("APPROVED_LICENSE_STAGE") or "").strip()
        commenced = (r.get("COMMENCE_OPERATIONS_DATE") or "").strip()
        # "operating" is asserted only where the CCC gives a commence-operations
        # date AND the licence is not suspended — a suspended licence is not operating.
        if commenced and raw_status == "Active":
            operating = "operating"
        elif commenced:
            operating = "not operating"      # it did commence, and no longer trades
        else:
            operating = "not yet operating"  # never commenced
        town = title(r.get("ESTABLISHMENT_CITY") or r.get("BUSINESS_CITY", ""))
        row = dict(blank)
        row.update({
            "licence_id": lid, "state": "MA", "program": program, "category": category,
            "licence_type": name, "tier": (r.get("CULTIVATION_TIER") or "").strip(),
            "legal_name": r.get("BUSINESS_NAME", ""), "holder_is_individual": "N",
            "status": "; ".join(x for x in (raw_status, stage, operating) if x),
            "standard_status": std,
            "issue_date": iso(r.get("LIC_START_DATE")),
            "expiry_date": iso(r.get("LIC_EXPIRATION_DATE")),
            "first_issue_date": iso(r.get("LIC_ORIGINAL_START_DATE")),
            "street_address": ", ".join(x for x in (
                (r.get("ESTABLISHMENT_ADDRESS_1") or r.get("BUSINESS_ADDRESS_1") or "").strip(),
                town, r.get("BUSINESS_STATE", ""), r.get("BUSINESS_ZIP_CODE", "")) if x),
            "town": town, "town_as_listed": r.get("ESTABLISHMENT_CITY") or r.get("BUSINESS_CITY", ""),
            "contact_phone": r.get("BUSINESS_PHONE", ""), "contact_email": r.get("BUSINESS_EMAIL", ""),
            "contact_is_law_firm": "N",
            "source": MA_SRC, "source_url": MA_URL, "data_as_of": MA_READ_ON,
        })
        carry(row, prior.get(("MA", lid)), town_county, "MA", town)
        rows.append(row)
    return rows, unmapped


def carry(row, old, town_county, state, town):
    """Carry enrichment forward; for a new row fall back to a town->county pair
    already verified in the prior table. Never invent a county."""
    for f in ENRICHMENT:
        if not row.get(f) and old and old.get(f):
            row[f] = old[f]
    if not row.get("county") and town:
        c = town_county.get((state, town.lower()))
        if c:
            row["county"], row["county_source"] = c, "town lookup (carried from prior table)"
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(MASTER, encoding="utf-8") as f:
        old_rows = list(csv.DictReader(f))
    cols = list(old_rows[0].keys())
    if "standard_status" not in cols:
        cols.insert(cols.index("status") + 1, "standard_status")
    # HANDOFF's schema calls for a state-specific "extra details" slot. The
    # Mid-Atlantic table needs it heavily; carrying it here too (mostly empty)
    # keeps the two regional tables unionable without a later migration.
    if "extra_details" not in cols:
        cols.append("extra_details")
    blank = {c: "" for c in cols}
    prior = {(r["state"], r["licence_id"]): r for r in old_rows}
    town_county = {(r["state"], r["town"].lower()): r["county"]
                   for r in old_rows if r["town"] and r["county"]}
    before = collections.Counter(r["state"] for r in old_rows)

    ct, ct_excluded, ct_unmapped = build_ct(prior, town_county, blank)
    ma, ma_unmapped = build_ma(prior, town_county, blank)
    # The prior table recorded only each state's own wording. Map it to the
    # standard status so one search can span all six states, keeping the
    # state's wording in `status` untouched.
    CARRIED_STATUS = {
        "Active": "Active",
        "Conditional": "Provisional",
        "Conditional, Jurisdiction Approved": "Provisional",
        "Pending Conditional": "Pending",
        "Pending": "Pending",
    }
    carried, carried_unmapped = [], []
    for r in old_rows:
        if r["state"] not in ("ME", "VT", "RI", "NH"):
            continue
        row = dict(blank, **{k: v for k, v in r.items() if k in blank})
        std = CARRIED_STATUS.get(r["status"].strip())
        if std:
            row["standard_status"] = std
        elif r["status"].strip():
            carried_unmapped.append(("status (" + r["state"] + ")", r["status"]))
        carried.append(row)

    new_rows = carried + ct + ma
    tests = [r for r in new_rows
             if is_test_record(r["state"], r["licence_id"], r["legal_name"], r["dba"])]
    new_rows = [r for r in new_rows if r not in tests]
    new_rows.sort(key=lambda r: (r["state"], r["licence_id"]))
    after = collections.Counter(r["state"] for r in new_rows)

    print("state   before    after   change   source")
    for st in ("CT", "MA", "ME", "NH", "RI", "VT"):
        how = "rebuilt from data/raw/" if st in ("CT", "MA") else "carried forward unchanged"
        d = after[st] - before[st]
        print(f"  {st}   {before[st]:>6}   {after[st]:>6}   {d:>+6}   {how}")
    print(f"total   {sum(before.values()):>6}   {sum(after.values()):>6}   {sum(after.values())-sum(before.values()):>+6}")

    print("\nCT application records excluded (not licences):")
    for k, n in ct_excluded.most_common():
        print(f"  {n:>4}  {k}")
    print(f"  {sum(ct_excluded.values()):>4}  total excluded")

    print("\nRegulator test records excluded (not licences):")
    for st, n in sorted(collections.Counter(r["state"] for r in tests).items()):
        print(f"  {n:>4}  {st}")

    unmapped = collections.Counter(ct_unmapped + ma_unmapped + carried_unmapped)
    if unmapped:
        print("\nUNMAPPED values (left empty, never guessed):")
        for (kind, val), n in unmapped.most_common():
            print(f"  {n:>4}  {kind}: {val!r}")
    else:
        print("\nNo unmapped licence types or statuses.")

    if args.dry_run:
        print("\n[dry-run] nothing written")
        return
    with open(MASTER, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in new_rows:
            w.writerow({c: r.get(c, "") for c in cols})
    print(f"\nwrote {MASTER.relative_to(ROOT)} — {len(new_rows)} rows, {len(cols)} columns")


if __name__ == "__main__":
    main()
