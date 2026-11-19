#!/usr/bin/env python3
"""Build the public data files the website reads, in site/data/.

CLAUDE.md: "Private columns — strip before any deploy ... data/clean/ is tracked
in git with these columns present, so the public build must drop them
explicitly — git-ignoring data/private/ is not by itself enough."

So the column lists here are ALLOWLISTS, never denylists. A denylist fails open:
add a private column to a clean table next year and it ships. An allowlist fails
closed — a new column is absent from the site until someone decides it is public
and names it here. The private columns are also listed, but only so this script
can assert they are gone and refuse to write if they are not.

The data is real: the clean tables hold 35,520 premises phone numbers, 20,842
emails and 21,276 owner records. None of it belongs on the public site.

Two other CLAUDE.md rules shape what is emitted:
  * "Unverified entries stay off the public site until checked." Business
    entries marked Unverified or needs_verify are built into a separate file
    the public pages do not load, rather than silently dropped, so the count
    is visible and nothing is lost.
  * "Every fact and every count carries a source link and a date." Every
    licence keeps its source, source_url and data_as_of, and every summary
    count carries the date of the data it came from.

Licences are written per state, and split into a list file and a detail file.
California alone is 20,984 rows, so one file for everything would be tens of
megabytes and the Database page would load all of it to show one state. The
list file carries only what a results table shows; the detail file carries the
full public record, including the long per-row extra_details prose, and is
loaded when a profile is opened. Both are built from the same allowlist, so the
split is about payload size and never about what is public.

Usage:
  python3 scripts/build_site_data.py [--dry-run]
"""
import argparse, collections, csv, json, pathlib, re, shutil, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import us_map  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLEAN = ROOT / "data" / "clean"
OUT = ROOT / "site" / "data"
TABLES = ["new_england_licences.csv", "mid_atlantic_licences.csv",
          "regions_3_to_9_licences.csv"]

# Named in CLAUDE.md. Asserted absent from every file written.
PRIVATE = ["contact_name", "contact_phone", "contact_email", "owners", "key_people_private"]

# A licence row as the public site may see it. Premises address, town and county
# are public record — the regulator publishes them — and are what the county
# maps need. owner_count is an aggregate, not a person; contact_is_law_firm is a
# flag about the contact, not the contact.
LICENCE_PUBLIC = [
    "licence_id", "state", "program", "category", "licence_type", "standard_type",
    "standard_types_all", "tier", "legal_name", "dba", "holder_is_individual",
    "status", "standard_status", "issue_date", "expiry_date", "first_issue_date",
    "street_address", "town", "town_as_listed", "county", "county_source",
    "location_basis", "town_opted_in_adult_use", "town_allows_this_activity",
    "website", "contact_is_law_firm", "owner_count", "group_id", "linked_group",
    "licences_in_group", "programs_in_group", "grow_town", "grow_county",
    "retail_town", "retail_county", "source", "source_url", "data_as_of",
    "extra_details",
]

# What a results table shows. A subset of LICENCE_PUBLIC, never a superset.
LICENCE_LIST = [
    "licence_id", "state", "program", "standard_type", "standard_status", "status",
    "licence_type", "legal_name", "dba", "town", "county", "expiry_date", "website",
]

BUSINESS_PUBLIC = [
    "business_id", "profile_id", "region", "regions_in_profile", "entries_in_profile",
    "scope", "home_state", "category", "business_name", "sub_type", "cannabis_focus",
    "description", "website", "phone", "email", "address", "states_served",
    "states_served_codes", "credentials", "evidence_links", "audit_verdict",
    "needs_verify", "audit_note", "sources", "last_checked",
]

# The home-page map's legal status per jurisdiction (scripts/build_legal_status.py).
# Statements about the law, each with its citation, official link and audit date.
LEGAL_PUBLIC = ["state", "state_name", "legal_status", "citation", "source_url",
                "source_kind", "note", "report_last_audited"]

UNVERIFIED = ("unverif",)


def rows_of(name):
    with open(CLEAN / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def public(row, allowed):
    """Only the allowed keys, and only those with a value."""
    return {k: row[k] for k in allowed if (row.get(k) or "").strip()}


def assert_clean(obj, where):
    """Refuse to emit anything carrying a private key, at any depth."""
    stack = [obj]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            for key, value in item.items():
                if key in PRIVATE:
                    sys.exit(f"REFUSING TO WRITE {where}: private column {key!r} present")
                stack.append(value)
        elif isinstance(item, list):
            stack.extend(item)


def write(path, obj, dry_run):
    assert_clean(obj, path.name)
    if dry_run:
        return len(json.dumps(obj, separators=(",", ":")))
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    path.write_text(text, encoding="utf-8")
    return len(text)


# ------------------------------------------------------------ detail buckets
BUCKET_SIZE = 300


def buckets_for(n):
    return max(1, -(-n // BUCKET_SIZE))


def bucket(licence_id, nb):
    """FNV-1a over the id's characters. site/assets/app.js computes the same
    function to find a licence's bucket, so the two must not drift: ids are
    ASCII (verify.py checks), where Python's ord() and JS charCodeAt() agree."""
    h = 0x811C9DC5
    for ch in licence_id:
        h ^= ord(ch)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h % nb


RELATED_CAP = 12
NAME_NOISE = re.compile(r"[^a-z0-9 ]+")
NAME_SUFFIX = re.compile(r"\b(llc|l l c|inc|incorporated|corp|corporation|co|ltd|lp|llp|pllc|pc)\b")


def norm_name(name):
    n = NAME_NOISE.sub(" ", name.lower())
    return " ".join(NAME_SUFFIX.sub(" ", n).split())


def usable_address(addr):
    a = addr.strip().lower()
    return bool(re.search(r"\d", a)) and "not available" not in a


def related_licences(rows):
    """Other licences in the same state that share this one's group, holder or
    premises. Shared holder skips individuals: two hemp growers called John Smith
    are not the same person. Each relation is capped, with the true total kept."""
    keys = {
        "same group": lambda r: r.get("group_id") or r.get("linked_group") or "",
        "same holder": lambda r: "" if r.get("holder_is_individual") == "Y"
                                 else norm_name(r.get("legal_name") or ""),
        "same address": lambda r: r["street_address"].strip().lower()
                                  if usable_address(r.get("street_address") or "") else "",
    }
    out = collections.defaultdict(list)
    for relation, key in keys.items():
        groups = collections.defaultdict(list)
        for r in rows:
            k = key(r)
            if k:
                groups[k].append(r)
        for members in groups.values():
            if len(members) < 2:
                continue
            for r in members:
                others = [m for m in members if m["licence_id"] != r["licence_id"]]
                out[r["licence_id"]].append({
                    "relation": relation, "total": len(others),
                    "licences": [{"licence_id": m["licence_id"],
                                  "name": m.get("dba") or m.get("legal_name") or "",
                                  "standard_type": m.get("standard_type", ""),
                                  "standard_status": m.get("standard_status", ""),
                                  "town": m.get("town", "")}
                                 for m in others[:RELATED_CAP]]})
    return out


def is_unverified(row):
    verdict = (row.get("audit_verdict") or "").strip().lower()
    flag = (row.get("needs_verify") or "").strip().lower()
    return verdict.startswith(UNVERIFIED) or flag in ("true", "yes", "y")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    licences = []
    for name in TABLES:
        licences.extend(rows_of(name))
    for col in PRIVATE:
        if col in LICENCE_PUBLIC or col in BUSINESS_PUBLIC:
            sys.exit(f"a private column is in an allowlist: {col}")

    if not args.dry_run and (OUT / "licences").exists():
        shutil.rmtree(OUT / "licences")   # stale state files must not survive

    bytes_written = collections.Counter()
    by_state = collections.defaultdict(list)
    for r in licences:
        by_state[r["state"]].append(r)

    summary = {"generated_from": "data/clean/*_licences.csv", "states": {}}
    county_names = us_map.county_display_names()
    for state, rows in sorted(by_state.items()):
        bytes_written["licences (list)"] += write(
            OUT / "licences" / f"{state}.json",
            {"state": state, "count": len(rows),
             "licences": [public(r, LICENCE_LIST) for r in rows]}, args.dry_run)
        # The full public record, in small buckets so a profile page or a detail
        # panel loads ~300 records, not California's 21,000.
        nb = buckets_for(len(rows))
        shards = collections.defaultdict(list)
        related = related_licences(rows)
        for r in rows:
            rec = public(r, LICENCE_PUBLIC)
            if related.get(r["licence_id"]):
                rec["related"] = related[r["licence_id"]]
            shards[bucket(r["licence_id"], nb)].append(rec)
        for b in range(nb):
            bytes_written["licences (detail)"] += write(
                OUT / "licences" / "detail" / state / f"{b}.json",
                {"state": state, "bucket": b, "of": nb, "licences": shards.get(b, [])},
                args.dry_run)
        types = collections.Counter(r["standard_type"] for r in rows if r["standard_type"])
        statuses = collections.Counter(r["standard_status"] for r in rows if r["standard_status"])
        counties = collections.Counter(r["county"] for r in rows if r["county"])
        asof = sorted({r["data_as_of"] for r in rows if r["data_as_of"]})
        summary["states"][state] = {
            "licences": len(rows),
            "detail_buckets": nb,
            "with_a_licence_number": sum(1 for r in rows if not r["licence_id"].startswith(state + "-")),
            "standard_type": dict(types.most_common()),
            "standard_status": dict(statuses.most_common()),
            "default_search_set": sum(1 for r in rows
                                      if r["standard_status"] in ("Active", "Provisional")),
            "counties": len(counties),
            "by_county": dict(counties.most_common()),
            # What a reader sees: "Baltimore City", "Winchester City", "Orleans Parish".
            "county_names": {c: county_names.get((state, c), c) for c in counties},
            "towns_by_county": {c: dict(collections.Counter(
                r["town"] for r in rows if r["county"] == c and r["town"]).most_common())
                for c in counties},
            "rows_without_a_county": sum(1 for r in rows if not r["county"]),
            "programs": dict(collections.Counter(
                r["program"] for r in rows if r["program"]).most_common()),
            # The state's own licence names, which HANDOFF wants shown on a
            # state page in preference to the standard type.
            "licence_types_as_the_state_names_them": dict(collections.Counter(
                r["licence_type"] for r in rows if r["licence_type"]).most_common()),
            # Never one number: these are different measures on different dates.
            "data_as_of": asof[0] if len(asof) == 1 else {"earliest": asof[0], "latest": asof[-1]},
            "sources": sorted({r["source"] for r in rows if r["source"]})[:12],
        }

    biz = rows_of("businesses_master.csv")
    primaries = [r for r in biz if r["is_primary_profile"] == "Y"]
    publishable = [r for r in primaries if not is_unverified(r)]
    held_back = [r for r in primaries if is_unverified(r)]
    bytes_written["businesses"] = write(
        OUT / "businesses.json",
        {"note": "primary profiles only, and only entries the audit did not leave unverified",
         "count": len(publishable),
         "businesses": [public(r, BUSINESS_PUBLIC) for r in publishable]}, args.dry_run)
    # Kept, not dropped, so the number is visible and nothing is lost.
    bytes_written["businesses_held_back"] = write(
        OUT / "businesses_unverified.json",
        {"note": "NOT FOR THE PUBLIC SITE — CLAUDE.md: unverified entries stay off the public "
                 "site until checked. Built so the count is visible and the entries are not lost.",
         "count": len(held_back),
         "businesses": [public(r, BUSINESS_PUBLIC) for r in held_back]}, args.dry_run)

    summary["businesses"] = {
        "directory_entries": len(biz),
        "profiles": len(primaries),
        "publishable": len(publishable),
        "held_back_unverified": len(held_back),
        "by_category": dict(collections.Counter(r["category"] for r in publishable).most_common()),
    }
    summary["totals"] = {
        "licences": len(licences),
        "jurisdictions_with_licence_data": len(by_state),
        "licences_with_a_county": sum(1 for r in licences if r["county"]),
    }
    bytes_written["summary"] = write(OUT / "summary.json", summary, args.dry_run)

    legal = rows_of("legal_status.csv")
    if len(legal) != 51:
        sys.exit(f"legal_status.csv has {len(legal)} rows, not 51 — "
                 "run python3 scripts/build_legal_status.py")
    bytes_written["legal_status"] = write(
        OUT / "legal_status.json",
        {"note": "Each status restates section 1.1 of that jurisdiction's audited report; "
                 "report_last_audited is the date the law was checked.",
         "states": {r["state"]: public(r, LEGAL_PUBLIC) for r in legal}}, args.dry_run)
    geo = us_map.build({r["state_name"]: r["state"] for r in legal})
    bytes_written["us_map"] = write(OUT / "us_map.json", geo, args.dry_run)
    # One county map per state. A county value with no shape (a premises outside
    # its licensing state, already flagged on the row) is listed, never drawn.
    county_maps = us_map.counties({s["fips"]: s["code"] for s in geo["states"]})
    unmatched = collections.Counter()
    for code, cm in county_maps.items():
        drawn = {c["county"] for c in cm["counties"]}
        st = summary["states"].get(code)
        if st:
            unmatched.update({(code, c): n for c, n in st["by_county"].items() if c not in drawn})
        bytes_written["county maps"] += write(OUT / "counties" / f"{code}.json", cm, args.dry_run)
    if unmatched:
        print(f"  {sum(unmatched.values())} licence rows in {len(unmatched)} county values have no "
              f"shape in their own state (premises outside the licensing state); listed, not drawn")

    print(f"{len(licences):,} licence rows -> {len(by_state)} per-state files")
    print(f"{len(primaries):,} business profiles -> {len(publishable):,} publishable, "
          f"{len(held_back):,} held back as unverified")
    for k, n in bytes_written.most_common():
        print(f"  {k:24} {n:>12,} bytes")
    extra = [c for c in LICENCE_LIST if c not in LICENCE_PUBLIC]
    if extra:
        sys.exit(f"LICENCE_LIST is not a subset of LICENCE_PUBLIC: {extra}")
    print(f"\n  allowlisted: {len(LICENCE_PUBLIC)} licence columns of 43 "
          f"({len(LICENCE_LIST)} of them in the list view), "
          f"{len(BUSINESS_PUBLIC)} business columns of 32")
    print(f"  private columns asserted absent: {', '.join(PRIVATE)}")
    if args.dry_run:
        print("\n(nothing written)")


if __name__ == "__main__":
    main()
