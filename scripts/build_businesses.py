#!/usr/bin/env python3
"""Build data/clean/businesses_master.csv from the audited business directories.

Two of the eleven directories (national, New England) were parsed in the
earlier chat and are already in the file. The other nine are still HTML in
reports/businesses/, and each was laid out differently by whoever produced it:

  * six are category tables  — great-lakes, plains, mountain, southwest,
    south-central, pacific
  * two are per-entry blocks — mid-atlantic, southeast  (<div class="entry">)
  * one is heading-per-entry — california

The table directories differ in their column names but not in what the columns
mean, so headers are matched to schema fields by pattern rather than with a
hand-written map per file. A header that matches nothing is reported, never
silently dropped.

Usage: python3 scripts/build_businesses.py [--dry-run] [--only great-lakes]
"""
import argparse, collections, csv, html, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "reports" / "businesses"
OUT = ROOT / "data" / "clean" / "businesses_master.csv"
TODAY = "2026-11-12"

# file stem -> (region label, id prefix)
TABLE_DIRS = {
    "great-lakes-businesses-audited": ("Great Lakes", "GL"),
    "plains-businesses-audited": ("Plains", "PL"),
    "mountain-businesses-audited": ("Mountain", "MT"),
    "southwest-businesses-audited": ("Southwest", "SW"),
    "south-central-businesses-audited": ("South Central", "SC"),
    "pacific-businesses-audited-or-wa-ak-hi": ("Pacific (OR/WA/AK/HI)", "PAC"),
}

# header text -> schema field. First match wins, so order matters.
HEADER_MAP = [
    (r"^business\b.*standard", ["business_name", "category"]),   # pacific packs two in one
    (r"^business\b|^firm\b|^company\b|^name\b", ["business_name"]),
    (r"sub-?type", ["sub_type"]),
    (r"standard categ|^category\b", ["category"]),
    (r"^state\b|home state", ["home_state"]),
    (r"^scope\b|^scale\b", ["scope"]),
    # Anchored: an unanchored match steals "What they provide for cannabis/hemp
    # clients", which is a description, not the cannabis/hemp tag.
    (r"^cannabis\s*/\s*hemp", ["cannabis_focus"]),
    (r"what they do|what they provide|services|descript|products", ["description"]),
    (r"contact|website|phone|email", ["contact_as_published"]),
    (r"^address\b|^social\b", ["address"]),
    (r"states served", ["states_served"]),
    (r"key people", ["key_people_private"]),
    (r"evidence", ["evidence_links"]),
    (r"credential|licen", ["credentials"]),
    (r"verdict", ["audit_verdict"]),
    (r"audit note|audit verdict & note|^note", ["audit_note"]),
    (r"source", ["sources"]),
    (r"disposition", ["audit_note"]),
]
# tables that are tallies or audit logs rather than the directory itself
SKIP_HEADER = re.compile(r"(?i)^(category|business)$")
TALLY = re.compile(r"(?i)confirmed.*corrected.*unverified|what was checked")


ENTITY = re.compile(r"&(?:[a-zA-Z]+|#\d+);")


def txt(s):
    """Visible text. Unescapes until stable, because one report is double-escaped.

    california-businesses-audited.html carries 59 instances of "&amp;amp;", so a
    single pass leaves "&amp;" and publishes a business name reading "Sheppard,
    Mullin, Richter &amp; Hampton LLP". No directory text is meant to display a
    literal entity, so repeating the unescape is safe; it is capped so a
    pathological value cannot loop.
    """
    out = re.sub(r"<[^>]+>", " ", s)
    for _ in range(3):
        once = html.unescape(out)
        if once == out or not ENTITY.search(once):
            out = once
            break
        out = once
    return re.sub(r"\s+", " ", out).strip()


def cells(tr):
    return [txt(c) for c in re.findall(r"<t[dh].*?</t[dh]>", tr, re.S | re.I)]


def links(cell_html):
    return [html.unescape(u) for u in re.findall(r'href="(https?://[^"]+)"', cell_html, re.I)]


def map_headers(hdr):
    """schema field -> column index, plus the headers nothing matched."""
    out, unmapped = {}, []
    for i, h in enumerate(hdr):
        hl = h.lower()
        for pat, fields in HEADER_MAP:
            if re.search(pat, hl):
                for f in fields:
                    out.setdefault(f, i)
                break
        else:
            if h:
                unmapped.append(h)
    return out, unmapped


def split_contact(value):
    """'W: site.com P: 555-1234 E: a@b.com' -> website, phone, email."""
    v = value or ""
    email = (re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", v) or [None])
    email = email.group(0) if hasattr(email, "group") else ""
    phone = re.search(r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", v)
    site = re.search(r"(?:https?://)?(?:www\.)?[\w-]+\.(?:com|org|net|io|co|us|law|health|shop)"
                     r"(?:/[^\s,;]*)?", v)
    return (site.group(0) if site else "", phone.group(0) if phone else "", email)


def category_for(pos, headings):
    """The nearest Category heading above this table."""
    best = ""
    for off, text in headings:
        if off < pos:
            best = text
        else:
            break
    return best


def parse_table_directory(stem, region, prefix, warn):
    path = SRC / f"{stem}.html"
    s = path.read_text(errors="replace")
    headings = [(m.start(), txt(m.group(1)))
                for m in re.finditer(r"<h[2-4][^>]*>(.*?)</h[2-4]>", s, re.S | re.I)
                if re.match(r"(?i)^categor", txt(m.group(1)))]
    tables = [(m.start(), m.group(0)) for m in re.finditer(r"<table.*?</table>", s, re.S | re.I)]
    # the directory tables are the ones sharing the most common header shape
    shapes = collections.Counter()
    for _, tb in tables:
        rs = re.findall(r"<tr.*?</tr>", tb, re.S | re.I)
        if rs:
            shapes[tuple(cells(rs[0]))] += 1
    if not shapes:
        return []
    main_hdr, _ = shapes.most_common(1)[0]
    fields, unmapped = map_headers(list(main_hdr))
    if unmapped:
        warn.append((f"{stem}: headers not mapped", "; ".join(unmapped)[:90]))
    if "business_name" not in fields:
        warn.append((f"{stem}: no business-name column", str(list(main_hdr))[:90]))
        return []
    rows, n = [], 0
    for pos, tb in tables:
        trs = re.findall(r"<tr.*?</tr>", tb, re.S | re.I)
        if not trs or tuple(cells(trs[0])) != main_hdr:
            continue
        cat_heading = category_for(pos, headings)
        for tr in trs[1:]:
            raw = re.findall(r"<t[dh].*?</t[dh]>", tr, re.S | re.I)
            c = [txt(x) for x in raw]
            if not c or not c[fields["business_name"]].strip():
                continue
            if TALLY.search(" ".join(c[:3])):
                continue
            n += 1
            get = lambda f: (c[fields[f]] if f in fields and fields[f] < len(c) else "")
            name, cat = get("business_name"), get("category")
            sub, focus, scope_v = get("sub_type"), get("cannabis_focus"), get("scope")
            verdict_inline = ""
            # Pacific writes everything into one "Business / Standard category"
            # cell with inline labels: "Gleam Law Sub-type: ... Scope: ...".
            if re.search(r"(?i)(sub-?type|standard category|scope)\s*:", name):
                def label(field, blob):
                    mm = re.search(rf"(?i){field}\s*:\s*(.*?)(?=\s+(?:sub-?type|standard category|"
                                   rf"scope|cannabis\s*/\s*hemp|audit verdict|verdict)\s*:|$)", blob)
                    return mm.group(1).strip(" ;,") if mm else ""
                blob = name
                sub = sub or label("sub-?type", blob)
                cat = cat if cat and ":" not in cat else label("standard category", blob)
                scope_v = scope_v or label("scope", blob)
                focus = focus or label(r"cannabis\s*/\s*hemp", blob)
                verdict_inline = label(r"audit verdict", blob) or label(r"verdict", blob)
                name = re.split(r"(?i)\s+(?:sub-?type|standard category|scope|audit verdict)\s*:",
                                blob)[0].strip()
            # Plains packs "Standard category; sub-type; cannabis/hemp tag" into one.
            elif cat.count(";") >= 2 and not (sub and focus):
                parts = [x.strip() for x in cat.split(";")]
                cat, sub, focus = parts[0], sub or parts[1], focus or parts[-1]
            if "—" in name and not cat:
                name, _, cat = name.partition("—")
            site, phone, email = split_contact(get("contact_as_published"))
            all_links = [u for x in raw for u in links(x)]
            row = {
                "business_id": f"{prefix}-{n:03d}", "region": region, "scope": scope_v,
                "home_state": get("home_state"), "category_no": "", "category": cat or cat_heading,
                "entry_no": "", "business_name": name.strip(),
                "needs_verify": "True" if re.search(
                    r"(?i)unverified", " ".join((get("audit_verdict"), get("audit_note"),
                                                 verdict_inline))) else "False",
                "audit_verdict": get("audit_verdict") or verdict_inline, "sub_type": sub,
                "cannabis_focus": focus, "description": get("description"),
                "website": site, "phone": phone, "email": email, "address": get("address"),
                "contact_as_published": get("contact_as_published"),
                "states_served": get("states_served"), "states_served_codes": "",
                "key_people_private": get("key_people_private"),
                "evidence_of_cannabis_work": get("evidence_links"),
                "evidence_links": "; ".join(dict.fromkeys(all_links))[:900],
                "credentials": get("credentials"), "audit_note": get("audit_note"),
                "sources": get("sources"), "last_checked": TODAY,
            }
            rows.append(row)
    return rows


ENTRY_DIRS = {
    "mid-atlantic-businesses-audited": ("Mid-Atlantic", "MA2"),
    "southeast-businesses-audited": ("Southeast", "SE"),
}
# <strong>Label:</strong> value  ->  schema field
LABEL_MAP = {
    "standard category": "category", "sub-type": "sub_type", "subtype": "sub_type",
    "scale": "scope", "tag": "scope", "scope": "scope",
    "cannabis / hemp tag": "cannabis_focus", "cannabis-only/general": "cannabis_focus",
    "cannabis/hemp tag": "cannabis_focus",
    "description": "description", "what it is": "description",
    "website": "website", "phone": "phone", "email": "email", "address": "address",
    "social": "address", "states served & scope": "states_served",
    "states served": "states_served", "owners/key people": "key_people_private",
    "key people": "key_people_private", "evidence of cannabis work": "evidence_of_cannabis_work",
    "credentials": "credentials", "source link": "sources", "verdict": "audit_verdict",
    "verdict in audit": "audit_verdict", "licence number": "credentials",
    "name/dba": "dba_note", "state cannabis-operator licence": "credentials",
    "parent": "parent_note", "category note": "audit_note", "entity-name note": "audit_note",
    "original category": "category", "what to do with it": "audit_note",
    "owners/key people": "key_people_private", "cannabis-only/general": "cannabis_focus",
}
# A bare <strong>Unverified</strong> is a verdict, not a label.
BARE_VERDICT = re.compile(r"(?i)^(confirmed|corrected|unverified|removed|moved out)\b")


# Southeast writes its detail as running prose with plain-text labels rather
# than <strong> ones: "Website: ... Phone: ... Key people: ... Evidence: ...".
PLAIN_LABELS = {
    "website": "website", "phone": "phone", "email": "email", "address": "address",
    "socials": "address", "phone/email/address/socials": "contact_as_published",
    "states served": "states_served", "states": "states_served",
    "key people": "key_people_private", "evidence": "evidence_of_cannabis_work",
    "credentials": "credentials", "flags": "audit_note", "scale": "scope", "tag": "cannabis_focus",
    "standard category": "category",
}
PLAIN_RE = re.compile(r"(?i)\b(" + "|".join(sorted((re.escape(k) for k in PLAIN_LABELS),
                                                   key=len, reverse=True)) + r")\s*:\s*")


def plain_labelled(text_blob):
    """Pull 'Label: value' pairs out of running prose, each value ending where
    the next known label begins."""
    out = collections.defaultdict(list)
    hits = list(PLAIN_RE.finditer(text_blob))
    for i, m in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(text_blob)
        val = text_blob[m.end():end].strip(" .;|")
        field = PLAIN_LABELS.get(m.group(1).lower())
        if field and val and not re.match(r"(?i)^not published", val):
            out[field].append(val)
    return out


def parse_entry_directory(stem, region, prefix, warn):
    """Directories built as one block per business: <div|article class="entry">
    with an <h3> name, a meta line, and <strong>Label:</strong> value paragraphs."""
    s = (SRC / f"{stem}.html").read_text(errors="replace")
    blocks = re.findall(r'<(?:div|article) class="entry[^"]*">(.*?)</(?:div|article)>',
                        s, re.S | re.I)
    rows, unmapped, moved_out = [], collections.Counter(), []
    for i, b in enumerate(blocks, 1):
        hm = re.search(r"<h[34][^>]*>(.*?)</h[34]>", b, re.S | re.I)
        if not hm:
            continue
        name = txt(hm.group(1))
        # the heading sometimes carries the verdict: "Talaria — MOVED OUT"
        heading_note = ""
        if " — " in name:
            head, _, tail = name.rpartition(" — ")
            if tail.isupper() or re.match(r"(?i)^(moved out|removed|closed)", tail):
                name, heading_note = head.strip(), tail.strip()
        vals = collections.defaultdict(list)
        body = b[hm.end():]          # the heading itself can contain <strong>
        for m in re.finditer(r"<strong>(.*?)</strong>\s*(.*?)(?=<strong>|</p>|$)", body, re.S | re.I):
            lab = txt(m.group(1)).rstrip(":").lower()
            lab = re.sub(r"\s*/\s*", "/", lab)       # "name / dba" -> "name/dba"
            if BARE_VERDICT.match(lab) and lab not in LABEL_MAP:
                vals["audit_verdict"].append(txt(m.group(1)).rstrip("."))
                continue
            val = txt(m.group(2)).lstrip(": ").strip(" |")
            field = LABEL_MAP.get(lab)
            if not field:
                # "Verdict: Unverified." style, where the verdict is in the label
                vm = re.match(r"(?i)verdict\s*:?\s*(.+)", lab)
                if vm:
                    field, val = "audit_verdict", vm.group(1)
                else:
                    unmapped[lab[:34]] += 1
                    continue
            if val:
                vals[field].append(val)
        # Fill anything the <strong> labels did not carry from the prose.
        for field, vs in plain_labelled(txt(body)).items():
            if not vals.get(field):
                vals[field] = vs
        if not vals and not name:
            continue
        g = lambda f: "; ".join(dict.fromkeys(vals.get(f, [])))[:900]
        # Most entries carry the verdict as a badge span rather than a label:
        # <span class="badge badge-Confirmed">Confirmed</span>
        # Scope the badge to the entry's own meta line: a block can contain
        # further badges deeper down that belong to sub-items, not the entry.
        meta = re.search(r'<p class="meta">(.*?)</p>', b, re.S | re.I)
        scope_html = meta.group(1) if meta else b
        badge = (re.search(r'class="[^"]*badge-([A-Za-z]+)"', scope_html)
                 or re.search(r'class="badge\s+(?!badge)([A-Za-z]+)"', scope_html)
                 or re.search(r'class="[^"]*badge-([A-Za-z]+)"', b))
        verdict = g("audit_verdict") or (badge.group(1).title() if badge else "") or heading_note
        extra = "; ".join(x for x in (
            f"parent: {g('parent_note')}" if g("parent_note") else "",
            f"name/DBA note: {g('dba_note')}" if g("dba_note") else "",
            g("audit_note")) if x)
        # HANDOFF: a business holding a state or tribal cannabis licence belongs
        # in the licence database, not the directory. The audits mark those
        # "MOVED OUT"; keeping them here would double-count them.
        if re.match(r"(?i)^(moved out|removed)\b", verdict.strip()):
            moved_out.append((name, verdict))
            continue
        all_links = [html.unescape(u) for u in re.findall(r'href="(https?://[^"]+)"', b, re.I)]
        rows.append({
            "business_id": f"{prefix}-{i:03d}", "region": region, "scope": g("scope"),
            "home_state": "", "category_no": "", "category": g("category"), "entry_no": "",
            "business_name": name,
            "needs_verify": "True" if re.search(r"(?i)unverified", verdict) else "False",
            "audit_verdict": verdict, "sub_type": g("sub_type"),
            "cannabis_focus": g("cannabis_focus"), "description": g("description"),
            "website": g("website"), "phone": g("phone"), "email": g("email"),
            "address": g("address"), "contact_as_published": "",
            "states_served": g("states_served"), "states_served_codes": "",
            "key_people_private": g("key_people_private"),
            "evidence_of_cannabis_work": g("evidence_of_cannabis_work"),
            "evidence_links": "; ".join(dict.fromkeys(all_links))[:900],
            "credentials": g("credentials"),
            "audit_note": "; ".join(x for x in (extra, heading_note if verdict != heading_note else "") if x),
            "sources": g("sources"), "last_checked": TODAY,
        })
    if moved_out:
        print(f"    {len(moved_out)} moved out of the directory as licensed operators: "
              + "; ".join(f"{n} ({v})" for n, v in moved_out[:3]))
        warn.append((f"{stem}: moved out as licensed operators",
                     "; ".join(n for n, _ in moved_out)))
    if unmapped:
        warn.append((f"{stem}: labels not mapped",
                     "; ".join(f"{k}({v})" for k, v in unmapped.most_common(6))))
    return rows


def parse_california(warn):
    """California's audit table is the complete business list — 371 rows, the
    figure HANDOFF records. Its category column is a number, and the tally
    table above it maps each number to a standard category name. The prose
    detail further down the report is the rewritten directory; it is not merged
    here, so website, phone and address stay empty for California for now."""
    s = (SRC / "california-businesses-audited.html").read_text(errors="replace")
    tables = re.findall(r"<table.*?</table>", s, re.S | re.I)
    cat_map = {}
    for tb in tables:
        rs = [cells(tr) for tr in re.findall(r"<tr.*?</tr>", tb, re.S | re.I)]
        if not rs or "Standard category" not in rs[0]:
            continue
        ci, si = rs[0].index("Category"), rs[0].index("Standard category")
        for r in rs[1:]:
            if len(r) > si:
                num = re.match(r"\s*(\d+)", r[ci])
                if num:
                    cat_map[num.group(1)] = r[si].strip()
        break
    rows = []
    for tb in tables:
        trs = re.findall(r"<tr.*?</tr>", tb, re.S | re.I)
        if not trs:
            continue
        hdr = cells(trs[0])
        if "Business" not in hdr or "Verdict" not in hdr:
            continue
        ix = {h: i for i, h in enumerate(hdr)}
        for tr in trs[1:]:
            raw = re.findall(r"<t[dh].*?</t[dh]>", tr, re.S | re.I)
            c = [txt(x) for x in raw]
            get = lambda h: c[ix[h]] if h in ix and ix[h] < len(c) else ""
            name = get("Business")
            if not name:
                continue
            verdict = get("Verdict")
            if re.match(r"(?i)^(removed|moved out|already listed)", verdict):
                continue
            cat_no = re.match(r"\s*(\d+)", get("Category"))
            scope = ""
            # "Cultiva Law, PLLC — National" carries the scope in the name
            if " — " in name:
                head, _, tail = name.rpartition(" — ")
                if re.match(r"(?i)^(national|regional|local)\b", tail):
                    name, scope = head.strip(), tail.strip()
            rows.append({
                "business_id": f"CA-{len(rows) + 1:03d}", "region": "California",
                "scope": scope, "home_state": "CA",
                "category_no": cat_no.group(1) if cat_no else "",
                "category": cat_map.get(cat_no.group(1), "") if cat_no else "",
                "entry_no": "", "business_name": name,
                "needs_verify": "True" if re.search(r"(?i)unverified", verdict) else "False",
                "audit_verdict": verdict, "sub_type": "", "cannabis_focus": "",
                "description": "", "website": "", "phone": "", "email": "", "address": "",
                "contact_as_published": "", "states_served": get("Sub-region"),
                "states_served_codes": "", "key_people_private": "",
                "evidence_of_cannabis_work": get("Corrections"),
                "evidence_links": "; ".join(dict.fromkeys(
                    html.unescape(u) for x in raw for u in
                    re.findall(r'href="(https?://[^"]+)"', x, re.I)))[:900],
                "credentials": "", "audit_note": get("Corrections")[:600],
                "sources": get("What was checked (URL)")[:600], "last_checked": TODAY,
            })
    if not rows:
        warn.append(("california", "no audit table found"))
    return rows


# HANDOFF's 17 standard business categories.
STANDARD_CATEGORIES = ["Legal", "Accounting and Tax", "Insurance", "Real Estate",
                       "Construction and Facilities", "Security", "Cash Management",
                       "Waste Services", "Staffing and Recruiting", "Compliance and Consulting",
                       "Marketing and Advertising", "Software", "Packaging and Labelling",
                       "Grow Supplies and Equipment", "Extraction and Lab Equipment",
                       "Consumer Brands", "Hemp and CBD Products"]
# The national and New England directories describe each category in a sentence
# rather than naming it, so map the description to the standard name.
CATEGORY_PATTERNS = [
    (r"lawyer|law firm|legal", "Legal"),
    (r"accountant|cpa|tax advis", "Accounting and Tax"),
    (r"^insurance|insurance agent|insurance broker", "Insurance"),
    (r"real estate|landlord|zoned property", "Real Estate"),
    (r"construction|electrical|hvac|build-?out|facility", "Construction and Facilities"),
    (r"security system|security guard|^security", "Security"),
    (r"payment processor|cashless|atm|banking|lending|armoured|armored|cash management",
     "Cash Management"),
    (r"waste", "Waste Services"),
    (r"staffing|recruit", "Staffing and Recruiting"),
    # Software must be tested before Compliance: the national directory's
    # software category reads "Software: seed-to-sale, POS, compliance, ERP,
    # e-commerce, delivery software", and "compliance" would steal it.
    (r"software|seed-to-sale|pos\b|erp|e-commerce", "Software"),
    (r"compliance|licensing.*consultant|application consultant", "Compliance and Consulting"),
    (r"marketing|advertis|listing platform|marketplace|design", "Marketing and Advertising"),
    (r"packaging|labell?ing", "Packaging and Labelling"),
    (r"lighting|nutrient|grow suppl|hydroponic|cultivation equipment|greenhouse",
     "Grow Supplies and Equipment"),
    (r"extraction|lab equipment|processing.*equipment", "Extraction and Lab Equipment"),
    (r"consumer brand|mso brand", "Consumer Brands"),
    (r"hemp|cbd", "Hemp and CBD Products"),
]


def standard_category(value, sub_type="", description=""):
    """Return (standard category, leftover) for a directory's category text."""
    v = (value or "").strip()
    if v in STANDARD_CATEGORIES:
        return v, ""
    # "Cash Management; armoured courier — General" style
    for std in STANDARD_CATEGORIES:
        if v.lower().startswith(std.lower() + ";") or v.lower().startswith(std.lower() + " ("):
            return std, v[len(std):].lstrip("; (").rstrip(")")
    # A category that bundles several standards (the national directory has one)
    # is resolved from the row's own sub-type instead.
    blob = v.lower()
    if sum(1 for pat, _ in CATEGORY_PATTERNS if re.search(pat, blob)) > 2:
        for pat, std in CATEGORY_PATTERNS:
            if re.search(pat, (sub_type + " " + description).lower()):
                return std, v
    for pat, std in CATEGORY_PATTERNS:
        if re.search(pat, blob):
            return std, v if v.lower() != std.lower() else ""
    return "", v


def normalise_categories(rows, warn):
    fixed, unresolved = 0, collections.Counter()
    for r in rows:
        std, leftover = standard_category(r["category"], r.get("sub_type", ""),
                                          r.get("description", ""))
        if not std:
            unresolved[r["category"][:54]] += 1
            continue
        if std != r["category"]:
            if leftover and not r.get("sub_type"):
                r["sub_type"] = leftover
            elif leftover:
                r["audit_note"] = "; ".join(x for x in (r.get("audit_note", ""),
                                                        f"directory category: {leftover}") if x)
            r["category"] = std
            fixed += 1
    print(f"categories normalised to the standard 17: {fixed}")
    if unresolved:
        print("categories that could not be resolved:")
        for k, v in unresolved.most_common(8):
            print(f"  {v:>4}  {k}")
        warn.append(("unresolved categories", str(sum(unresolved.values()))))
    return fixed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true"), ap.add_argument("--only")
    ap.add_argument("--refresh", action="append", default=[],
                    help="drop a region's rows and re-parse it from its report "
                         "(repeatable). Anything another script added to those rows — "
                         "California's contact detail, the licence-match flags — must be "
                         "re-applied afterwards; see docs/STATUS.md for the order.")
    a = ap.parse_args()

    with open(OUT, encoding="utf-8") as f:
        existing = list(csv.DictReader(f))
    cols = list(existing[0].keys())
    if a.refresh:
        before = len(existing)
        dropped = {r["region"] for r in existing if r["region"] in a.refresh}
        missing = [x for x in a.refresh if x not in {r["region"] for r in existing}]
        if missing:
            sys.exit(f"no such region in the file: {missing} — "
                     f"regions are {sorted({r['region'] for r in existing})}")
        existing = [r for r in existing if r["region"] not in a.refresh]
        print(f"refresh: dropped {before - len(existing)} rows from {sorted(dropped)}")
    have = {r["region"] for r in existing}
    print(f"existing: {len(existing)} rows from {sorted(have)}")

    warn, added = [], []
    for stem, (region, prefix) in TABLE_DIRS.items():
        if a.only and a.only not in stem:
            continue
        if region in have:
            print(f"  {region}: already in the file, skipped")
            continue
        got = parse_table_directory(stem, region, prefix, warn)
        print(f"  {region:24} {len(got):>4} businesses")
        added.extend(got)

    for stem, (region, prefix) in ENTRY_DIRS.items():
        if a.only and a.only not in stem:
            continue
        if region in have:
            print(f"  {region}: already in the file, skipped")
            continue
        got = parse_entry_directory(stem, region, prefix, warn)
        print(f"  {region:24} {len(got):>4} businesses")
        added.extend(got)

    if "California" not in have and not (a.only and "calif" not in a.only):
        got = parse_california(warn)
        print(f"  {'California':24} {len(got):>4} businesses")
        added.extend(got)

    print(f"\nparsed {len(added)} new businesses")
    if warn:
        print("notes:")
        for k, v in warn:
            print(f"  {k}: {v}")
    if not added:
        normalise_categories(existing, warn)
        if not a.dry_run:
            with open(OUT, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=cols)
                w.writeheader()
                for r in existing:
                    w.writerow({c: r.get(c, "") for c in cols})
            print(f"wrote {OUT.relative_to(ROOT)} — {len(existing)} rows")
        return
    cat = collections.Counter(r["category"][:46] for r in added)
    print("\ntop categories:")
    for k, v in cat.most_common(8):
        print(f"  {v:>4}  {k}")
    blank = sum(1 for r in added if not r["category"])
    print(f"rows with no category: {blank}")

    all_rows = existing + added
    normalise_categories(all_rows, warn)

    if a.dry_run:
        print("\n[dry-run] nothing written")
        return
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in all_rows:
            w.writerow({c: r.get(c, "") for c in cols})
    print(f"\nwrote {OUT.relative_to(ROOT)} — {len(all_rows)} rows")


if __name__ == "__main__":
    main()
