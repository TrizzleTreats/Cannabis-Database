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
