"""Which raw file is current for each source, and the date it was read.

The builders used to name each raw file by its download date
("..._2026-11-12.csv") and stamp a fixed TODAY on every row. A daily fetch could then
never move the data: new downloads would go unread, or overwrite a file whose name
and rows still said 12 November.

The manifest (data/raw/manifest.csv) already logs every fetch: when, which source id,
which file, and whether it was good. This module reads it:

  current(rel)        the newest good file of the same source as `rel` (a path the
                      builders know, relative to data/raw/), and the date it was read.
  current_by_id(id)   the same, by source id.
  declared(state)     the current file for every source declared for a state, so a
                      builder that reads a whole folder (Colorado's sheets) reads one
                      file per source, never an old and a new copy of the same sheet.

"Good" is status "ok" (new bytes, saved) or "ok: unchanged" (downloaded again, same
bytes as the current file, nothing saved). A row's date is the day its file's bytes were
first saved, so it changes only when the regulator's data changes; the daily check is
recorded in the manifest and returned by last_checked(). A suspect or failed fetch is
never current: the builders keep using the last good file, with its own date.

A file the manifest does not know (Massachusetts' two files predate the fetcher) is
returned as given, with no date; the builder then uses its documented fallback.
"""
import csv, functools, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
MANIFEST = RAW / "manifest.csv"
SOURCES = pathlib.Path(__file__).resolve().parent / "sources.json"
GOOD = ("ok", "ok: unchanged")


@functools.lru_cache(maxsize=1)
def _manifest():
    if not MANIFEST.exists():
        return ()
    with open(MANIFEST, newline="", encoding="utf-8") as f:
        return tuple(csv.DictReader(f))


def reload():
    """Forget the cached manifest and declarations (after a fetch has appended)."""
    _manifest.cache_clear()
    _declared.cache_clear()


@functools.lru_cache(maxsize=1)
def _declared():
    return tuple(json.loads(SOURCES.read_text(encoding="utf-8")))


def source_id(rel):
    """The source a builder's path belongs to: by its declaration in sources.json
    first (the declared filename is the name a builder knows), then by any fetch the
    manifest has logged under that name."""
    state, _, name = rel.partition("/")
    for s in _declared():
        if s["state"] == state and s["filename"] == name:
            return s["id"]
    for r in _manifest():
        if r["state"] == state and r["filename"] == name:
            return r["id"]
    return None


def current_by_id(sid):
    """(Path, 'YYYY-MM-DD' or None): the current file of source `sid` and the day those
    bytes were first saved. A later "ok: unchanged" check does not move that date, so an
    unchanged source does not rewrite every row's date each day; the check itself is
    in the manifest (see last_checked). None if the file predates the fetcher's log."""
    good = [r for r in _manifest()
            if r["id"] == sid and r["status"] in GOOD
            and (RAW / r["state"] / r["filename"]).exists()]
    if not good:
        return None, None
    latest = max(good, key=lambda r: r["fetched_at"])
    saved = [r["fetched_at"] for r in good
             if r["filename"] == latest["filename"] and r["status"] == "ok"]
    return RAW / latest["state"] / latest["filename"], (min(saved)[:10] if saved else None)


def last_checked(sid):
    """The most recent day source `sid` was downloaded with a good result, changed or not."""
    good = [r["fetched_at"] for r in _manifest() if r["id"] == sid and r["status"] in GOOD]
    return max(good)[:10] if good else None


def current(rel):
    """(Path, read date or None) for the file a builder names as `rel`."""
    sid = source_id(rel)
    if sid:
        path, read_on = current_by_id(sid)
        if path:
            return path, read_on
    return RAW / rel, None


def declared(state, suffix=""):
    """[(source id, Path, read date)] for every source declared for `state` that has
    a good file on disk, optionally only files ending in `suffix`."""
    out = []
    for s in _declared():
        if s["state"] != state:
            continue
        path, read_on = current_by_id(s["id"])
        if path and path.name.endswith(suffix):
            out.append((s["id"], path, read_on))
    return sorted(out, key=lambda t: t[1].name)


def resolve(rel, documented):
    """(Path, data_as_of) for a builder that names `rel` and documents a date for it.

    While the current file is still the one `rel` names, the documented date stands:
    for many sources it is the regulator's own "as of" date, read off the file when
    the spec was written, which is more precise than the day it was downloaded. Once
    a newer download is current, that documented date describes a file no longer
    used, so the date becomes the day the new file was read. (Parsing each
    regulator's own date out of each new file is a per-source refinement still to
    do; until then a refreshed row says when it was read, never a stale date.)"""
    path, read_on = current(rel)
    if path.name == pathlib.PurePath(rel).name or not read_on:
        return path, documented
    return path, read_on


def resolve_declared(state, suffix, documented):
    """[(Path, data_as_of)] for every declared source of `state`, by the same rule."""
    names = {s["id"]: s["filename"] for s in _declared() if s["state"] == state}
    return [(path, documented if path.name == names.get(sid) or not read_on else read_on)
            for sid, path, read_on in declared(state, suffix)]
