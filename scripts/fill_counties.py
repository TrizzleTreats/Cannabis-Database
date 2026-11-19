#!/usr/bin/env python3
"""Fill the county column from official sources. CLAUDE.md requires a county on
every row, and 4,039 of 50,544 rows have none because their regulator does not
publish one.

Two sources, both official, neither guessed:
  1. The US Census geocoder (geocoding.geo.census.gov, no key) resolves a full
     street address to its county. This is address-level, so it is safe for the
     township states HANDOFF warns about — Ohio, Michigan, Indiana, Illinois,
     Minnesota, North Dakota, New Jersey and Pennsylvania all have towns whose
     names repeat across counties, and a name-only lookup would mis-assign them.
  2. New Jersey's CRC Government Relations table, already in data/raw/, lists
     County against Municipality for every NJ municipality. That is the
     regulator's own pairing, so NJ rows are filled from it rather than guessed.

Results are cached in data/raw/census_county_lookup.csv so a re-run costs
nothing and the provenance stays on disk.

Usage:
  python3 scripts/fill_counties.py --geocode      # build/extend the cache
  python3 scripts/fill_counties.py --apply        # write counties into the tables
"""
import argparse, collections, csv, html, os, pathlib, re, ssl, sys, time
import urllib.error, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
TABLES = ["new_england_licences.csv", "mid_atlantic_licences.csv", "regions_3_to_9_licences.csv"]
CACHE = ROOT / "data" / "raw" / "census_county_lookup.csv"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
GEOCODER = "https://geocoding.geo.census.gov/geocoder/geographies/address"
# Pinned so a later re-run is comparable rather than silently different.
BENCHMARK, VINTAGE = "Public_AR_Current", "Current_Current"


def ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    # macOS keeps its bundle at the first two; Debian/Ubuntu (a CI runner) at the third.
    for ca in ("/etc/ssl/cert.pem", "/private/etc/ssl/cert.pem",
               "/etc/ssl/certs/ca-certificates.crt"):
        if os.path.exists(ca):
            return ssl.create_default_context(cafile=ca)
    sys.exit("no CA bundle found - refusing to fetch without certificate verification")


CTX = ssl_context()


def rows_of(name):
    with open(ROOT / "data/clean" / name, encoding="utf-8") as f:
        return list(csv.DictReader(f)), None


def split_street(addr, town):
    """The street part of 'N Something St, Town, ST, 12345'."""
    a = re.sub(r"\s+", " ", (addr or "").strip())
    if not a:
        return ""
    first = a.split(",")[0].strip()
    # Some states write the town into the same comma field as the street.
    if town and first.lower().endswith(town.lower()):
        first = first[: -len(town)].strip(" ,")
    return first


def needs_county(r):
    return not r["county"].strip()


def geocodable(r):
    return bool(re.match(r"^\s*\d", r["street_address"] or "")) and bool(r["town"].strip())


ADDRESS_STATE = re.compile(r",\s*([A-Z]{2})\s*,\s*\d+\s*$")


def premises_state(r):
    """The state the PREMISES are in, which is not always the licensing state.

    Connecticut's hemp-consumables credential is held by manufacturers in other
    states, so a CT row can carry a Minnesota address. Geocoding it as "4811
    Dusharme Dr, Brooklyn Center, CT" returns no match, and that no-match was
    being recorded as though the address were unfindable, when asking about
    Minnesota finds it immediately. The address's own state wins when it states
    one; the licensing state is the fallback.
    """
    found = ADDRESS_STATE.search((r["street_address"] or "").strip())
    return found.group(1) if found else r["state"]


def key_of(r):
    return "|".join((split_street(r["street_address"], r["town"]), r["town"].strip(),
                     premises_state(r)))


def drop_gap_note(r):
    """Remove any "county unavailable=" note from a row that now has a county.

    A row cannot both carry a county and say its county is unavailable, and 107
    rows did: the county arrived later from a different source (the ACS2021 town
    map, or a re-geocode) while the earlier no-match note stayed behind. That is
    exactly the placeholder-as-published-value CLAUDE.md forbids, and it reads
    as a live caveat on a value that no longer needs one.
    """
    if not r["extra_details"]:
        return
    r["extra_details"] = "; ".join(x for x in r["extra_details"].split("; ")
                                   if not x.startswith("county unavailable="))


def set_county(r, county, source):
    """Set a county, its source, and clear any stale gap note together."""
    r["county"], r["county_source"] = county, source
    drop_gap_note(r)


def load_cache():
    if not CACHE.exists():
        return {}
    with open(CACHE, encoding="utf-8") as f:
        return {r["key"]: r for r in csv.DictReader(f)}


def save_cache(cache):
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["key", "street", "town", "state", "county",
                                          "county_subdivision", "matched_address", "status",
                                          "fetched_at"])
        w.writeheader()
        for k in sorted(cache):
            # Rows cached before county_subdivision existed simply have none.
            w.writerow({f: cache[k].get(f, "") for f in w.fieldnames})


def geocode_full(street, town, state):
    """(county, county_subdivision, matched_address, status).

    The County Subdivisions layer is what makes Connecticut tractable. CT's
    county-equivalents are Planning Regions since 2022, so the Counties layer
    returns "Naugatuck Valley Planning Region" — a vocabulary this project does
    not use. The same response names the county subdivision, "Plymouth town",
    which IS a Connecticut town and so can be mapped to a traditional county
    through the ACS2021 table. It also resolves a village or borough to the
    municipality that contains it, at address level: "15 Container Dr,
    Terryville" is in Plymouth, and two Cornwall Bridge addresses turn out to
    sit in different towns, Cornwall and Sharon, either side of the Housatonic.
    """
    q = urllib.parse.urlencode({"street": street, "city": town, "state": state,
                                "benchmark": BENCHMARK, "vintage": VINTAGE, "format": "json"})
    req = urllib.request.Request(f"{GEOCODER}?{q}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
        import json
        d = json.loads(r.read().decode("utf-8", "replace"))
    m = (d.get("result") or {}).get("addressMatches") or []
    if not m:
        return "", "", "", "no match"
    g = m[0].get("geographies") or {}
    counties = g.get("Counties") or []
    name = (counties[0].get("NAME") if counties else "") or ""
    # Census writes "El Paso County"; the tables hold the bare name.
    name = re.sub(r"\s+(County|Parish|Borough|Census Area|Municipality|City and Borough)$", "", name)
    subs = g.get("County Subdivisions") or []
    sub = (subs[0].get("NAME") if subs else "") or ""
    return name, sub, m[0].get("matchedAddress", ""), "ok" if name else "matched but no county"


def geocode(street, town, state):
    """(county, matched_address, status) — the long-standing three-value form."""
    county, _sub, matched, status = geocode_full(street, town, state)
    return county, matched, status


CT_SUBDIVISION = re.compile(r"\s+(town|city|borough)$", re.I)


def ct_town_of(subdivision):
    """"Plymouth town" -> "plymouth", the key ct_town_counties() uses."""
    return CT_SUBDIVISION.sub("", (subdivision or "").strip()).strip().lower()


NJ_SUFFIX = re.compile(r"\s+(twp|township|boro|borough|city|town|village)\.?$", re.I)


def nj_variants(name):
    """CRC and the licence list spell the same municipality differently —
    'Egg Harbor Township' against 'egg harbor twp' — so compare on a few
    normalised forms. CRC also contains at least one typo ('egg habor city')."""
    n = re.sub(r"[^a-z0-9 ]", "", name.strip().lower())
    n = re.sub(r"\s+", " ", n)
    out = [n]
    bare = NJ_SUFFIX.sub("", n).strip()
    if bare and bare != n:
        out.append(bare)
    for suf in ("twp", "township", "boro", "borough", "city", "town"):
        out.append(f"{bare or n} {suf}")
    return out


def nj_municipality_counties():
    """County against Municipality, from the CRC's own Government Relations table."""
    path = ROOT / "data/raw/new-jersey/crc_government_relations_2026-11-12.html"
    if not path.exists():
        return {}
    t = path.read_text(errors="replace")
    out, county = {}, ""
    for tr in re.findall(r"<tr.*?</tr>", t, re.S | re.I):
        cells = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", c))).strip()
                 for c in re.findall(r"<t[dh].*?</t[dh]>", tr, re.S | re.I)]
        if len(cells) < 2:
            continue
        # The table repeats the county in its first column, sometimes blank on
        # continuation rows, so the last non-empty value carries forward.
        if cells[0]:
            county = cells[0]
        muni = cells[1]
        if county and muni and not re.match(r"(?i)^(county|municipality)$", muni):
            for v in nj_variants(muni):
                out.setdefault(v, county)
    return out


CT_TRADITIONAL = {"Fairfield", "Hartford", "Litchfield", "Middlesex",
                  "New Haven", "New London", "Tolland", "Windham"}


def ct_town_counties():
    """Connecticut's traditional eight counties, town by town.

    The project's decision (12 Nov 2026) is that Connecticut uses its
    traditional eight counties, not the nine Planning Regions that replaced
    them as Census county-equivalents in 2022. Current TIGER therefore cannot
    supply them, so the mapping comes from the Census ACS2021 vintage, the last
    one published before the change — an official source, just an older one.
    """
    path = ROOT / "data/raw/census_ct_town_county_2021.csv"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return {r["town"].strip().lower(): r["county"] for r in csv.DictReader(f)}


def independent_cities():
    """(state, basename) pairs that are both an independent city and a county."""
    path = ROOT / "data/raw/census_counties_by_state.csv"
    names = collections.defaultdict(set)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                names[(r["state"], r["county_basename"])].add(r["county_name"])
    return {k for k, v in names.items() if len(v) > 1}


def official_counties():
    path = ROOT / "data/raw/census_counties_by_state.csv"
    if not path.exists():
        return {}
    out = collections.defaultdict(set)
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[r["state"]].add(r["county_basename"])
            if r["county_name"].endswith(" city"):
                out[r["state"]].add(r["county_name"])
    return out


# Values regulators put in a county column that are not counties.
NOT_A_COUNTY = {"out of state/unknown", "out of state", "unknown", "private", "n/a", "na",
                "none", "various", "statewide", "other"}
# Documented renames and historical names regulators still use.
COUNTY_ALIAS = {("FL", "dade"): "Miami-Dade"}


def _fold(s):
    """St Lawrence / St. Lawrence / Saint Lawrence all fold together, and case
    folds too — so McLennan survives a title()-cased source."""
    s = s.lower().strip()
    s = re.sub(r"\bsaint\b", "st", s)
    s = re.sub(r"[^a-z0-9]", "", s)
    return s


def canonicalise(all_rows):
    """Rewrite each county to the Census spelling, blank the values that are not
    counties at all, and leave the genuinely foreign ones for validate() to flag.
    title() mangles Mc- names (McLennan -> Mclennan), and regulators spell
    St./Saint and independent cities their own way."""
    official = official_counties()
    if not official:
        print("county reference not built; fetch it first")
        return
    folded = {st: {_fold(c): c for c in cs} for st, cs in official.items()}
    fixed, blanked, left = collections.Counter(), collections.Counter(), collections.Counter()
    for name, rows in all_rows.items():
        changed = 0
        for r in rows:
            c = r["county"].strip()
            if not c:
                continue
            st = r["state"]
            if c.lower() in NOT_A_COUNTY:
                note = (f"county not published={r['county']} is a placeholder in the source, not a "
                        "county, so the county is left empty")
                r["county"], r["county_source"] = "", ""
                if "county not published=" not in r["extra_details"]:
                    r["extra_details"] = "; ".join(x for x in (r["extra_details"], note) if x)
                blanked[st] += 1
                changed += 1
                continue
            if c in official.get(st, set()) or (st == "CT" and c in CT_TRADITIONAL):
                continue
            # try the official spelling, with and without a trailing designator
            alias = COUNTY_ALIAS.get((st, _fold(c)))
            # "Baltimore City" and "St. Louis City" are independent cities;
            # TIGER carries them under the same basename as the county.
            stripped = re.sub(r"\s+(County|Parish|Borough|City and Borough|Census Area|"
                              r"Municipality|City)$", "", c, flags=re.I).strip()
            for cand in ([alias] if alias else []) + [c, stripped]:
                hit = folded.get(st, {}).get(_fold(cand))
                # Baltimore, St. Louis and four Virginia names are both an
                # independent city and a county. Stripping "City" would merge
                # them, so the city keeps Census's own "<name> city" form
                # (scripts/resolve_independent_cities.py explains the rule).
                if hit and re.search(r"\bcity$", c, re.I) and (st, hit) in independent_cities():
                    hit = f"{hit} city"
                if hit:
                    if hit != r["county"]:
                        r["county"] = hit
                        r["county_source"] = "; ".join(x for x in (
                            r["county_source"], "spelling normalised to the Census county name") if x)
                        fixed[st] += 1
                        changed += 1
                    break
            else:
                left[st] += 1
        if changed:
            cols = list(rows[0].keys())
            with open(ROOT / "data/clean" / name, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=cols)
                w.writeheader()
                for r in rows:
                    w.writerow({c2: r.get(c2, "") for c2 in cols})
            print(f"  {name}: {changed} counties rewritten")
    print("spelling normalised:", dict(fixed.most_common()))
    print("blanked as not-a-county placeholders:", dict(blanked.most_common()))
    print("still not a county of their state (validate() will flag):", dict(left.most_common()))


def validate(all_rows):
    """Flag any county that is not a county of its own state. Most are licences
    whose premises is in another state — Connecticut's hemp-consumables
    credential is held by manufacturers across the country — and the rest came
    from the 24 Oct 2026 table with no source recorded."""
    official = official_counties()
    if not official:
        print("county reference not built; run the TIGERweb fetch first")
        return
    where = collections.defaultdict(set)
    for st, cs in official.items():
        for c in cs:
            where[c].add(st)
    flagged, unresolved = collections.Counter(), collections.Counter()
    for name, rows in all_rows.items():
        changed = 0
        for r in rows:
            c = r["county"].strip()
            if not c or "premises outside the licensing state=" in r["extra_details"]:
                continue
            if r["state"] == "CT" and c in CT_TRADITIONAL:
                continue
            if c in official.get(r["state"], set()):
                continue
            elsewhere = sorted(where.get(c, set()))
            if len(elsewhere) == 1:
                note = (f"premises outside the licensing state={c} is a county of {elsewhere[0]}, "
                        f"not {r['state']} — the licence is issued by {r['state']} but the premises "
                        f"is not, so leave it off a {r['state']} county map")
                flagged[r["state"]] += 1
            elif elsewhere:
                note = (f"county not valid for this state={c} is not a county of {r['state']}; it "
                        f"exists in {', '.join(elsewhere[:6])}. Inherited from the 24 Oct 2026 table "
                        f"with no source recorded — needs checking")
                unresolved[r["state"]] += 1
            else:
                note = (f"county not valid for this state={c} is not a county of any state in the "
                        f"Census list. Inherited from the 24 Oct 2026 table with no source recorded "
                        f"— needs checking")
                unresolved[r["state"]] += 1
            if note.split("=")[0] + "=" not in r["extra_details"]:
                r["extra_details"] = "; ".join(x for x in (r["extra_details"], note) if x)
                changed += 1
        if changed:
            cols = list(rows[0].keys())
            with open(ROOT / "data/clean" / name, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=cols)
                w.writeheader()
                for r in rows:
                    w.writerow({c2: r.get(c2, "") for c2 in cols})
            print(f"  {name}: {changed} rows flagged")
    print("resolved to another state:", dict(flagged.most_common()))
    print("still ambiguous or unknown:", dict(unresolved.most_common()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geocode", action="store_true"), ap.add_argument("--apply", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--canonicalise", action="store_true")
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    if not (a.geocode or a.apply or a.validate or a.canonicalise):
        ap.error("pass --geocode, --apply, --canonicalise or --validate")

    todo, all_rows = [], {}
    for name in TABLES:
        rows, _ = rows_of(name)
        all_rows[name] = rows
        for r in rows:
            if needs_county(r) and geocodable(r):
                todo.append(r)
    cache = load_cache()
    keys = []
    for r in todo:
        k = key_of(r)
        if k not in keys:
            keys.append(k)
    print(f"{len(todo)} county-less rows are geocodable, {len(keys)} distinct addresses, "
          f"{sum(1 for k in keys if k in cache)} already cached")

    if a.geocode:
        pending = [k for k in keys if k not in cache]
        # Entries cached before the County Subdivisions layer was read hold no
        # subdivision, and Connecticut's villages cannot be resolved without
        # one. Re-fetch just those rather than discarding a 2,700-entry cache.
        stale = [k for k in keys if k in cache and cache[k].get("status") == "ok"
                 and not cache[k].get("county_subdivision")]
        if stale:
            print(f"  {len(stale)} cached addresses predate the county-subdivision "
                  f"layer and will be re-fetched")
            pending = pending + stale
        if a.limit:
            pending = pending[: a.limit]
        print(f"geocoding {len(pending)} addresses against the Census geocoder "
              f"(benchmark {BENCHMARK}, vintage {VINTAGE})", flush=True)
        done = fail = 0
        for i, k in enumerate(pending, 1):
            street, town, state = k.split("|")
            try:
                county, sub, matched, status = geocode_full(street, town, state)
            except Exception as exc:
                county, sub, matched, status = "", "", "", f"error: {type(exc).__name__}"
            cache[k] = dict(key=k, street=street, town=town, state=state, county=county,
                            county_subdivision=sub, matched_address=matched, status=status,
                            fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
            done += 1 if county else 0
            fail += 0 if county else 1
            if i % 100 == 0 or i == len(pending):
                print(f"  {i}/{len(pending)}  matched {done}  unmatched {fail}", flush=True)
                save_cache(cache)
            time.sleep(0.25)
        save_cache(cache)
        print(f"cache now holds {len(cache)} addresses; {sum(1 for v in cache.values() if v['county'])} with a county")

    if a.apply:
        ct_towns = ct_town_counties()
        print(f"CT town->traditional county pairs (Census ACS2021): {len(ct_towns)}")
        nj = nj_municipality_counties()
        print(f"NJ municipality->county pairs from the CRC table: {len(nj)}")
        filled, unfilled = collections.Counter(), collections.Counter()
        contradictions = collections.Counter()
        for name, rows in all_rows.items():
            changed = 0
            for r in rows:
                revisit = r["county_source"].startswith("US Census geocoder")
                if not needs_county(r) and not revisit:
                    continue
                k = key_of(r)
                hit = cache.get(k)
                # Connecticut first: its county comes from the traditional-county
                # town map, never from the geocoder's Planning Region.
                if r["state"] == "CT" and r["town"].strip().lower() in ct_towns:
                    set_county(r, ct_towns[r["town"].strip().lower()],
                               "Census ACS2021 county subdivisions, matched on town — "
                               "Connecticut's traditional eight counties, the vocabulary "
                               "this project uses")
                    filled["CT"] += 1
                    changed += 1
                    continue
                # Connecticut is a special case. Census replaced CT's eight
                # counties with nine Planning Regions as county-equivalents in
                # 2022, so the geocoder returns e.g. "Capitol Planning Region".
                # The rest of the CT rows, and ct_towns.csv, carry the
                # traditional county names, and mixing the two vocabularies in
                # one column would be worse than leaving the gap visible.
                # A CT row whose place name is not a town — Terryville, Mystic,
                # Cornwall Bridge, Kensington, Baltic are villages and boroughs.
                # The geocoder's Counties layer is a Planning Region and unusable,
                # but the same response names the county SUBDIVISION, which is a
                # real CT town, and that maps to a traditional county. Resolved at
                # address level, so a village split across two towns is settled by
                # the address rather than assumed.
                if (r["state"] == "CT" and hit and hit.get("county_subdivision")
                        and ct_town_of(hit["county_subdivision"]) in ct_towns):
                    muni = CT_SUBDIVISION.sub("", hit["county_subdivision"].strip()).strip()
                    ct_county = ct_towns[ct_town_of(hit["county_subdivision"])]
                    # Deliberately NOT led by "US Census geocoder": the revisit
                    # rule below re-processes any row whose county_source starts
                    # that way, and this one is already settled. ACS2021 is also
                    # the more accurate lead — it is what supplies the county.
                    set_county(r, ct_county,
                               f"Census ACS2021 for Connecticut's traditional county, after the "
                               f"Census geocoder ({BENCHMARK}/{VINTAGE}) resolved the address to "
                               f"county subdivision '{hit['county_subdivision']}' — the geocoder's "
                               f"own Counties layer gives a Planning Region, which this project "
                               f"does not use")
                    if not r["location_basis"]:
                        r["location_basis"] = ("village or borough resolved to its containing "
                                               "municipality by address")
                    note = (f"municipality={muni}; place as listed={r['town']} is a village or "
                            f"borough rather than a Connecticut town")
                    if "municipality=" not in r["extra_details"]:
                        r["extra_details"] = "; ".join(x for x in (r["extra_details"], note) if x)
                    filled["CT"] += 1
                    changed += 1
                    continue
                if r["state"] == "CT" and hit and "Planning Region" in (hit["county"] or ""):
                    why = ("county unavailable=the Census geocoder returns Connecticut's post-2022 "
                           f"Planning Region ({hit['county']}) rather than a traditional county, and "
                           "the rest of the CT rows use traditional county names — filling this from "
                           "the geocoder would mix two vocabularies in one column")
                    if "county unavailable=" not in r["extra_details"]:
                        r["extra_details"] = "; ".join(x for x in (r["extra_details"], why) if x)
                        changed += 1
                    unfilled["CT"] += 1
                    continue
                if hit and hit["county"]:
                    set_county(r, hit["county"],
                               f"US Census geocoder ({BENCHMARK}/{VINTAGE}), "
                               f"matched {hit['matched_address']}")
                    # A licence can have premises in another state entirely —
                    # Connecticut's hemp-consumables credential is held by
                    # manufacturers in Buffalo, Atlanta, Bend and Chattanooga.
                    # The county is right for the premises but belongs to
                    # another state, so a state county map must exclude it.
                    ms = re.search(r",\s*([A-Z]{2}),\s*\d{5}", hit["matched_address"] or "")
                    if ms and ms.group(1) != r["state"]:
                        note = (f"premises outside the licensing state=the address geocodes to "
                                f"{ms.group(1)}, so this county ({hit['county']}) is not in "
                                f"{r['state']} and must be left off a {r['state']} county map")
                        if "premises outside the licensing state=" not in r["extra_details"]:
                            r["extra_details"] = "; ".join(x for x in (r["extra_details"], note) if x)
                    if needs_county(r) or not revisit:
                        filled[r["state"]] += 1
                    changed += 1
                elif r["state"] == "NJ" and any(v in nj for v in nj_variants(r["town"])):
                    set_county(r, next(nj[v] for v in nj_variants(r["town"]) if v in nj),
                               "NJ CRC Government Relations table (County against Municipality)")
                    filled["NJ"] += 1
                    changed += 1
                elif r["county"]:
                    # Reached on a revisit: the row already has a county that
                    # this pass did not improve on, so there is no gap to
                    # explain. Writing a "county unavailable" note here is what
                    # put a live caveat on 107 settled values.
                    pass
                else:
                    # Say WHY a county is still missing, so a blank is never
                    # mistaken for an oversight.
                    if not geocodable(r) and not r["town"].strip():
                        why = ("county unavailable=no town or street address is published for this "
                               "licence, so no county can be resolved")
                    elif r["state"] == "NJ":
                        why = ("county unavailable=this town is not in the CRC's Government Relations "
                               "municipality table — it is likely an unincorporated place inside a "
                               "township rather than a municipality, and no street address is published")
                    elif not geocodable(r):
                        why = ("county unavailable=only a town is published, and a name-only lookup is "
                               "unsafe here because town names repeat across counties")
                    else:
                        hit2 = cache.get(k)
                        why = ("county unavailable=the Census geocoder returned "
                               f"{(hit2 or {}).get('status', 'no result')} for this address")
                    if "county unavailable=" not in r["extra_details"]:
                        r["extra_details"] = "; ".join(x for x in (r["extra_details"], why) if x)
                        changed += 1
                    unfilled[r["state"]] += 1
            # A row that HAS a county must not also say its county is
            # unavailable. 107 did, because the county arrived later from a
            # different source while the earlier no-match note stayed behind.
            # Swept here rather than only at the fill sites, because a row
            # already holding a county is never revisited by the fill.
            for r in rows:
                if r["county"] and "county unavailable=" in r["extra_details"]:
                    drop_gap_note(r)
                    contradictions[r["state"]] += 1
                    changed += 1
            if changed:
                cols = list(rows[0].keys())
                with open(ROOT / "data/clean" / name, "w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=cols)
                    w.writeheader()
                    for r in rows:
                        w.writerow({c: r.get(c, "") for c in cols})
                print(f"  {name}: {changed} counties filled")
        # Counties carried over from the 24 Oct 2026 table arrived with no
        # source recorded. CLAUDE.md wants a source on every fact, so say
        # plainly where they came from rather than leaving the field blank.
        carried = collections.Counter()
        for name, rows in all_rows.items():
            n = 0
            for r in rows:
                if r["county"] and not r["county_source"]:
                    r["county_source"] = ("carried forward from the 24 Oct 2026 New England table; "
                                          "its own source was not recorded")
                    carried[r["state"]] += 1
                    n += 1
            if n:
                cols = list(rows[0].keys())
                with open(ROOT / "data/clean" / name, "w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=cols)
                    w.writeheader()
                    for r in rows:
                        w.writerow({c: r.get(c, "") for c in cols})
        if carried:
            print("county_source back-filled for carried-forward rows:", dict(carried.most_common()))

        print("\nfilled by state:", dict(filled.most_common()))
        # Counted from the rows themselves, not accumulated during the walk: a
        # row whose county_source invites a revisit passes through the unfilled
        # branch on every run even when it already has a county, which made
        # Connecticut read as 24 gaps when it had 5.
        unfilled = collections.Counter(
            r["state"] for rows in all_rows.values() for r in rows if not r["county"])
        print("total filled:", sum(filled.values()))
        print("still without a county (each row now says why):", dict(unfilled.most_common()))
        print("total still without:", sum(unfilled.values()))
        if contradictions:
            print(f"stale 'county unavailable' notes cleared from rows that now have a "
                  f"county: {dict(contradictions)} (total {sum(contradictions.values())})")


    if a.canonicalise:
        canonicalise(all_rows)
    if a.validate:
        validate(all_rows)


if __name__ == "__main__":
    main()
