#!/usr/bin/env python3
"""Draft a public-records request for each jurisdiction that publishes no licensee list.

26 of the 51 jurisdictions publish licence data only through a per-record lookup
portal — eLicense, Accela, "Verify a License" — which answers one query at a
time and cannot be enumerated. STATUS records the sweep that established this:
every regulator page the audited reports cite was fetched and scanned for a
list-shaped data file and for ArcGIS, Tableau and PowerBI embeds, and across all
26 it found zero licensee lists and no cannabis map embed, with 128 of 150 pages
fetching successfully. So this is not a tooling gap, and the remaining route is
to ask.

The letters are written here; a person sends them. That is not a limitation to
work around — a records request needs a real requester with a reply address, and
the reply comes back to them.

Two things this deliberately does NOT do:

  * It does not cite a statute. Every state's public-records law has its own
    name and number, and a request citing the wrong one is worse than a request
    citing none — it invites a brush-off and it misinforms the sender. Each
    letter leaves a marked slot, and the agency's own records page is the place
    to fill it from.
  * It does not invent an address. The agency named in each letter is the
    candidate the project's own audited report for that state names most often
    in a cannabis-licensing context, with its own evidence quoted underneath so
    the sender can see why. Where the report's strongest candidate is plainly a
    tax or liquor body — which happens in the states that license no cannabis
    beyond hemp — the letter says so rather than addressing it confidently.

The ask is written to work whatever a state licenses: it asks for every licence,
permit and registration the agency issues under any cannabis, marijuana or hemp
programme, rather than naming programmes that may not exist there.

It also asks for nothing exempt. No personal contact details, no owners' home
addresses, no application materials, no security plans. That is partly this
project's own privacy rule and partly practical: a request that cannot trip an
exemption is cheap to fulfil and hard to refuse.

Usage:
  python3 scripts/draft_data_requests.py [--out outreach/data-requests]
"""
import argparse, collections, html, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent

STATES = {
    "AK": "Alaska", "AR": "Arkansas", "AZ": "Arizona", "GA": "Georgia", "IA": "Iowa",
    "ID": "Idaho", "IN": "Indiana", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MT": "Montana",
    "NC": "North Carolina", "ND": "North Dakota", "NE": "Nebraska", "NM": "New Mexico",
    "OK": "Oklahoma", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee",
    "UT": "Utah", "WI": "Wisconsin", "WV": "West Virginia", "WY": "Wyoming",
}
SLUG = {
    "AK": "alaska", "AR": "arkansas", "AZ": "arizona", "GA": "georgia", "IA": "iowa",
    "ID": "idaho", "IN": "indiana", "KS": "kansas", "KY": "kentucky", "LA": "louisiana",
    "MI": "michigan", "MN": "minnesota", "MS": "mississippi", "MT": "montana",
    "NC": "north-carolina", "ND": "north-dakota", "NE": "nebraska", "NM": "new-mexico",
    "OK": "oklahoma", "SC": "south-carolina", "SD": "south-dakota", "TN": "tennessee",
    "UT": "utah", "WI": "wisconsin", "WV": "west-virginia", "WY": "wyoming",
}

# What STATUS already records about a state's position, so a letter does not ask
# a question the project has already answered.
KNOWN = {
    "MI": "Michigan's CRA publishes monthly Licensing Reports, but they are activity reports — "
          "prequalifications, approvals and denials for that month — not a roster of current "
          "licensees. This asks for the roster.",
    "MN": "Minnesota's OCM licence data page serves a Radware Bot Manager hCaptcha to any client. "
          "A records request is the route that does not depend on solving one.",
    "OK": "Oklahoma publishes dated aggregate counts on its Licensing and Tax Data page (as of "
          "2 Nov 2026: 1,226 dispensaries, 1,582 growers, 545 processors, 42 transporters, 12 "
          "labs, 7 waste facilities) but licensee-level data only through Verify a License. This "
          "asks for the roster behind those counts.",
    "AZ": "No dispensary list file appears on either the Marijuana Licensing or Medical Marijuana "
          "pages. The only such file found anywhere in the crawl sits on a private site, which "
          "this project's primary-sources rule excludes.",
}
# States whose licence universe is hemp registration rather than cannabis licensing.
HEMP_ONLY = {"ID", "KS", "WY", "IN"}

# Where STATUS already states the agency, that beats anything extracted from
# prose. Michigan is the clearest case: the reports still carry "Bureau of
# Marijuana Regulation", the body's former name, while STATUS records the
# current Cannabis Regulatory Agency.
STATED = {
    "MI": "Cannabis Regulatory Agency (CRA)",
    "MN": "Office of Cannabis Management (OCM)",
    "OK": "Oklahoma Medical Marijuana Authority (OMMA)",
    "AZ": "Arizona Department of Health Services (ADHS)",
}

AGENCY_RE = re.compile(
    r"((?:[A-Z][A-Za-z'&.\-]{2,} ){0,4}"
    r"(?:Office|Department|Division|Bureau|Commission|Board|Authority)"
    r"(?: of [A-Z][A-Za-z'&.\- ]{3,40})?)")
CONTEXT = re.compile(r"licens|permit|registr", re.I)
SUBJECT = re.compile(r"cannabis|marijuana|hemp", re.I)
OFF_TOPIC = re.compile(r"election|canvass|veterinar|pharmacy count|advisory", re.I)
# The subject words that mark a candidate as actually being the cannabis body.
ON_SUBJECT = re.compile(r"cannabis|marijuana|hemp", re.I)
# Regex extraction from prose produces fragments, and a fragment can even carry
# a negation: Mississippi's best raw candidate was "The Mississippi Department
# of Agriculture & Commerce does not issue hem". Anything that looks like a
# sentence remnant, names a federal body, or runs long is thrown away.
FRAGMENT = re.compile(r"\b(does|do|has|have|will|began|is|are|was|were|not|and the|of the)\b", re.I)
FEDERAL = re.compile(r"\bU\.?S\.?\b|\bUnited States\b|\bFederal\b", re.I)


CONNECTIVE = {"of", "and", "for", "the", "&"}
AGENCY_NOUN = re.compile(r"^(Office|Department|Division|Bureau|Commission|Board|Authority)$")


def trim_to_name(name):
    """Cut a candidate at the first word that is plainly sentence prose.

    The extraction pulls a clause, not a name: "Office of Medical Cannabis
    ceased accepting permit", "Board of Pharmacy NO current cannabis licensing
    ro". An agency name is Title Case words and connectives, so the name ends at
    the first lower-case word that is not a connective — and at an ALL-CAPS word
    too, which is how the reports start an editorial aside.
    """
    kept = []
    for word in name.split():
        if word in CONNECTIVE:
            kept.append(word)
            continue
        if word[:1].islower() or (word.isupper() and len(word) > 1):
            break
        kept.append(word)
    while kept and kept[-1] in CONNECTIVE:
        kept.pop()
    return " ".join(kept)


def well_formed(name, code):
    """A usable agency name for THIS state, not a clause or another state's body."""
    if len(name) > 58 or FEDERAL.search(name) or FRAGMENT.search(name):
        return False
    # The reports compare states, so Mississippi's report names the Alabama
    # Medical Cannabis Commission and an unguarded extraction addresses the
    # letter to Alabama.
    others = {n for c, n in STATES.items() if c != code} | {
        "Alabama", "California", "Colorado", "Connecticut", "Delaware", "Florida", "Hawaii",
        "Illinois", "Maine", "Maryland", "Massachusetts", "Missouri", "Nevada", "New Jersey",
        "New York", "Ohio", "Oregon", "Pennsylvania", "Rhode Island", "Texas", "Vermont",
        "Virginia", "Washington"} - {STATES[code]}
    if any(re.search(rf"\b{re.escape(o)}\b", name) for o in others):
        return False
    return any(AGENCY_NOUN.match(w) for w in name.split())


def report_for(code):
    hits = list((ROOT / "reports" / "regions").rglob(f"{SLUG[code]}/*.html"))
    return hits[0] if hits else None


def candidates(code):
    """Agencies the state's own audited report names in a licensing context."""
    path = report_for(code)
    if not path:
        return [], None
    text = html.unescape(re.sub(r"<[^>]+>", " ", path.read_text(errors="replace")))
    text = re.sub(r"\s+", " ", text)
    found = collections.Counter()
    for m in AGENCY_RE.finditer(text):
        window = text[max(0, m.start() - 150):m.end() + 150]
        if not (CONTEXT.search(window) and SUBJECT.search(window)):
            continue
        name = trim_to_name(m.group(1).strip())
        if len(name) < 12 or OFF_TOPIC.search(name) or not well_formed(name, code):
            continue
        found[name] += 1
    # Prefer a candidate that actually names the subject. A well-formed
    # "Department of Revenue" is still the wrong recipient for a licence list.
    ranked = sorted(found.items(),
                    key=lambda kv: (bool(ON_SUBJECT.search(kv[0])), kv[1]), reverse=True)
    return ranked[:4], path.relative_to(ROOT)


FIELDS = """  1. the licence, permit or registration number as you issue it
  2. the licence type in your own wording, not a category we have chosen
  3. the status in your own wording, and what each status value means if that is
     not self-evident
  4. the legal name of the holder
  5. the trade name or DBA, where one is recorded
  6. the premises address, including the county — county is the field we most
     often cannot obtain anywhere else
  7. the issue date and the expiry date
  8. the date the extract was produced"""

BODY = """{today}

{agency}
{state}

**Public records request — list of licensed cannabis, marijuana and hemp businesses**

[ Cite {state}'s public records law here before sending. Its name and section
  number are on the agency's own records-request page; this letter deliberately
  does not guess them. ]

Dear Records Officer,

I am building a free, public, non-commercial database of cannabis and hemp law
and licensing across all fifty states and the District of Columbia. It uses
official government sources only. I am requesting a copy of a record your
agency already holds.

**What I am asking for**

A list of every licence, permit or registration your agency currently issues
under any cannabis, marijuana or hemp programme it administers, in whatever
machine-readable format you already have — CSV, Excel or a database export. For
each record:

{fields}

If an existing report or export already contains these, I would rather have
that than a custom extract. I am not asking you to create a new record or to
analyse anything.

**What I am NOT asking for**

To keep this simple and to avoid anything exempt, I am expressly not requesting:

  * personal contact details of any individual — no personal phone numbers,
    personal email addresses or home addresses
  * the names or addresses of owners, officers or financial backers
  * application materials, financial disclosures, or any security or
    transportation plan
  * anything about patients, caregivers or employees

If any field I have asked for is exempt, please withhold that field, provide the
rest, and cite the specific exemption. Personal details of individuals will not
be published by me in any case.

**Why I am asking rather than downloading it**

{why}

**Practicalities**

Electronic delivery by email or a download link is ideal, and I am happy to
accept the data in whatever structure you hold it. If fees apply, please tell me
the estimate before incurring any cost, and let me know whether a fee waiver is
available for non-commercial public-interest use.

If another agency in {state} holds this record instead, I would be grateful if
you could tell me which, or forward this request.

Anything you provide will be published with attribution to your agency and with
the date you provided it, so a reader can see exactly how current it is.

Thank you for your time.

Yours sincerely,

[ your name ]
[ your email ]
[ your postal address, if the agency requires one ]

---

## Before you send this

  * **Confirm the agency.** {agency_note}{proposed_caution}
  * **Confirm where to send it.** Most agencies have a records-request page or a
    designated officer, and some require a web form rather than an email. This
    draft does not guess an address.
  * **Add the statute.** One line, from that same records page.

Evidence this project has for the ask, if you are challenged on it:
{evidence}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outreach/data-requests")
    ap.add_argument("--today", default="14 November 2026")
    args = ap.parse_args()
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)

    index, low = [], []
    for code, state in sorted(STATES.items(), key=lambda kv: kv[1]):
        cands, src = candidates(code)
        stated = STATED.get(code)
        onsubject = [(n, c) for n, c in cands if ON_SUBJECT.search(n)]
        best = stated or (onsubject[0][0] if onsubject else "")
        shaky = not best
        agency = best or "[ the agency that licenses cannabis, marijuana or hemp in this state ]"

        if stated:
            note = (f"“{stated}” — recorded in this project's own STATUS, which is more current "
                    f"than the state report (the report still uses an earlier name for it). "
                    f"Confirm the records-request route, not the agency.")
        elif onsubject:
            note = (f"“{best}” names cannabis, marijuana or hemp in its own title and is "
                    f"cited {onsubject[0][1]}x in a licensing context in this project's audited "
                    f"report. Worth a glance, not a re-research.")
        else:
            note = ("NOT FILLED IN. Nothing in this project's report for this state names a "
                    "cannabis, marijuana or hemp body in a licensing context, so no recipient is "
                    "guessed here"
                    + (" — expected, because this state licenses no cannabis beyond hemp, so the "
                       "right recipient is most likely its agriculture department's hemp "
                       "programme." if code in HEMP_ONLY else
                       ". The other agencies the report does name are listed below."))

        why = (KNOWN.get(code) or
               "Your agency's published pages do not appear to include a downloadable list of "
               "licence holders. Every regulator page cited in this project's research for this "
               "state was fetched and checked for a list-shaped data file and for embedded ArcGIS, "
               "Tableau and Power BI reports; none was found, and licence data appears to be "
               "available only through a lookup that answers one record at a time.")
        if code in HEMP_ONLY:
            why += ("\n\nI understand this state may license hemp only, and no adult-use or "
                    "medical programme. The hemp grower, processor and handler registrations are "
                    "exactly what I am asking for in that case.")

        evidence = "\n".join(f"  * {n} — named {c}x in a licensing context" for n, c in cands) \
            or "  * (nothing well-formed extracted from the report)"
        if src:
            evidence += f"\n  * Source read: {src}"

        # Only a name lifted out of the reports' prose carries this risk. A name
        # from STATED is one the project itself records and has checked.
        proposed_caution = "" if stated else (
            "\n    **This name came out of the report's prose, which cannot tell a body that "
            "licenses today from one proposed in a bill** — and that matters here, because these "
            "are the 26 jurisdictions with no licence data and several run no programme at all. "
            "If it turns out to be proposed rather than operating, the live recipient is almost "
            "certainly the agriculture or health department that runs the state's hemp programme.")
        text = BODY.format(today=args.today, agency=agency, state=state, fields=FIELDS,
                           why=why, agency_note=note, evidence=evidence,
                           proposed_caution=proposed_caution)
        path = out / f"{code}-{SLUG[code]}.md"
        path.write_text(text, encoding="utf-8")
        index.append((code, state, best, shaky))
        if shaky:
            low.append(code)

    readme = ["# Data requests — 26 jurisdictions that publish no licensee list", "",
              f"Drafted {args.today} by scripts/draft_data_requests.py. One letter per "
              "jurisdiction. **A person has to send these**: a records request needs a real "
              "requester and a reply address.", "",
              "Each letter needs three things added before it goes out — the agency confirmed, "
              "the send-to address, and the state's public-records statute. None is guessed here; "
              "a wrong statute or a wrong recipient is worse than a blank.", "",
              "**Read this before working through the table.** The agency column is extracted "
              "from this project's own audited report for each state, and it cannot distinguish a "
              "body that licenses today from one proposed in a bill. That matters here more than "
              "it would elsewhere: these are precisely the 26 jurisdictions with no licence data, "
              "and several run no programme at all. So treat a plausible-sounding "
              "\"Cannabis Control Commission\" as a lead to check, not a fact — and where a state "
              "licenses only hemp, expect the real recipient to be its agriculture or health "
              "department rather than any cannabis body.", "",
              "| State | Candidate agency from this project's own report | Confidence |",
              "|---|---|---|"]
    for code, state, best, shaky in index:
        readme.append(f"| {state} ({code}) | {best or '**not filled in — find it**'} | "
                      f"{'FIND THE AGENCY' if shaky else 'named in the letter'} |")
    readme += ["", f"{len(index) - len(low)} of {len(index)} name a cannabis, marijuana or hemp "
                   f"body in their own title, which is the only basis on which a recipient is "
                   f"filled in here. {len(low)} are left blank for you to fill: "
                   f"{', '.join(low)}. A blank is deliberate — a letter addressed to the wrong "
                   f"agency is worse than one addressed to none.", "",
               "The ask is deliberately narrow and asks for nothing exempt — no personal contact "
               "details, no owners, no application materials, no patient or employee data. That "
               "is this project's own privacy rule, and it also makes the request cheap to fulfil "
               "and hard to refuse."]
    (out / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")

    print(f"{len(index)} letters -> {out.relative_to(ROOT)}")
    print(f"  agency looks plausible : {len(index) - len(low)}")
    print(f"  agency needs checking  : {len(low)}  ({', '.join(low)})")
    print(f"  index                  : {(out / 'README.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
