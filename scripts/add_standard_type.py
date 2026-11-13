#!/usr/bin/env python3
"""Write `standard_type` and `standard_types_all` into the three licence tables.

The mapping and the reasoning behind every non-obvious call live in
scripts/standard_types.py and docs/HANDOFF.md. This script only applies them.

`category` and `licence_type` are never touched: the regulator's own official
licence name stays in licence_type for the state pages, and the build's own
grouping stays in category. The new columns sit after licence_type, which is
where HANDOFF's column list puts the standard type, and mirror how
standard_status sits directly after status.

Idempotent, so a re-run after a rebuild is safe. It refuses to write at all if
any row carries a category the mapping does not know - an unmapped category is
a decision for HANDOFF.md, and a silent blank in a search column would read as
"no such licence" rather than "not classified yet".

Usage:
  python3 scripts/add_standard_type.py            # report what would change
  python3 scripts/add_standard_type.py --apply    # write the tables
"""
import argparse, collections, csv, pathlib, sys

from standard_types import CATEGORY_TO_TYPES, STANDARD_TYPES, types_for

ROOT = pathlib.Path(__file__).resolve().parent.parent
TABLES = ["new_england_licences.csv", "mid_atlantic_licences.csv",
          "regions_3_to_9_licences.csv"]
NEW_COLS = ["standard_type", "standard_types_all"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write the tables")
    args = ap.parse_args()

    all_rows, unmapped = {}, collections.Counter()
    for name in TABLES:
        path = ROOT / "data/clean" / name
        if not path.exists():
            sys.exit(f"{name} is not built yet")
        with open(path, encoding="utf-8") as f:
            all_rows[name] = list(csv.DictReader(f))
        for r in all_rows[name]:
            if r["category"] not in CATEGORY_TO_TYPES:
                unmapped[(r["state"], r["category"], r["licence_type"])] += 1

    if unmapped:
        print("Refusing to write - these categories have no standard type:")
        for (st, cat, lt), n in unmapped.most_common():
            print(f"  {n:>6}  {st}  {cat!r}  (licence_type {lt!r})")
        print("\nDecide each one in docs/HANDOFF.md and add it to "
              "scripts/standard_types.py. Do not let it default.")
        sys.exit(1)

    lead_count, multi, per_state = collections.Counter(), collections.Counter(), {}
    for name in TABLES:
        rows = all_rows[name]
        for r in rows:
            lead, every = types_for(r["category"], r["licence_type"])
            r["standard_type"], r["standard_types_all"] = lead, every
            lead_count[lead] += 1
            if "; " in every:
                multi[(r["state"], r["category"], every)] += 1
        per_state[name] = collections.Counter(
            (r["state"], r["standard_type"]) for r in rows)

    total = sum(lead_count.values())
    print(f"{total:,} rows across {len(TABLES)} tables\n")
    print("standard_type (the lead activity, one per row)")
    for t in STANDARD_TYPES:
        n = lead_count.get(t, 0)
        print(f"  {n:>7,}  {t}" + ("   <- no rows" if not n else ""))
    missing = [t for t in STANDARD_TYPES if not lead_count.get(t)]
    if missing:
        print(f"\n  {len(missing)} of the 16 types lead no row: {', '.join(missing)}")
        print("  That is a fact about the 26 built jurisdictions, not an error.")

    n_multi = sum(multi.values())
    print(f"\nmulti-activity licences: {n_multi} rows "
          f"({total - n_multi:,} carry a single type)")
    for (st, cat, every), n in multi.most_common():
        print(f"  {n:>4}  {st}  {cat!r}")
        print(f"        -> standard_types_all {every!r}")

    if not args.apply:
        print("\nNothing written. Re-run with --apply.")
        return

    for name in TABLES:
        rows = all_rows[name]
        cols = [c for c in rows[0].keys() if c not in NEW_COLS]
        at = cols.index("licence_type") + 1
        cols[at:at] = NEW_COLS
        with open(ROOT / "data/clean" / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in rows:
                w.writerow({c: r.get(c, "") for c in cols})
        print(f"\n{name}: {len(rows):,} rows x {len(cols)} columns written")

    print("\nper state, leading standard_type:")
    for name in TABLES:
        for st in sorted({s for s, _ in per_state[name]}):
            d = {t: n for (s, t), n in per_state[name].items() if s == st}
            top = sorted(d.items(), key=lambda kv: -kv[1])
            print(f"  {st}: " + ", ".join(f"{t} {n}" for t, n in top))


if __name__ == "__main__":
    main()
