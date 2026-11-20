/* Cannabis Database — shared front-end helpers.
   Plain ES modules, no framework and no build step: the data is static JSON
   written by scripts/build_site_data.py, and the project intends the site to
   update itself from scripts rather than from a toolchain. */

export const DATA = "data";

export async function loadJSON(path) {
  const res = await fetch(`${DATA}/${path}`);
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

export const fmt = (n) => (n ?? 0).toLocaleString("en-US");

export function el(tag, attrs = {}, ...kids) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  for (const kid of kids.flat()) {
    if (kid === null || kid === undefined || kid === false) continue;
    node.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
  }
  return node;
}

/* The ten standard statuses, grouped only for colour. The regulator's own
   wording always stays on the row — this is the standard value's shade. */
const LIVE = new Set(["Active", "Provisional", "Limited Operations"]);
const WAITING = new Set(["Pending", "Suspended"]);

export function statusBadge(standard, own) {
  if (!standard) {
    return el("span", {
      class: "badge none",
      title: own
        ? `The regulator publishes no status for this licence. Its own wording: ${own}`
        : "The regulator publishes no status for this licence. Empty is not Active.",
      text: "not published",
    });
  }
  const shade = LIVE.has(standard) ? "active" : WAITING.has(standard) ? "pending" : "dead";
  return el("span", {
    class: `badge ${shade}`,
    title: own ? `The regulator's own wording: ${own}` : "",
    text: standard,
  });
}

/* Filters live in the URL, so a filtered view can be linked and a licence
   type on a state page can open the database already narrowed. */
export function readParams(defaults) {
  const q = new URLSearchParams(location.search);
  const out = { ...defaults };
  for (const key of Object.keys(defaults)) {
    if (q.has(key)) out[key] = q.get(key);
  }
  return out;
}

export function writeParams(state, defaults) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(state)) {
    if (v && v !== defaults[k]) q.set(k, v);
  }
  const url = q.toString() ? `?${q}` : location.pathname;
  history.replaceState(null, "", url);
}

export function debounce(fn, ms = 180) {
  let t;
  return (...a) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...a), ms);
  };
}

/* CSV export of exactly what is on screen. Quotes every field, because
   business names carry commas and descriptions carry quotes. */
export function toCSV(rows, columns) {
  const esc = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const lines = [columns.map((c) => esc(c.label)).join(",")];
  for (const r of rows) lines.push(columns.map((c) => esc(c.get(r))).join(","));
  return lines.join("\r\n");
}

export function download(name, text, type = "text/csv") {
  const url = URL.createObjectURL(new Blob([text], { type: `${type};charset=utf-8` }));
  const a = el("a", { href: url, download: name });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function sortRows(rows, key, dir) {
  const sign = dir === "descending" ? -1 : 1;
  return [...rows].sort((a, b) => {
    const x = (a[key] ?? "").toString().toLowerCase();
    const y = (b[key] ?? "").toString().toLowerCase();
    if (x === y) return 0;
    if (x === "") return 1;        // blanks last, whichever direction
    if (y === "") return -1;
    return x < y ? -sign : sign;
  });
}

/* Every page carries it — HANDOFF: "Footer on every page: 'legal information,
   not legal advice' linking to full terms." */
export function mountFooter(host) {
  host.append(
    el("footer", { class: "disclaimer" },
      el("p", {},
        el("strong", { text: "This is legal information, not legal advice. " }),
        "Cannabis and hemp law changes often and differs by state, county and city. ",
        "Nothing here is a substitute for advice from a lawyer licensed in your jurisdiction. ",
        el("a", { href: "terms.html" }, "Full terms and sources"),
        "."),
      el("p", {},
        "Every figure on this site comes from an official government source and carries the ",
        "date it was read. Counts are not interchangeable: ",
        el("em", { text: "issued" }), ", ", el("em", { text: "approved" }), ", ",
        el("em", { text: "licensed" }), ", ", el("em", { text: "pending renewal" }), " and ",
        el("em", { text: "operating" }), " are different measures and are never added together."),
    ));
}

export function mountTopbar(host, current) {
  const link = (href, label) =>
    el("a", { href, ...(href === current ? { "aria-current": "page" } : {}) }, label);
  host.prepend(
    el("nav", { class: "topbar" },
      el("span", { class: "wordmark", text: "US Cannabis & Hemp Law" }),
      link("index.html", "Home"),
      link("database.html", "Database"),
      link("federal.html", "Federal law"),
    ));
}

/* ------------------------------------------------------------ licence records
   A state's full public records are split into buckets by an FNV-1a hash of the
   licence id (scripts/build_site_data.py, bucket()). This is the same function;
   if one changes, the other must too. */
export function bucketOf(id, nb) {
  let h = 0x811c9dc5;
  for (let i = 0; i < id.length; i++) {
    h = Math.imul((h ^ id.charCodeAt(i)) >>> 0, 0x01000193) >>> 0;
  }
  return h % nb;
}

const bucketCache = {};
export async function loadLicence(state, id, summary) {
  const nb = summary?.states?.[state]?.detail_buckets;
  if (!nb) return null;
  const key = `${state}/${bucketOf(id, nb)}`;
  if (!bucketCache[key]) {
    const data = await loadJSON(`licences/detail/${key}.json`);
    bucketCache[key] = Object.fromEntries(data.licences.map((x) => [x.licence_id, x]));
  }
  return bucketCache[key][id] || null;
}

export const profileHref = (d) =>
  `licence.html?state=${encodeURIComponent(d.state)}&id=${encodeURIComponent(d.licence_id)}`;

const fact = (label, value) => (value ? [el("dt", { text: label }), el("dd", {}, value)] : []);

/* The full public record of one licence: heading, facts, the row's own flags,
   and its source. Used by the Database's side panel and by the profile page. */
export function licenceDetail(d, opts = {}) {
  // replaceChildren() would print a null as the text "null", so drop them here.
  return licenceDetailParts(d, opts).filter((x) => x !== null && x !== undefined);
}

function licenceDetailParts(d, { heading = "h3" } = {}) {
  // extra_details is "key=value; key=value" — the per-row flags the build wrote.
  const flags = (d.extra_details || "").split("; ").filter(Boolean);
  const county = d.county
    ? el("a", { href: `county.html?state=${d.state}&county=${encodeURIComponent(d.county)}` },
        `${d.county} County`)
    : null;
  return [
    el(heading, { text: d.legal_name || "(the regulator publishes no name)" }),
    el("p", { class: "sub" }, [d.dba && `trading as ${d.dba}`, d.licence_id].filter(Boolean).join(" · ")),
    el("dl", {},
      fact("Licence type", d.licence_type),
      fact("Standard type", d.standard_types_all || d.standard_type),
      fact("Programme", d.program),
      fact("Status", d.status),
      fact("Standard status", statusBadge(d.standard_status, d.status)),
      fact("Tier", d.tier),
      fact("Issued", d.issue_date),
      fact("First issued", d.first_issue_date),
      fact("Expires", d.expiry_date),
      // Most regulators put the town inside the address already; add it only when absent.
      fact("Address", d.street_address && d.town
        && !d.street_address.toLowerCase().includes(d.town.toLowerCase())
        ? `${d.street_address}, ${d.town}` : (d.street_address || d.town)),
      fact("Town", d.town ? el("a", { href: townHref(d.state, d.county, d.town) }, d.town) : ""),
      fact("County", county),
      fact("Town as listed", d.town_as_listed !== d.town ? d.town_as_listed : ""),
      fact("County source", d.county_source),
      fact("Location basis", d.location_basis),
      fact("Website", d.website && el("a", { href: d.website, target: "_blank", rel: "noopener" }, d.website)),
      fact("Part of", d.linked_group && `${d.linked_group} (${d.licences_in_group} licences)`),
    ),
    flags.length
      ? el("div", { class: "flags" },
          el("b", { text: "What this row says about itself" }),
          el("ul", { style: "margin:.4rem 0 0; padding-left:1.1rem" },
            flags.map((f) => el("li", { text: f }))))
      : null,
    el("p", { class: "source" },
      d.source || "",
      d.source_url ? [" — ", el("a", { href: d.source_url, target: "_blank", rel: "noopener" }, "source")] : "",
      d.data_as_of ? ` · read ${d.data_as_of}` : ""),
  ];
}

/* ------------------------------------------------------------- county maps
   One state's counties from site/data/counties/<ST>.json. Uncoloured on
   purpose: HANDOFF puts county colour-coding in "later, not now", so the map
   is navigation, and the counts are in the tooltip and the tables. */
export const countyHref = (state, county) =>
  `county.html?state=${encodeURIComponent(state)}&county=${encodeURIComponent(county)}`;

export const townHref = (state, county, town) =>
  `town.html?state=${encodeURIComponent(state)}&county=${encodeURIComponent(county || "")}`
  + `&town=${encodeURIComponent(town)}`;

export function countyMap(cm, { counts = {}, highlight = null, link = true, label = "" } = {}) {
  const SVG = "http://www.w3.org/2000/svg";
  const make = (tag, attrs = {}) => {
    const n = document.createElementNS(SVG, tag);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    return n;
  };
  const svg = make("svg", { class: "countymap", viewBox: cm.viewBox.join(" "), role: "group",
    "aria-label": label || `Map of the counties of ${cm.state}` });
  for (const c of cm.counties) {
    const n = counts[c.county] || 0;
    const tip = `${c.name}${n ? ` — ${n.toLocaleString("en-US")} licence records` : ""}`;
    const path = make("path", { d: c.d, class: c.county === highlight ? "on" : "" });
    const title = make("title"); title.textContent = tip;
    if (link) {
      const a = make("a", { href: countyHref(cm.state, c.county), "aria-label": tip });
      a.append(title, path);
      svg.append(a);
    } else {
      path.append(title);
      svg.append(path);
    }
  }
  return svg;
}
