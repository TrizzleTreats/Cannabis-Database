"""Turn the Census state boundaries (us-atlas TopoJSON, already projected) into SVG paths.

Done at build time so the site needs no mapping library and fetches nothing from a CDN:
the browser gets one small JSON of path strings. The geometry is shapes only — it carries
no legal content and is never the source of a status.

Input:  data/raw/us-atlas/states-albers-10m.json (d3.geoAlbersUsa, 975x610, AK/HI inset)
Output: {"viewBox": ..., "states": [{"code", "name", "fips", "d", "label": [x, y],
          "callout": bool}]}
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOPOLOGY = ROOT / "data" / "raw" / "us-atlas" / "states-albers-10m.json"

# Too small to hold a two-letter label inside the shape. These get a label in a column
# to the right of the map with a leader line, the usual convention for US choropleths.
CALLOUTS = ["VT", "NH", "MA", "RI", "CT", "NJ", "DE", "MD", "DC"]
CALLOUT_X = 1000
CALLOUT_TOP, CALLOUT_STEP = 150, 30
VIEWBOX = [0, 0, 1060, 610]

# Nudges for states whose area centroid sits awkwardly for a label (Florida's centroid
# is on the Gulf side of the peninsula, Michigan's is in Lake Michigan, Louisiana's and
# Kentucky's sit off-centre). Pixels in the 975x610 projection.
NUDGE = {"FL": (12, 8), "MI": (14, 22), "LA": (-8, 0), "KY": (6, 2), "ID": (0, 18),
         "HI": (-4, -10), "CA": (-6, 0), "WV": (-3, 4), "VA": (6, 2), "NY": (6, 0)}


def _decode_arcs(topo):
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)
    return arcs


def _ring(indices, arcs):
    pts = []
    for i in indices:
        arc = arcs[i] if i >= 0 else list(reversed(arcs[~i]))
        pts.extend(arc if not pts else arc[1:])
    return pts


def _area_centroid(ring):
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        f = x0 * y1 - x1 * y0
        a += f
        cx += (x0 + x1) * f
        cy += (y0 + y1) * f
    if abs(a) < 1e-9:
        return 0.0, ring[0]
    return abs(a) / 2, (cx / (3 * a), cy / (3 * a))


def _path(rings):
    parts = []
    for ring in rings:
        pts = [f"{x:.1f},{y:.1f}" for x, y in ring]
        # drop consecutive duplicates the rounding creates
        pts = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
        parts.append("M" + "L".join(pts) + "Z")
    return "".join(parts)


def build(code_by_name):
    topo = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    arcs = _decode_arcs(topo)
    out = []
    for g in topo["objects"]["states"]["geometries"]:
        name = g["properties"]["name"]
        code = code_by_name.get(name)
        if not code:
            continue  # territories (Puerto Rico etc.) are not among the 51
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
        rings = [_ring(r, arcs) for poly in polys for r in poly]
        # label at the centroid of the largest outer ring
        outer = [_ring(poly[0], arcs) for poly in polys]
        _, (lx, ly) = max((_area_centroid(r) for r in outer), key=lambda t: t[0])
        dx, dy = NUDGE.get(code, (0, 0))
        entry = {"code": code, "name": name, "fips": g["id"], "d": _path(rings),
                 "anchor": [round(lx, 1), round(ly, 1)]}
        if code in CALLOUTS:
            entry["callout"] = True
            entry["label"] = [CALLOUT_X, CALLOUT_TOP + CALLOUT_STEP * CALLOUTS.index(code)]
        else:
            entry["label"] = [round(lx + dx, 1), round(ly + dy, 1)]
        out.append(entry)
    missing = sorted(set(code_by_name.values()) - {s["code"] for s in out})
    if missing:
        raise SystemExit(f"map geometry is missing jurisdictions: {missing}")
    return {"viewBox": VIEWBOX, "source": "US Census Bureau cartographic state boundaries, "
            "2017 edition, via us-atlas 3.0.1 (data/raw/us-atlas/)", "states": out}


# ------------------------------------------------------------------ counties
COUNTIES = ROOT / "data" / "raw" / "us-atlas" / "counties-albers-10m.json"
CENSUS_NAMES = ROOT / "data" / "raw" / "census_counties_by_state.csv"
CT_TRADITIONAL = {"Fairfield", "Hartford", "Litchfield", "Middlesex", "New Haven",
                  "New London", "Tolland", "Windham"}


def county_display_names():
    """(state, value in the county column) -> the name to show a reader.

    The column holds Census basenames, plus "<name> city" for the six independent
    cities that share a basename with a county (scripts/resolve_independent_cities.py).
    A reader should see "Baltimore County" and "Baltimore City", "Winchester City"
    (an independent city with no county of that name), "Orleans Parish",
    "District of Columbia" — never "Winchester County"."""
    import csv, collections
    by_base = collections.defaultdict(list)
    with open(CENSUS_NAMES, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            by_base[(r["state"], r["county_basename"])].append(r["county_name"])
    out = {}
    for (st, base), names in by_base.items():
        pretty = [n[:-4] + "City" if n.endswith(" city") else n for n in names]
        if len(names) == 1:
            out[(st, base)] = pretty[0]
        else:
            for n, p in zip(names, pretty):
                if n.endswith(" city"):
                    out[(st, f"{base} city")] = p
                else:
                    out[(st, base)] = p
    for c in CT_TRADITIONAL:
        out[("CT", c)] = f"{c} County"
    return out


def counties(fips_to_code):
    """One SVG per state: every county's path in the shared projection, keyed by
    the value this project's county column uses for it."""
    topo = json.loads(COUNTIES.read_text(encoding="utf-8"))
    arcs = _decode_arcs(topo)
    names = county_display_names()
    per_state = {}
    for g in topo["objects"]["counties"]["geometries"]:
        code = fips_to_code.get(g["id"][:2])
        if not code or "arcs" not in g:
            continue
        base = g["properties"]["name"]
        # The six city/county pairs share a name; Census county codes of 500 and
        # above are the independent cities.
        value = base
        if (code, f"{base} city") in names and int(g["id"][2:]) >= 500:
            value = f"{base} city"
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
        rings = [_ring(r, arcs) for poly in polys for r in poly]
        outer = [_ring(poly[0], arcs) for poly in polys]
        _, (lx, ly) = max((_area_centroid(r) for r in outer), key=lambda t: t[0])
        st = per_state.setdefault(code, {"counties": [], "pts": []})
        st["counties"].append({"county": value, "name": names.get((code, value), value),
                               "fips": g["id"], "d": _path(rings),
                               "center": [round(lx, 1), round(ly, 1)]})
        st["pts"].extend(rings[0])
    out = {}
    for code, st in per_state.items():
        xs = [p[0] for p in st["pts"]]
        ys = [p[1] for p in st["pts"]]
        pad = 4
        out[code] = {"state": code,
                     "viewBox": [round(min(xs) - pad, 1), round(min(ys) - pad, 1),
                                 round(max(xs) - min(xs) + 2 * pad, 1),
                                 round(max(ys) - min(ys) + 2 * pad, 1)],
                     "source": "US Census Bureau cartographic county boundaries, 2017 edition, "
                               "via us-atlas 3.0.1 (data/raw/us-atlas/)",
                     "counties": sorted(st["counties"], key=lambda c: c["name"])}
    return out
