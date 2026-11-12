# Status (12 November 2026)

## Done
- Research and audits for all 50 states + DC, federal, the national business directory and all 10 regional business directories (California separate).
- Every report checked for completeness in Claude chat. Re-checked in Claude Code on 12 Nov 2026: all 64 files in docs/FILE_INDEX.md are present, none missing, none truncated, nothing on disk outside the index.
- Git repository started (local only, no remote). data/private/ is git-ignored and nothing under it is tracked. CLAUDE.md now names the private columns that live inside tracked data/clean/ files, so the public build has something authoritative to strip against.
- Master list of 1,242 official sites, allowed to Claude Code in .claude/settings.json as WebFetch(domain:...) rules. Four hosts were added during the build: paauditor.b-cdn.net, content.govdelivery.com, www.arcgis.com, maryland.maps.arcgis.com. einpresswire.com was deliberately left out as a secondary news reprint.
- New England licence table rebuilt from data/raw/ on 12 Nov 2026 (scripts/build_new_england.py): 3,917 to 4,267 rows. CT 253 to 498, MA 967 to 1,072; ME, VT, RI and NH carried forward unchanged because their raw files hold nothing the table did not already have. A `standard_status` column was added so one search spans all six states.
- Mid-Atlantic raw licence data captured for all six jurisdictions (scripts/fetch_raw.py, declared in scripts/sources.json, logged in data/raw/manifest.csv). 23 of 24 declared sources fetched.
- USDA hemp list (May 2026) parsed.

## Next
1. Post-election re-checks: Idaho HJR 4 (3 Nov 2026 ballot) and any other state with a 2026 cannabis measure; update Part 0 and Part 9 of those reports once results are certified.
2. Build the Mid-Atlantic clean tables from data/raw/ into the master licence schema. Nothing in data/clean/ has been written for the Mid-Atlantic yet — raw capture only.
3. Fill the 128 rows that still have no county (CT 84, ME 23, MA 19, RI 2). CLAUDE.md requires a county for every town; these are left empty rather than guessed.
4. Extend the download pattern to Regions 3-9 (44 states). scripts/sources.json is the template.
5. Build the business table from all directories; de-duplicate across directories and merge national firms under parent profiles.
6. Build the site.

## What the build corrected in the research
These are findings from the official sources themselves, not re-readings of the reports. Each needs folding back into the relevant state report.
- **CT**: ngch-56tr had been downloaded filtered to cannabis credential types only, so 280 hemp and THC-beverage credentials were missing — including the 104 live rows the master table was carrying with the wrong source label. Filter on `credential`, never `credentialtype`: types CSM and CSW are shared with "MANUFACTURER / WHOLESALER OF DRUGS, COSMETICS & MEDICAL DEVICES" and pull in roughly 4,300 unrelated pharmacy licences.
- **MD**: Part 5 recorded the MCA data dashboard as 404 and concluded MCA publishes no downloadable registry. The dashboard is live and carries an "Accessible Data Extract" XLSX dated Sept 2026, and the Dispensary Locator holds a 130-row table with a county for each dispensary. Maryland is not a no-download state. Resolved paths: /Pages/Data-Dashboard.aspx, /Pages/Dispensary-Locator.aspx, /Pages/Industry_Licensees_and_Registrants.aspx.
- **DC**: the retailer GIS layer Part 5 said not to guess is layer 31 of the Health_WebMercator MapServer — 79 retailers, 77 Active, 1 Safekeeping with Location, 1 Emergency Closure, with a ward for each. The non-retailer layer 33 gives the by-type counts Part 5 had to leave as VERIFY: 9 cultivation, 10 manufacturers, 1 courier, 1 testing lab, all Active.
- **PA**: a 23 Sept 2026 MMAB presentation exists. The audit recorded that the page listed a Sept agenda but no presentation, so its 24 June 2026 metrics are no longer the latest. The DOH growers-processors page carries no permittee-list PDF at all — only guidance forms.
- **MA**: licence MP281798 is Suspended as of 27 Oct 2026 but the old table showed it "Active; Final License; operating". Two further suspended licences were absent entirely. The rebuild represents all three.

## Open loose ends
- NY hemp producer list: agriculture.ny.gov returns HTTP 403 to programmatic clients and a file download to the browser pane, so neither the HTML list nor the PDF could be captured. Needs a manual download. Note it carries personal emails — private columns only.
- MD dashboard extract (XLSX) is stored raw but unparsed: openpyxl is not installed.
- MD dispensary locator also drives an ArcGIS instant app (appid 51f75b68c70f4c6d8ab0aa4f4de74f55 on maryland.maps.arcgis.com); its underlying feature service is not yet resolved.
- PA hemp permit map is Power BI at cedatareporting.pa.gov and was not attempted; Part 5 records a live fetch returning only "Loading data...".
- DC: the GIS retailer count (77 Active, Nov 2026) is NOT a correction to ABCA's 66 retailers (Aug 2026 report) — different source and date. Do not reconcile them into one number.
- NY: the OCM dataset has 3,056 rows but only 2,286 distinct licence numbers, and 385 rows carry no licence number at all — those are applicants under proximity protection. Row count is not a licence count, and neither figure should be compared directly with the OCM 2025 Annual Report's 2,008 active (30 Nov 2025).
- CT: 465 records in the fresh download are applications that never became licences (DENIED, EXPIRED APPLICATION / NSF PAYMENT DUE, WITHDRAWN, INSPECTION INCOMPLETE) and are excluded from the licence table. The rule is in scripts/build_new_england.py; it keys on statusreason, not status, because "EXPIRED APPLICATION / PROVISIONAL LICENSE EXPIRED" was a real licence.
- Talaria: treat as a licensed operator everywhere (moved out of Mid-Atlantic directory as an NJ wholesaler, still in Great Lakes).
- CropLine (NV): link to Green Therapeutics' licence, not the directory.
- Crested River Cannabis Company (MN): confirm licence and move.
- Coastal Cannabis Consulting (LA): founder tied to a pharmacy licensee; decide.
- American Cannabis Company (CO): ownership unverified.
- California businesses: 242 of 371 unverified; match every name against the DCC licence download and CDPH hemp registrations.
- California state report (R91) and Michigan (R56) audits are light; check law and tax pages against official sites.
- New Hampshire audit is light (about 42 rows). Its 7 ATC rows were hand-transcribed from a DHHS PDF and still have no stored raw file.
- New Jersey audit is lighter than the rest (about 78 claims).
- Arkansas Act 629 enrolled text and Act 934 changes: check before quoting.
- Market figures for Utah, Arizona, New Mexico and Mississippi came from secondary summaries; replace with official figures.
- Thin domain lists (Iowa, Arkansas, Wyoming, Tennessee): add official sites as found.
