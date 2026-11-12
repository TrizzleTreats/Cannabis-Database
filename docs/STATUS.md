# Status (12 November 2026)

## Done
- Research and audits for all 50 states + DC, federal, the national business directory and all 10 regional business directories (California separate).
- Every report checked for completeness in Claude chat. Re-checked in Claude Code on 12 Nov 2026: all 64 files in docs/FILE_INDEX.md are present, none missing, none truncated, nothing on disk outside the index.
- Git repository started (local only, no remote). data/private/ is git-ignored and nothing under it is tracked. CLAUDE.md now names the private columns that live inside tracked data/clean/ files, so the public build has something authoritative to strip against.
- Master list of 1,242 official sites, allowed to Claude Code in .claude/settings.json as WebFetch(domain:...) rules. Four hosts were added during the build: paauditor.b-cdn.net, content.govdelivery.com, www.arcgis.com, maryland.maps.arcgis.com. einpresswire.com was deliberately left out as a secondary news reprint.
- New England licence table rebuilt from data/raw/ on 12 Nov 2026 (scripts/build_new_england.py): 3,917 to 4,267 rows. CT 253 to 498, MA 967 to 1,072; ME, VT, RI and NH carried forward unchanged because their raw files hold nothing the table did not already have. A `standard_status` column was added so one search spans all six states.
- Mid-Atlantic raw licence data captured for all six jurisdictions (scripts/fetch_raw.py, declared in scripts/sources.json, logged in data/raw/manifest.csv). 23 of 24 declared sources fetched.
- Mid-Atlantic clean table built: data/clean/mid_atlantic_licences.csv, 4,067 rows (scripts/build_mid_atlantic.py). NY 3,056, NJ 586, PA 181, MD 130, DC 100, DE 14. Same 41 columns as the New England table, in the same order, so the two union cleanly (8,334 rows combined).
- Regions 3-9 started: data/clean/regions_3_to_9_licences.csv, 41,026 rows across 7 of 39 jurisdictions (scripts/build_states.py). CA 20,984, TX 12,853, OR 3,701, CO 1,832, WA 1,226, NV 345, AL 85. Same 41 columns as the other two tables, so all three union to 49,360 rows.
- USDA hemp list (May 2026) parsed.

## Next
1. Post-election re-checks: Idaho HJR 4 (3 Nov 2026 ballot) and any other state with a 2026 cannabis measure; update Part 0 and Part 9 of those reports once results are certified.
2. Fill the counties the regulators do not publish: PA 181, NJ 586, DE 14 rows have none at all, plus NY 306, CT 84, ME 23, MA 19, MD 3, RI 2. CLAUDE.md requires a county for every town; all are left empty rather than guessed. A town-to-county gazetteer per state is the missing piece.
3. Resolve the licence numbers PA, NJ, MD and DE do not publish in their public lists. NJ's are in per-facility licence PDFs linked from the CRC page (e.g. RE000900); the other three publish none anywhere found so far.
4. Finish Regions 3-9: 32 of 39 jurisdictions remain. The two blockers are a PDF text extractor (none installed; 2,219 discovered files are PDFs) and browser-pane runs for the portal and bot-checked states. scripts/sources.json plus a spec in scripts/build_states.py is the pattern — adding a state is adding a spec.
5. Decide the schema gaps the real data surfaced: licence types "Event Organizer" and "Operator", and statuses "Canceled", "Limited Operations" and "Inactive".
6. Build the business table from all directories; de-duplicate across directories and merge national firms under parent profiles.
7. Build the site.

## What the build corrected in the research
These are findings from the official sources themselves, not re-readings of the reports. Each needs folding back into the relevant state report.
- **CT**: ngch-56tr had been downloaded filtered to cannabis credential types only, so 280 hemp and THC-beverage credentials were missing — including the 104 live rows the master table was carrying with the wrong source label. Filter on `credential`, never `credentialtype`: types CSM and CSW are shared with "MANUFACTURER / WHOLESALER OF DRUGS, COSMETICS & MEDICAL DEVICES" and pull in roughly 4,300 unrelated pharmacy licences.
- **MD**: Part 5 recorded the MCA data dashboard as 404 and concluded MCA publishes no downloadable registry. The dashboard is live and carries an "Accessible Data Extract" XLSX dated Sept 2026, and the Dispensary Locator holds a 130-row table with a county for each dispensary. Maryland is not a no-download state. Resolved paths: /Pages/Data-Dashboard.aspx, /Pages/Dispensary-Locator.aspx, /Pages/Industry_Licensees_and_Registrants.aspx.
- **DC**: the retailer GIS layer Part 5 said not to guess is layer 31 of the Health_WebMercator MapServer — 79 retailers, 77 Active, 1 Safekeeping with Location, 1 Emergency Closure, with a ward for each. The non-retailer layer 33 gives the by-type counts Part 5 had to leave as VERIFY: 9 cultivation, 10 manufacturers, 1 courier, 1 testing lab, all Active.
- **PA**: a 23 Sept 2026 MMAB presentation exists. The audit recorded that the page listed a Sept agenda but no presentation, so its 24 June 2026 metrics are no longer the latest. The DOH growers-processors page carries no permittee-list PDF at all — only guidance forms.
- **MA**: licence MP281798 is Suspended as of 27 Oct 2026 but the old table showed it "Active; Final License; operating". Two further suspended licences were absent entirely. The rebuild represents all three.

## Regions 3-9: what each of the 39 jurisdictions actually publishes

Built so far — 13 of 39, and they include the large markets:

| State | Rows | Source | What it gives |
|---|---|---|---|
| CA | 20,984 | DCC Cannabis Unified License Search API | Whole universe, 7 statuses, county, owners, coordinates, Adult-Use/Medicinal designation |
| TX | 12,853 | DSHS consumable-hemp and retail-hemp lists | Hemp licences with county; Texas licenses no adult-use or broad medical |
| OR | 3,701 | OLCC Socrata dataset q32u-cmam | County, tier, canopy type, endorsements |
| CO | 1,832 | MED's nine public Google Sheets, all 18 tabs | Medical AND retail across every category; no county published |
| WA | 1,226 | LCB Frequently Requested Lists | Retail only, with county; producers and processors not included |
| NV | 345 | CCB Cannabis Establishment List | Type, status, county; no premises address |
| FL | 289 | FDACS hemp cultivation licence list (PDF) | Licence number, issue date, responsible person; county on the 2025 records only |
| IL | 289 | Tableau view behind the Dispensary Locations map | Dispensaries with coordinates; no licence number, status or county |
| MO | 238 | DCR Verified Dispensary Locator (ArcGIS) | Licence number, county, website, coordinates |
| OH | 232 | DCC dispensary map (ArcGIS on maps.ohio.gov) | Licence number, legal name, DBA, county, status |
| HI | 94 | DOH Manufactured Hemp Product registry (PDF) | Registration number, validity dates; 19 online-only, 6 out-of-state registrants |
| AL | 85 | ABC Board consumable hemp list | Hemp retail only; medical (AMCC) is litigation-delayed |
| VA | 26 | VDACS hemp processors and approved labs (PDFs) | Firm, address, county |

Pennsylvania also improved: its dispensary source is now the DOH PDF (197 rows, product availability as of 10 Nov 2026) instead of the PASDA layer's 181 rows from Jan 2025. PASDA stays in data/raw/ for its coordinates.

**The ArcGIS trick that unlocked Ohio and Missouri.** Neither publishes a dispensary file; both embed a map. The route is: read the embed's item id, fetch `arcgis.com/sharing/rest/content/items/<id>/data?f=json`, follow the itemId it names to the web map or app config, and take the operational layer's FeatureServer URL. Ohio's sits on maps.ohio.gov, Missouri's on services6.arcgis.com. Nothing is guessed — each hop is read from the previous response. Illinois was the same shape but Tableau rather than ArcGIS: its CSV is at `/t/Public/views/<workbook>/<view>.csv`.

### Why the other 26 are not built yet

The audited reports cite landing pages, not files. Across all 39 reports only **9** machine-readable URLs appear, against **117 xlsx** and **2,219 PDFs** one hop deeper (scripts/discover_sources.py, logged in data/raw/discovered_sources.csv). A second hop was then run against the nine biggest remaining states — Michigan, Illinois, Ohio, Oklahoma, Arizona, Florida, Missouri, Minnesota and Colorado — and only Colorado yielded a licensee list. Michigan's hits were inspection checklists; Missouri's and Oklahoma's were product-recall lists. So for those eight there is **no downloadable licensee list reachable from the pages the reports cite**, and their data lives in interactive search portals, PDFs, or behind bot checks.

Two concrete blockers now stand in the way, and both have a known fix:

1. ~~No PDF text extraction.~~ **Resolved.** pypdf 7.0.1, openpyxl 3.1.5 and xlrd 2.0.2 are now installed. That immediately yielded Pennsylvania's current dispensary list, Florida's hemp licences and Virginia's processors and labs.
2. **Portals and bot checks need the browser pane.** Colorado proved the route: sbg.colorado.gov and med.colorado.gov both return a Cloudflare interstitial to any scripted client, and the nine sheet links were only readable through the browser pane. The same approach should work for Michigan's CRA search, Illinois' IDFPR lists, Oklahoma's OMMA search, Arizona's ADHS list, Florida's OMMU pages, Missouri's DCR search and Minnesota's OCM list.

**Minnesota is blocked by a CAPTCHA.** Its OCM "Application and License Holder Data" page serves a Radware Bot Manager hCaptcha to the browser pane. Solving or bypassing a CAPTCHA is off limits, so Minnesota needs a person to fetch that page by hand.

**Oklahoma publishes dated aggregate counts but no roster.** Its "Licensing and Tax Data" page carries a monthly table — as of 2 Nov 2026: 1,226 dispensaries, 1,582 growers, 545 processors, 42 transporters, 12 labs, 7 waste-disposal facilities, 1 education licence, 302,634 patients. Those are official, dated figures worth using for the Market tab and for reconciliation, but licensee-level data is only in OMMA's "Verify a License" portal. The table is in HTML accordions that need expanding before the rows exist in the DOM.

**Arizona** publishes no dispensary list file on either its Marijuana Licensing or Medical Marijuana pages; the only PDF-shaped "AZ licensed marijuana establishments" file found in the whole crawl sits on pamos.com, a private site, which the primary-sources-only rule excludes.

**Michigan is a special case worth recording.** Its CRA publishes monthly "Licensing Reports" as files named .doc that are actually RTF produced by Crystal Reports, and they parse cleanly. But they are *activity* reports — prequalifications, approvals and denials for that month, with name, licence id, address, date and determination — not a roster of current licensees. Building a Michigan roster from them would mean accumulating every month since 2019 and replaying the state changes, which is a different job from reading a list.

The remaining 22 states (AK, AR, GA, ID, IN, IA, KS, KY, LA, MS, MT, NE, NM, NC, ND, SC, SD, TN, UT, WV, WI, WY) have not been probed state by state through the browser pane yet. Most are small or medical-only programmes; several (ID, KS, NE, WY) license no cannabis at all beyond hemp, so their licence universe is hemp registrations.

### What the build corrected or found in regions 3-9

- **CO**: each of the MED's nine sheets has **two tabs, one medical and one retail**, and a Google Sheets CSV export without an explicit `gid` silently returns only the first. The first pass therefore produced a medical-only Colorado; declaring every tab by gid added 1,257 retail licences, including 636 retail stores.
- **OR**: OLCC withholds the premises address of producers, processors and wholesalers — 2,771 of 3,795 source rows say "Exempt from Public Disclosure". Only retailers and laboratories have public addresses.
- **OR**: OLCC publishes one row per licence *term*, so a renewed licence appears more than once (94 licences). Collapsed to the latest term with the earliest effective date kept as first_issue_date.
- **WA**: an LCB licence number belongs to the premises and survives an ownership transfer, so one number can carry both a closed and an active holder. The LCB file also holds near-duplicate rows differing only in ZIP+4 and phone.
- **CA**: the DCC returns the literal string "Data Not Available" for both names on 5 licences and "Not Published" for some premises. An earlier pass wrote "Data Not Available" into the town column; those are now blank and flagged.
- **CA**: the provisional-licence programme has wound down — 5,333 provisional licences are Expired and only 9 are both Active and provisional-term.
- **TX**: one hemp registration covers many outlets (a chain registers once and lists each store), so 12,217 source rows are 9,695 licences.
- **PA**: the DOH dispensary PDF carries the same King of Prussia ZIP of 19706 that the audit flagged in PASDA — so it is DOH's own error, not a PASDA transcription slip. Its two sibling King of Prussia rows carry 19406, and 19706 is a Delaware ZIP. Recorded as published and flagged, not rewritten.
- **FL**: FDACS leaves the county column blank on its 2026 records while populating it on the 2025 ones — 174 of 289 rows have no county.
- **IL**: the Tableau export repeats the "Dispensary Name" column twice and mixes 'Yes' with 'yes' in the medical-patients flag.
- **MO**: the DCR layer packs the licensee and its trading name into one semicolon-separated `Dispensary` value.
- **OH**: the DCC layer spells its own licence type three ways (Dual, Dual Use, Dual Use Dispensary) and its state two ways (Ohio, OH).
- **HI**: 19 of 94 registrants are online-only with no premises address at all, and 6 are registered from outside Hawaii (CA, TN, LA). DOH publishes no county, which is correct — Hawaii has no municipal government below county level.
- **Schema gaps surfaced by real data.** HANDOFF's 14 standard licence types have no entry for California's "Event Organizer" (193 rows) or Colorado's "Operator" (8). Its 7 standard statuses have no entry for California's "Canceled" (1,622) or "Limited Operations" (156), or OLCC's "Inactive" (796). Those rows carry the nearest standard value plus `standard_status_approximate=yes` in extra_details, so an approximation is never mistaken for the regulator's own word. **These need a schema decision.**

## Mid-Atlantic counts: what this table says vs what the reports say

These figures are different measures on different dates and must not be reconciled into single numbers.

| Jurisdiction | This table | Regulator / report figure | Why they differ |
|---|---|---|---|
| NY | 3,056 rows; 2,286 distinct licence numbers; 2,452 rows Active; 385 rows are live applications with no licence number | OCM 2025 Annual Report: 2,008 active across the five headline categories (30 Nov 2025) | A year later, one row per location rather than per licence, and the dataset includes proximity-protected applicants |
| DC | 79 retailers (77 Active) plus 21 non-retail facilities | ABCA August 2026 report: 66 total retailers | Different source and date; the GIS layer includes internet retailers. Do NOT treat 79 as a correction to 66 |
| PA | 181 dispensary locations | MMAB: 196 locations operational (1 June 2026); Auditor General: 195 "actively" | PASDA's layer is DOH Jan 2025 vintage, well before both |
| NJ | 586 organisation-location rows across 517 organisations | CRC: 541 businesses opened (Feb 2026); 397 licensed under CREAMM (Dec 2025) | CRC publishes organisations, not licences, and counts operating facilities in Metrc on a different basis |
| MD | 130 dispensaries: 127 storefronts and 3 delivery-only | MCA Jan 2026 briefing: 109 dispensaries operating | Ten months later, and the locator lists licensed rather than operating stores |
| DE | 14 storefronts across 6 operator brands | The DE report read 13 addresses across 5 brands in Oct 2026 | A sixth brand now appears: Field Supply Cannabis & Provisions, 4555 Kirkwood Hwy, Wilmington |

Data defects found in the official sources and recorded per row rather than silently repaired:
- **NY**: OCM attaches one `Location ID` to two different addresses on 4 applicant rows (Brooklyn/Woodside and Brooklyn/Bronx). Flagged in `extra_details`; ids carry a local suffix so the rows stay distinct.
- **PA**: PASDA carries both typos the audit flagged. `Bulter` is corrected to Butler in `town` (the facility's own name says Butler County) with `Bulter` kept in `town_as_listed`. The `RISE - King of Prussia` ZIP 19706 is left as published and flagged — its two sibling King of Prussia rows carry 19406.
- **MD**: the locator table's header columns are mislabelled relative to its cells — the header reads Dispensary, County, Address while the cells are Dispensary, Address, County. The build keys on cell position. A header-order parse would file every address as a county.
- **MD**: one address cannot be split into street and town (`782 State Route 3 N Gambrills Maryland 21054` — no comma and no street suffix); its town is left empty and flagged.

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
