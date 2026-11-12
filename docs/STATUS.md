# Status (12 November 2026)

## Done
- Research and audits for all 50 states + DC, federal, the national business directory and all 10 regional business directories (California separate).
- Every report checked for completeness in Claude chat.
- Master list of 1,238 official sites (domains/).
- New England licence, town and business data rebuilt from official sources on 12 Nov 2026 (see docs/FILE_INDEX.md). USDA hemp list (May 2026) parsed.

## Next
1. Rebuild data/clean/new_england_licences.csv from the fresh files in data/raw/ (it is from 24 Oct), and add New Hampshire's dispensary sheet.
2. Post-election re-checks: Idaho HJR 4 (3 Nov 2026 ballot) and any other state with a 2026 cannabis measure; update Part 0 and Part 9 of those reports once results are certified.
3. Add the domain list to Claude Code's allowed sites.
4. Download every state's official licence files into data/raw/<state>/ and build one master licence table (schema in HANDOFF.md).
5. Build the business table from all directories; de-duplicate across directories and merge national firms under parent profiles.
6. Build the site.

## Open loose ends
- Talaria: treat as a licensed operator everywhere (moved out of Mid-Atlantic directory as an NJ wholesaler, still in Great Lakes).
- CropLine (NV): link to Green Therapeutics' licence, not the directory.
- Crested River Cannabis Company (MN): confirm licence and move.
- Coastal Cannabis Consulting (LA): founder tied to a pharmacy licensee; decide.
- American Cannabis Company (CO): ownership unverified.
- California businesses: 242 of 371 unverified; match every name against the DCC licence download and CDPH hemp registrations.
- California state report (R91) and Michigan (R56) audits are light; check law and tax pages against official sites.
- New Hampshire audit is light (about 42 rows).
- New Jersey audit is lighter than the rest (about 78 claims).
- Arkansas Act 629 enrolled text and Act 934 changes: check before quoting.
- Market figures for Utah, Arizona, New Mexico and Mississippi came from secondary summaries; replace with official figures.
- Thin domain lists (Iowa, Arkansas, Wyoming, Tennessee): add official sites as found.
