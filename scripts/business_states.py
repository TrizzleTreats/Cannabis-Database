"""Which states a service business is in or serves, derived conservatively from its
directory entry, with the basis for each state recorded.

The directories' service areas are free text ("Regional (MD/DC/PA)", "Local (Tampa Bay /
Central FL)", "National (HQ Pittsburgh, PA; ...)"), and only a few dozen entries carry
coded states. A state is attached to a business only on one of two bases:

  based   the business has an address in the state (a "City, ST 12345" in its
          address), its recorded home state is that state, or it comes from the
          California directory, which lists California businesses only;
  named   its service-area text or scope names the state explicitly, by its full name
          or its two-letter code in capitals.

Nothing is inferred from a region: a business in the Mid-Atlantic directory is not
attached to every Mid-Atlantic state. A National firm is not attached to every state
either; the state page lists national firms separately.
"""
import re

STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
    "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia",
    "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}
BY_NAME = {v.lower(): k for k, v in STATES.items()}
# "City, ST 12345", or "City, ST" followed by a separator (some entries publish no ZIP).
ADDRESS = re.compile(r"\b([A-Z]{2})\s+\d{5}\b|,\s*([A-Z]{2})(?=\s*(?:[,;()\u2014-]|$))")
CODE = re.compile(r"(?<![A-Za-z])(" + "|".join(STATES) + r")(?![A-Za-z])")
# Longest names first, so "West Virginia" is not also read as "Virginia".
NAME = re.compile(r"\b(" + "|".join(sorted(map(re.escape, STATES.values()), key=len, reverse=True))
                  + r")\b", re.I)
# Places whose name contains another state's name.
NOT_A_STATE = re.compile(r"Kansas City|Washington[- ,]*D\.?C\.?|Virginia Beach|Indianapolis", re.I)


def _named(text):
    out = set()
    if not text:
        return out
    if re.search(r"Washington[- ,]*D\.?C\.?", text, re.I):
        out.add("DC")
    if re.search(r"Virginia Beach", text, re.I):
        out.add("VA")
    clean = NOT_A_STATE.sub(" ", text)
    out.update(m.group(1) for m in CODE.finditer(clean))
    out.update(BY_NAME[m.group(1).lower()] for m in NAME.finditer(clean))
    return out


def derive(b):
    """{state code: "based" | "named"} for one business entry (a dict of its fields)."""
    based = {m.group(1) or m.group(2) for m in ADDRESS.finditer(b.get("address") or "")} & set(STATES)
    home = (b.get("home_state") or "").strip()
    if home.upper() in STATES:
        based.add(home.upper())
    elif home.lower() in BY_NAME:
        based.add(BY_NAME[home.lower()])
    if b.get("region") == "California":
        based.add("CA")
    codes = {c.strip().upper() for c in (b.get("states_served_codes") or "").replace(";", ",").split(",")}
    named = (_named(b.get("states_served")) | _named(b.get("scope")) | (codes & set(STATES))) - based
    out = {s: "based" for s in based}
    out.update({s: "named" for s in named})
    return dict(sorted(out.items()))  # sets iterate in a per-run order; keep the output stable
