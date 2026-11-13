#!/usr/bin/env python3
"""Matching New Jersey's two spellings of the same municipality.

The CRC publishes its own town names two different ways, and both are official:

  permit PDF   "EGG HBR TWP", "EDGEWATER PRK", "CAPE MAY CH", "CARNEYS POINT"
  HTML table   "Egg Harbor Township", "Edgewater Park", "Cape May Court House",
               "Carney's Point"

No expansion table is invented here. An abbreviation is accepted only when it is
a letter-by-letter subsequence of a full name the CRC itself lists for that same
organisation, and only when exactly one candidate fits. Token counts must agree,
which is what stops "EGG HBR TWP" matching "Egg Harbor City".

One source of truth, imported by the builder, the county check and the
reconciliation report, so a match made in one cannot differ from the others.
"""
import re

# "TOWNSHIP OF FRANKLIN" and "FRANKLIN TOWNSHIP" are the same place written two
# ways; this is word order, not an expansion.
OF_FORM = re.compile(r"^(TOWNSHIP|BOROUGH|CITY|TOWN|VILLAGE)\s+OF\s+(.+)$")


def norm_town(name):
    """Upper-case, punctuation dropped, word order normalised.

    Apostrophes and full stops are deleted rather than replaced by a space:
    turning "Carney's Point" into "CARNEY S POINT" would give it three tokens
    against the permit's two ("CARNEYS POINT") and the token-count rule in
    is_abbrev_of would then reject a match between one town and itself.
    """
    s = re.sub(r"['`.]", "", (name or "").upper())
    s = re.sub(r"[^A-Z ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    m = OF_FORM.match(s)
    if m:
        s = f"{m.group(2)} {m.group(1)}"
    return s


def norm_org(name):
    """Compare organisation names without punctuation or corporate suffixes."""
    s = (name or "").upper()
    s = re.sub(r"\(.*?\)", " ", s)                      # "(formerly Justice Grown NJ)"
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = re.sub(r"\b(LLC|L L C|INC|CORP|CORPORATION|CO|COMPANY|LP|LLP|"
               r"HOLDINGS|GROUP|THE)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def is_abbrev_of(short, full):
    """True if `short` is a token-wise abbreviation of `full`.

    Each token must share its first letter with the matching token of the full
    name and be a subsequence of it: HBR of HARBOR, TWP of TOWNSHIP, PRK of
    PARK, CH of COURT HOUSE is NOT accepted (token counts differ) and is left
    to the caller to report rather than guessed at.
    """
    a, b = norm_town(short).split(), norm_town(full).split()
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x == y:
            continue
        if not y.startswith(x[0]) or len(x) > len(y):
            return False
        it = iter(y)
        if not all(ch in it for ch in x):
            return False
    return True


def resolve_town(permit_town, candidates):
    """The CRC's own full spelling for an abbreviated town.

    Returns (full_name, "") on a confident match, or ("", reason) otherwise.
    """
    pt = norm_town(permit_town)
    exact = [c for c in candidates if norm_town(c) == pt]
    if exact:
        return exact[0], ""
    hits = [c for c in candidates if is_abbrev_of(permit_town, c)]
    if len(hits) == 1:
        return hits[0], ""
    if not hits:
        return "", "no listed location matches"
    return "", f"ambiguous between {len(hits)}: {', '.join(hits)}"


def same_town(a, b):
    """True if two spellings are the same municipality by either rule."""
    return norm_town(a) == norm_town(b) or is_abbrev_of(a, b) or is_abbrev_of(b, a)
