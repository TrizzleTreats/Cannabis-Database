#!/usr/bin/env python3
"""Read .xlsx without openpyxl, which is not installed on this machine.

An xlsx is a zip of XML, so the sheet and its shared-string table can be parsed
directly. Enough of the format is handled for regulator exports: shared strings,
inline strings, numbers, booleans, and the 1900-epoch date serials these files
use for issue and expiry dates. Blank cells are preserved by column letter, so a
row never silently shifts left when a cell is empty.

Usage:
  python3 scripts/xlsx_reader.py <file.xlsx> [--sheet N] [--csv out.csv] [--head N]
"""
import argparse, csv, re, sys, zipfile
from datetime import date, timedelta
from xml.etree import ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
EPOCH = date(1899, 12, 30)   # Excel's 1900 system, with its leap-year bug


def col_index(ref):
    """'BC12' -> 54 (zero-based column number)."""
    letters = re.match(r"([A-Z]+)", ref or "A").group(1)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def shared_strings(z):
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    out = []
    for si in ET.fromstring(z.read("xl/sharedStrings.xml")):
        # a string may be split across several runs
        out.append("".join(t.text or "" for t in si.iter(f"{NS}t")))
    return out


def date_styles(z):
    """Style ids whose number format is a date, so serials can be rendered."""
    if "xl/styles.xml" not in z.namelist():
        return set()
    root = ET.fromstring(z.read("xl/styles.xml"))
    custom = {}
    for nf in root.iter(f"{NS}numFmt"):
        custom[nf.get("numFmtId")] = nf.get("formatCode", "")
    builtin_date = {str(i) for i in list(range(14, 23)) + list(range(45, 48)) + [27, 30, 36, 50, 57]}
    out = set()
    xfs = root.find(f"{NS}cellXfs")
    if xfs is None:
        return out
    for i, xf in enumerate(xfs):
        fid = xf.get("numFmtId")
        code = custom.get(fid, "")
        if fid in builtin_date or re.search(r"(?<!\\)[dmyh]", code or "", re.I) and "0.00" not in (code or ""):
            out.add(str(i))
    return out


def sheet_paths(z):
    names = [n for n in z.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n)]
    return sorted(names, key=lambda n: int(re.search(r"(\d+)", n).group(1)))


def read(path, sheet=0):
    """Return a list of rows, each a list of strings."""
    with zipfile.ZipFile(path) as z:
        strings = shared_strings(z)
        dstyles = date_styles(z)
        paths = sheet_paths(z)
        if not paths:
            raise SystemExit(f"{path}: no worksheets found")
        root = ET.fromstring(z.read(paths[min(sheet, len(paths) - 1)]))
        rows = []
        for r in root.iter(f"{NS}row"):
            cells = {}
            for c in r.iter(f"{NS}c"):
                t, s = c.get("t"), c.get("s")
                v = c.find(f"{NS}v")
                if t == "inlineStr":
                    isel = c.find(f"{NS}is")
                    val = "".join(x.text or "" for x in isel.iter(f"{NS}t")) if isel is not None else ""
                elif t == "s":
                    i = int(v.text) if v is not None and v.text else -1
                    val = strings[i] if 0 <= i < len(strings) else ""
                elif t == "b":
                    val = "TRUE" if (v is not None and v.text == "1") else "FALSE"
                else:
                    val = v.text if v is not None and v.text is not None else ""
                    if val and s in dstyles:
                        try:
                            val = (EPOCH + timedelta(days=float(val))).isoformat()
                        except (ValueError, OverflowError):
                            pass
                cells[col_index(c.get("r"))] = (val or "").strip()
            if cells:
                width = max(cells) + 1
                rows.append([cells.get(i, "") for i in range(width)])
        return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file"), ap.add_argument("--sheet", type=int, default=0)
    ap.add_argument("--csv"), ap.add_argument("--head", type=int, default=5)
    a = ap.parse_args()
    rows = read(a.file, a.sheet)
    if a.csv:
        width = max((len(r) for r in rows), default=0)
        with open(a.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            for r in rows:
                w.writerow(r + [""] * (width - len(r)))
        print(f"wrote {a.csv} — {len(rows)} rows x {width} cols")
    else:
        print(f"{len(rows)} rows")
        for r in rows[:a.head]:
            print("  ", r[:12])


if __name__ == "__main__":
    main()
