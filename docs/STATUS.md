# Status (19 November 2026)

## Done
- Research and audits for all 50 states + DC, federal, the national business directory and all 10 regional business directories (California separate).
- Every report checked for completeness in Claude chat. Re-checked in Claude Code on 12 Nov 2026: all 64 files in docs/FILE_INDEX.md are present, none missing, none truncated, nothing on disk outside the index.
- Git repository started (local only, no remote). data/private/ is git-ignored and nothing under it is tracked. CLAUDE.md now names the private columns that live inside tracked data/clean/ files, so the public build has something authoritative to strip against.
- Master list of official sites, allowed to Claude Code in .claude/settings.json as WebFetch(domain:...) rules — **1,257 hosts**. Five were added during the build: paauditor.b-cdn.net, content.govdelivery.com, www.arcgis.com, maryland.maps.arcgis.com, and data.mmcp.ms.gov (Mississippi's cannabis transparency portal, 14 Nov 2026). einpresswire.com was deliberately left out as a secondary news reprint.
- New England licence table rebuilt from data/raw/ on 12 Nov 2026 (scripts/build_new_england.py): 3,917 to 4,267 rows, then **4,236 on 19 Nov 2026 after 31 regulator test records were removed** (see "Test records" below). CT 253 to 498 (470 without its test records), MA 967 to 1,072; ME, VT, RI and NH carried forward unchanged because their raw files hold nothing the table did not already have. A `standard_status` column was added so one search spans all six states.
- Mid-Atlantic raw licence data captured for all six jurisdictions (scripts/fetch_raw.py, declared in scripts/sources.json, logged in data/raw/manifest.csv). 23 of 24 declared sources fetched.
- Mid-Atlantic clean table built: data/clean/mid_atlantic_licences.csv, 4,236 rows (scripts/build_mid_atlantic.py). NY 3,056, NJ 678, PA 197, MD 191, DC 100, DE 14. Same columns as the New England table, in the same order, so the two union cleanly. NJ was rebuilt from its permit PDFs on 12 Nov 2026 (586 → 678) and PA's dispensary source moved to the DOH PDF (181 → 197).
- Regions 3-9: data/clean/regions_3_to_9_licences.csv, 44,203 rows (scripts/build_states.py), one declarative spec per state plus a USDA federal-hemp spec. CA 20,984, TX 12,853, OR 3,701, CO 1,832, WA 1,226, FL 289, IL 289, MO 238, OH 232, NV 345, HI 94, AL 85, VA 26, and 2,009 USDA hemp producers across 25 further jurisdictions. Same column set as the other two tables; all three union to 52,706 rows (**52,675** since the test records came out on 19 Nov 2026) across **50 of the 51 jurisdictions**.
- Business directory built: all 11 audited directories parsed into data/clean/businesses_master.csv, 355 to 2,087 entries, every row on HANDOFF's 17 standard categories (scripts/build_businesses.py). California 371, National 237, Great Lakes 196, Plains 192, Pacific 192, Southeast 189, Mid-Atlantic 173, Southwest 165, South Central 130, Mountain 124, New England 118.
- Business-to-licence matching done (scripts/match_businesses_to_licences.py): 22 directory entries hold a state licence under the same name, flagged on the row with their licence numbers and written to data/clean/business_licence_matches.csv.
- USDA hemp list (May 2026) parsed.
- **New Jersey's licence numbers captured (12 Nov 2026).** The CRC publishes no licence number in any list, but each row of its permitted-businesses page links a per-business permit PDF, and that PDF is the issued licence. All 517 were fetched (scripts/fetch_nj_permits.py, declared as `nj-crc-permit-pdfs` in scripts/sources.json, one manifest row per file, 22.4 MB, 0 failures) and parsed into data/clean/nj_crc_permits.csv (scripts/parse_nj_permits.py): 660 pages giving **655 licences and 5 consumption-area endorsements**, with zero parse flags. Every URL was read out of the saved page, never constructed. **The master table is rebuilt from them**: NJ is now 678 rows, one per licence, carrying real numbers, street addresses, counties and full expiry dates where it had none. 17 permits print a county the Census geocoder corrected; 1 is disputed and keeps the regulator's value.
- **`standard_type` added to all three licence tables (12 Nov 2026).** CLAUDE.md says to show the state's own licence name on state pages and use the standard type for search, and HANDOFF names 16 standard types, but no column carried one — `category` was doing the job with 38 inconsistent values (Hemp Retail 12,396 beside Hemp Retailer 178; "Retail Store" where HANDOFF says Retail; compounds like "Cultivation; Manufacturing; Retail Store"). Two columns now sit after `licence_type`, where HANDOFF's column list puts them and mirroring how `standard_status` sits after `status`: `standard_type` (exactly one of the 16, the lead activity) and `standard_types_all` (every type the licence authorises, in canonical order). 41 → 43 columns in each table, all three still identical and in order. `category` and `licence_type` were not touched. All rows carry a type and all 16 types are in use. 24 rows authorise more than one activity — 10 New Jersey compound CRC organisation types, 9 RI compassion centres, 3 RI Industrial Hemp Dual, 2 VT Integrated. (It was 147 when this column was added, 133 of them New Jersey; rebuilding NJ from its permit PDFs replaced those organisation-level compounds with one row per licence, each authorising one activity, and left only the 10 CRC-listed locations that have no permit of their own.) Every non-obvious call is recorded in HANDOFF.md with its reasoning, following the precedent set for `standard_status`: nothing was improvised and nothing genuinely different was folded together. CT's micro-cultivator stayed **Cultivation** rather than Microbusiness (§21a-420: ≥15,000 sq ft for a cultivator, 2,000–10,000 for a micro-cultivator — the same activity at a smaller cap, where a microbusiness covers several activities), and hemp distributors stayed **Transport & Distribution** rather than Hemp Retail (they sell to retailers, not to the public).
  - The lead of a compound comes from a fixed downstream-first precedence, not from the order the source wrote: NJ publishes the same combination as "Cultivation; Manufacturing; Retail Store", "Retail Store; Cultivation" and "Dispensing, Cultivating", so source order would have scattered one real combination across three leads. All three now read `Cultivation; Manufacturing; Retail` or `Cultivation; Retail`.
  - The mapping lives in `scripts/standard_types.py` and is imported by both the applier and verify.py, so the check and the write cannot drift. It **refuses to write** if any row carries a category it does not know, rather than defaulting — a blank in a search column would read as "no such licence" instead of "not classified yet".
  - These are derived columns and the three builders do not write them, so `python3 scripts/add_standard_type.py --apply` has to be re-run after any rebuild. verify.py fails loudly if the column is missing or stale, which is the guard; the failure names the command to run. The new checks were tested by corrupting rows and by dropping the columns, and they do fail.
  - **Surfaced in passing, not fixed:** the 2 Vermont `Integrated` rows are a licence class Act 176 repealed on 1 July 2026 (§ 909 repealed; §901(d) now lists six types). The VT report already flags one legacy integrated licensee in a Sept 2026 secondary count as transitional-VERIFY. Their status is worth a check against the CCB daily portal.
  - data/clean/nj_crc_permits.csv keeps its own schema and is not one of the three 43-column tables, so it carries no standard_type itself. The NJ rows built FROM it do: `python3 scripts/add_standard_type.py --apply` is the last step of the New Jersey pipeline.

## Next
1. Post-election re-check: **Idaho HJR 4 — checked 13 Nov 2026, NOT yet certified, re-check on or after 24 Nov 2026.** Idaho HJR 4 was the only 2026 cannabis-related measure on any state ballot (the 2026 Idaho Medical Cannabis Act failed to qualify on 14 July 2026; HANDOFF records that Florida and Arkansas had none). As of 13 Nov the Secretary of State's press site carries no state canvass or certification — its most recent items are county-level and the counts are still moving: "Latah County Recount Complete" (11 Nov 2026) and "Bannock County Reports Additional Election Day Ballots" with a vote-margin correction (10 Nov 2026). Idaho Code §34-1211 requires the State Board of Canvassers to meet "within twenty-one (21) days after the general election", so certification is due by **24 Nov 2026** (https://legislature.idaho.gov/statutesrules/idstat/Title34/T34CH12/SECT34-1211/).
   - **The Idaho report is now past its own expiry and one of its statements is stale.** reports/regions/8-mountain/idaho/idaho-audited.html says on its face: "Do not carry this file forward after 3 November 2026 without replacing the HJR 4 passages with certified Secretary of State / VoteIdaho results." Its Part 0 / 1.9 wording — HJR 4 "on 3 Nov 2026 ballot, not yet voted on" — is no longer true: the vote has happened and only the result is pending. Part 1.2's discipline still holds exactly as written ("No constitutional amendment limiting legalisation currently in force; only PROPOSED HJR 4"), because an uncertified measure is not in force. The report is deliberately NOT edited yet: the plan is to replace those passages once there is a certified result to put in them, and a two-step edit would put an uncertified outcome into an audited file. Until then HJR 4 must be described as voted on 3 Nov 2026 with the result uncertified, never as pending a vote and never with an outcome.
   - **The home-page map carries Idaho too** (scripts/legal_status_data.py, row ID). Its note says HJR 4 was voted and is uncertified. Update it in the same change as the report, then re-run build_legal_status.py and build_site_data.py.
   - Do not take a result from the unofficial county totals. A recount has already changed one county's count, and the project's rule against reconciling two differently-dated figures applies to election returns as much as to licence counts.
2. The remaining **1,006** county gaps (CA 275, CO 240, NY 196, HI 64, FL 59, TX 51, IL 36, ME 23, PA 22, MO 11, AL 9, CT 5, VA 5, MD 3, MA 2, RI 2, NJ 2, DE 1). Every one carries a `county unavailable=` note saying why, so none is a silent blank. Most need an address the regulator does not publish. Down from 1,133: New Jersey's permits closed 86, Connecticut's villages 8, and fixing the wrong-state geocode query closed 34 in Texas.
3. Resolve the licence numbers **PA and DE** do not publish — they publish none anywhere found so far. **NJ and MD are DONE**: NJ's 655 licences carry the CRC's real numbers, and MD's 191 carry the MCA's (see "New Jersey: rebuilt from the permit PDFs" and "Maryland publishes licence numbers after all" below).
4. DONE (14 Nov 2026) — see "The USDA hemp list: 25 jurisdictions to 50" below. 2,009 federal hemp licences built in, taking coverage from 25 of 51 jurisdictions to 50.
5. Finish Regions 3-9: 13 of 39 jurisdictions are built, 26 remain. Those 26 were swept directly and publish no licensee list at all — see the systematic negative result below. Finishing them needs a data request to each regulator or a per-licensee portal crawl, not more parsing. scripts/sources.json plus a spec in scripts/build_states.py is the pattern for any that do turn out to publish one.
6. DONE (13 Nov 2026) — see "Connecticut's villages" below. 13 rows went to 5, and the 5 left are premises in other states that the Census geocoder cannot match at all.
7. DONE (13 Nov 2026) — see "The business directory: profiles, California's contact detail" below. What is left for a person, not a script: 4 licence matches whose geography cannot be checked, 11 that match only a licensee's trading name, and the 242 California entries the audit still marks unverified.
8. Build the site — IN PROGRESS. Done: the public data build, the Database page, **50 state pages, the federal page**, the terms page (see "The site" below) **the home page's legal-status map** (see "The legal-status map" below), and **licence profile pages, county pages and the state Overview's county map** (see "Profiles and county pages" below). Still to build: city/town pages, and the Laws / Taxes / Market tabs on each state page — those three rest on the law rather than licence data, and each says so on its face rather than showing an empty frame.

## What the build corrected in the research
These are findings from the official sources themselves, not re-readings of the reports. Each needs folding back into the relevant state report.
- **CT**: ngch-56tr had been downloaded filtered to cannabis credential types only, so 280 hemp and THC-beverage credentials were missing — including the 104 live rows the master table was carrying with the wrong source label. Filter on `credential`, never `credentialtype`: types CSM and CSW are shared with "MANUFACTURER / WHOLESALER OF DRUGS, COSMETICS & MEDICAL DEVICES" and pull in roughly 4,300 unrelated pharmacy licences.
- **MD**: Part 5 recorded the MCA data dashboard as 404 and concluded MCA publishes no downloadable registry. The dashboard is live and carries an "Accessible Data Extract" XLSX dated Sept 2026, and the Dispensary Locator holds a 130-row table with a county for each dispensary. Maryland is not a no-download state. Resolved paths: /Pages/Data-Dashboard.aspx, /Pages/Dispensary-Locator.aspx, /Pages/Industry_Licensees_and_Registrants.aspx. **Taken further on 14 Nov 2026**: that XLSX is now parsed and is what Maryland is built from — see below.
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

### The remaining 26 states: a systematic negative result

Every remaining state was swept directly: for each one, its report-cited regulator pages whose path names a cannabis, marijuana or hemp programme were fetched and scanned both for list-shaped data files and for ArcGIS, Tableau and PowerBI embeds — the three routes that worked for Ohio, Missouri and Illinois.

**Across all 26, the sweep found zero licensee list files and no cannabis map embed.** 128 of 150 pages fetched successfully, so this is not a fetch failure. The one cannabis map embed that did turn up, in Michigan, belongs to the **City of Grand Rapids** (owner `mrojas@grand_rapids.mi.us`), not the state CRA. New Mexico's embeds are water-resource maps from the Office of the State Engineer, and its 52 spreadsheets are all monthly **excise-tax** files, not licensee lists.

What that means concretely: these states publish licensee data only through per-record lookup portals — eLicense, Accela, "Verify a License" — which answer one query at a time and cannot be enumerated. Getting them needs either a data request to each regulator or a per-licensee crawl driven by a known list of licence numbers, which is a different and much slower job from reading a published list. That is the honest state of it, not a tooling gap.

Grand Rapids' layer is kept in data/raw/michigan-local-grand-rapids/ anyway: 110 records with licence number, type, status, expiry, address and coordinates, plus the same app's sensitive-use buffers, allowed zone districts and 1000ft/2000ft licence buffers. That is exactly the local-rules material HANDOFF's city pages need. It is NOT in the state licence table — it covers one city, and whether its `LIC-C-…` numbers are state licence numbers or city permit numbers is unverified. Most are small or medical-only programmes; several (ID, KS, NE, WY) license no cannabis at all beyond hemp, so their licence universe is hemp registrations.

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
- **Schema gaps surfaced by real data — now settled.** The standard licence types went from 14 to **16** (Event Organizer, Operator) and the standard statuses from 7 to **10** (Limited Operations, Inactive, Canceled), decided on 12 Nov 2026 and recorded in HANDOFF.md with the reasoning. Every regulator word that still has no standard of its own now has a fixed, documented mapping there rather than an improvised one. That took the rows carrying an approximated status from **3,358 down to 1** — Oregon's single "NOT APPROVED", which is a refused application rather than a licence and stays visible and flagged.
- 205 rows have a deliberately EMPTY standard_status: Maryland's 191 licences and Delaware's 14, because neither regulator publishes a status at all. Empty must never be read as Active. (Maryland's extract does carry licence start and expiry dates, which is not the same thing as a status.)

## New Jersey: rebuilt from the permit PDFs (12 Nov 2026)

The CRC's permitted-businesses page gives organisation, business types, locations and an
expiration YEAR. Each of its 517 rows also links a permit PDF, and that is where the licence
numbers live. 41 links sit in the Medicinal table and 476 in the Personal-Use table; one permit
per PDF page, so a multi-class operator's packet holds several (Verano: RE000001, RE000030,
RE000002, C000009, M000007).

What a permit carries that the HTML list does not: the licence number, the Commission's own class
wording, the full street address, the county in print, and a full expiration date. 655/655 rows
have a street address, a county and an ISO expiry — the current NJ rows in the master table have
none of the first, 498/586 of the second, and a bare year for the third.

| CRC's own class wording | Licences |
|---|---|
| CLASS 5 - RETAILER | 381 |
| CLASS 2 - MANUFACTURER | 86 |
| CLASS 1 - CULTIVATOR | 76 |
| MEDICAL RETAILER | 57 |
| MEDICAL CULTIVATOR | 24 |
| MEDICAL MANUFACTURER | 13 |
| CLASS 3 - WHOLESALER | 7 |
| CLASS 6 - DELIVERY | 7 |
| CLASS 4 - DISTRIBUTOR | 4 |

Programme comes from the statute each permit cites, not from the licence class: 560 cite the
CREAMM Act (P.L.2021, C.16) and are Adult Use, 95 cite the Jake Honig Act (P.L.2019, C.153) and
are Medical. All 21 New Jersey counties appear.

**Consumption-area endorsements are not licences.** Five pages are endorsements rather than
permits, numbered from the retailer's own licence number plus -CA000n: RE000163-CA0001
(Gynsyng, Merchantville), RE000164-CA0002 (High Rollers, Atlantic City), RE000290-CA0003
(SunnyTien, Atlantic City), RE000692-CA0004 (URB'N, Newark), RE000052-CA0005 (Xena NJ, Jersey
City). Each carries its own consumption-area address and expiry. They are kept as their own
`record_kind` and named on the licence they attach to; counting them as licences would inflate
the licence count, and they are the first real data behind HANDOFF's Consumption Lounge type.

**A licence number belongs to the premises, as in Washington.** Two numbers each appear on two
permits at the same address, under different holders — and must not be merged:
- RE000774, 102A E Front St, Plainfield (Union): CANNAVERDE DISPENSARY LLC expiring 2027-12-04
  and FOUR20 DISPENSARY LLC expiring 2026-03-04 — different holder *and* different expiry.
- RE001037, 4306 US 130, Willingboro (Burlington): AUTHORIZED DEALER DISPENSARY IV LLC and THE
  VAULT DISPENSARY, same expiry 2027-01-26 — reads as a trading-name change.
So 655 licences carry 653 distinct numbers, and any licence_id built on the number needs a local
suffix the way NY's duplicate Location IDs do.

**A past expiry does not mean a dead licence.** 72 of the 655 permits print an expiry already
past (earliest 2025-07-10), yet the CRC publishes all 517 businesses under its own heading
"Active Cannabis Business Permits & Licenses". The regulator's framing is the source for Active;
the expiry is recorded and flagged. Neither may be read as the other.

**17 permits print the wrong county, and the permits' own ZIPs are what proved it.** The CRC's
County/Municipality table flagged 11 disagreements but could not settle them: it lists only the
230 municipalities that have acted on cannabis, and some disagreements are the same-name
collision HANDOFF warns about rather than an error (Franklin Borough in Sussex against Franklin
Township in Warren; Ocean Township in Monmouth against Ocean Township in Ocean).

So every permit address went through the US Census geocoder at address level
(scripts/verify_nj_permit_counties.py, sharing fill_counties.py's cache): **556 agree, 18 differ,
86 no match.** A difference alone decides nothing, so the adjudication rests on the permit's own
printed ZIP: where it equals the ZIP of the address the geocoder matched, both describe the same
building and only the permit's county field is wrong. That held on **17 of the 18** — Hammonton
printed as Camden (4 rows, Brute's Roots; it is Atlantic), Lakewood as Monmouth (Ocean),
Clementon as Gloucester (2 rows, Honeygrove South; Camden), Sicklerville as Gloucester (2 rows,
MPX; Camden), Blackwood as Camden (Gloucester), Branchburg as Somerset (Hunterdon), Roselle as
Middlesex (Union), Somerset as Middlesex (Somerset), Passaic as Morris (Passaic), Cape May as
Atlantic (Cape May), Oak Ridge as Passaic (Morris), North Bergen as Bergen (Hudson). Those rows
publish the Census county, with the permit's printed value kept on the row.

**One is left unresolved and keeps the regulator's value**: RE000766, Evolve Cannabis, 186 Route
130, Bordentown. The permit prints Burlington with ZIP 08505; the geocoder returned Mercer but
matched ZIP 08620, a different address, so it settles nothing. Burlington stands until a person
checks it. The 86 with no match keep the permit's county and say on the row that it is unverified.

NJ's county gaps went from 88 to **2** — INSA Coastline at Cape May Court House and Sea & Leaf at
Cape May, both CRC-listed locations with no permit.

**The table is now built from the permits, one row per licence.** The old 586 rows could not be
matched to them one-to-one — they were organisation-by-location rows expanded from
organisation-level business types, so 135 of the 655 permits landed on a town that several of
them shared. NJ is now **678 rows: 655 permits + 23 locations the CRC lists for an organisation
but publishes no permit for.** Those 23 keep the organisation's business types with the row
saying the types are NOT confirmed for that location, exactly as every NJ row did before, and
carry an EMPTY standard_status, which must never be read as Active.

| | before | after |
|---|---|---|
| NJ rows | 586 | 678 |
| real licence numbers | 0 | 655 |
| street addresses | 0 | 655 |
| counties | 498 | 676 |
| full expiry dates | 0 (year only) | 655 |

Towns need care, because the CRC abbreviates them on the permit ("EGG HBR TWP") and spells them
out in the HTML ("Egg Harbor Township"). The rules live in **scripts/nj_towns.py**, shared by the
builder, the county check and the reconciliation report so no two of them can disagree: an
abbreviation is accepted only against the full names the CRC itself lists for that same
organisation, only when it is a letter-by-letter subsequence, and only when exactly one
candidate fits. No expansion table was invented. 26 rows say on the row that their spelling
could not be matched.

**Talaria is settled**: W000018, CLASS 3 - WHOLESALER, Talaria NJ LLC, 950 Mount Holly Rd,
Edgewater Park (Burlington), expires 2026-11-25. It was the one loose end waiting on a number.

The permits carry no personal data: a scan of the set found no email address and no phone number,
and the only individuals named are the Commission's own signing officers. No private-column
implications.

## Connecticut: the traditional eight counties (decided 12 Nov 2026)

Connecticut uses its traditional eight counties — Fairfield, Hartford, Litchfield, Middlesex, New Haven, New London, Tolland, Windham — not the nine Planning Regions that replaced them as Census county-equivalents in 2022.

Current Census sources cannot supply them: TIGER lists only the Planning Regions, and the geocoder returns "Capitol Planning Region" where another state returns "Hartford County". The mapping therefore comes from the **Census ACS2021 vintage**, the last published before the change — still an official source, just an older one. All 173 CT towns are cached in data/raw/census_ct_town_county_2021.csv.

That took CT from 391 rows with a county to **443**, leaving 13. scripts/verify.py now **fails** if a Planning Region ever appears in a CT row, and checks CT against the traditional eight rather than the current Census list.

**Closed on 13 Nov 2026**, and not by the town mapping this once called for — see "Connecticut's
villages" below. The Census geocoder's County Subdivisions layer resolves a village to its
municipality at address level, which beat the village-level assumption: 56 River Rd, Cornwall
Bridge is in Sharon, not Cornwall, and 37 Willow Street settles which of Stonington and Groton
Mystic's address sits in. 13 rows went to 5; the 5 left are premises in other states.

## Profiles and county pages (19 Nov 2026)

HANDOFF's site layout now has its profile and county levels.

- **Licence profiles**, `licence.html?state=XX&id=<licence id>`. Each shows the full public record,
  its status and type badges, the row's own flags, its source and read date, and a small county
  map. Below that are the licences it is linked to: **same group** (the regulator's or the build's
  grouping), **same holder** (the same company name in the state, normalised for punctuation and
  LLC/Inc), and **same address** (the same premises). Holders who are individuals are never
  matched by name, because two hemp growers called John Smith are not one person. Placeholder
  addresses ("Data Not Available", 18,978 California rows) are never treated as shared. Each list
  shows 12 with the true total; past 12, the holder list links to the Database filtered by name.
  A licence id that does not exist gets a plain "no such licence" page, not an error.
  The Database's side panel now carries an "Open the full profile" link, and both use one
  renderer in `site/assets/app.js`.
- **The detail records are bucketed.** Each state's full records were one file (California's was
  21 MB, loaded on the first click of any California row). They are now split into ~300-record
  buckets by an FNV-1a hash of the licence id: `site/data/licences/detail/<ST>/<n>.json`. Python
  (`build_site_data.py`) and JavaScript (`app.js`) compute the same hash. Every id is ASCII,
  where the two agree. Opening a California profile now loads ~300 KB. The related lists
  raise the total from 53 MB to 79 MB, but no page loads more than one bucket.
- **County pages**, `county.html?state=XX&county=<value>`. Each has the county highlighted on its state
  map, record counts, the counts by standard type and by status, the towns, the first 300 licences
  linked to their profiles, and a link to the Database. "Local rules" says plainly that it is not
  published yet. A county with no records says that a missing record is not proof of no business,
  and how many of the state's records carry no county.
- **Display names come from Census**, so a reader sees "Baltimore City", "Winchester City" (an
  independent city with no county of that name), "Denver County" and "Acadia Parish", never
  "Winchester County". `us_map.county_display_names()` builds them; CT keeps its traditional
  eight counties.
- **The state Overview opens with a clickable county map**, as HANDOFF specifies. It is uncoloured
  on purpose: HANDOFF lists county colour-coding as "later, not now". The counts are in each
  county's tooltip and in the county table, whose links now open the county page.
- **County shapes**: US Census 2017 cartographic county boundaries via us-atlas 3.0.1, stored in
  data/raw/us-atlas/ and logged in the manifest. The 2017 vintage still has Connecticut's
  traditional eight counties, the vocabulary this project uses. The six city/county name pairs
  are told apart by Census county code (500 and up is the city). 58 licence rows in 43
  county values have no shape in their own state. Every one is already flagged as premises
  outside the licensing state, and they are listed but not drawn.
- **Checked in headless Chromium**: profiles in MA and CO, a missing id, county pages for Baltimore
  City, Los Angeles and an empty county (Hinsdale), the Colorado Overview, and a click through from
  the Database panel to a California profile. No console errors, and no horizontal scroll at
  390 px. Fixed along the way: the Database panel printed a stray "null" under every record, the
  address repeated the town, and the state page's six tabs widened the page on a phone.
- **A commit-hygiene note.** Part of this work (the buckets and the shared renderer) went in
  with e5289a2, the independent-cities commit, because `git add -A` picked it up. The site
  worked at that commit, so it was left there rather than rewritten.

## Independent cities were merged into their counties (19 Nov 2026)

Census gives an independent city and the county of the same name one basename: Baltimore city and
Baltimore County, St. Louis city and St. Louis County, plus four Virginia pairs (Fairfax,
Franklin, Richmond, Roanoke). The county column holds basenames, and `fill_counties.py` stripped
the "City" designator when it normalised spellings, so **"Baltimore City" and "Baltimore County"
both became "Baltimore"**. Any per-county count or county page would have added two separate
jurisdictions together. 82 rows were affected.

- **Rule now.** A city is written as Census writes its county-equivalent name, "Baltimore city".
  The county keeps its bare basename, like every other county, and carries a
  `city or county checked=` note saying which source settled it. `fill_counties.py` keeps the
  designator from now on, and verify.py fails on a bare ambiguous name without that note.
- **Settled from the regulators' own county fields** (`scripts/resolve_independent_cities.py`),
  never from the town: a Baltimore mailing address is often in Baltimore County. Missouri: DCR
  GIS County field, 39 St. Louis County and 10 St. Louis city. Maryland: MCA Dispensary Locator
  county column, 22 Baltimore County and 10 Baltimore city. Both splits match the 10 + 10 rows
  the earlier normalisation had marked "spelling normalised".
- **One cleared rather than guessed.** VA-HEMP-PROC-001 (2004 Dabney Rd, Richmond 23230). VDACS
  lists its locality as "Richmond", which is both the city and Richmond County. The address rules
  out the county, which is on the Northern Neck, but ZIP 23230 also covers Henrico County. Its
  county is now blank, with the reason on the row. A geocoder run (not reachable from this
  sandbox) settles it. Virginia's county gaps go from 4 to 5.

## Test records removed: 28 Connecticut, 3 Vermont (19 Nov 2026)

Found while grouping licences by shared address for the profile pages. **28 Connecticut rows were
the DCP's own test credentials**: legal name and DBA "TEST RECORD", registered to the DCP's office
at 450 Columbus Blvd, Hartford. They were on the public site, which showed 28 of them. They
covered every credential type, and some carried real-looking numbers (ACRE.0015712, CSW.0005793-TIB),
so a number-based rule would have missed them. **3 Vermont rows**, all `Active`, were CCB test entries:
"Test - MANU0123", "Test - RTLR0086" and "High Society - Test - Manufacturing" (MANU0073).

- `scripts/build_new_england.py` now excludes them. Connecticut's are matched by the name "TEST
  RECORD", so a daily refresh that brings in new ones drops them too. Vermont's are named by
  licence id, because their only marker is the name. The run prints how many it dropped per state.
- **The table was NOT rebuilt to apply this.** A rebuild also clears the county notes that
  `scripts/fill_counties.py` writes (58 rows), and that step needs the Census geocoder, which this
  sandbox cannot reach. Instead the 31 rows were deleted from the existing table, and the diff is
  exactly 31 deletions. The next full rebuild produces the same result.
- **A second bug in the same builder, fixed.** Massachusetts rows were stamped
  `data_as_of = today` on every run, and Connecticut rows with no refresh date fell back to today
  too. So a rebuild on any later day would have claimed every MA licence was read that day.
  Both now use the date the raw file was read: 12 Nov 2026 (`MA_READ_ON`, `CT_READ_ON`).
- Checked and left alone: California's "La Test Labs LLC" (trading as Pacific Star Labs) and
  "we'd Test" match the word "test" but read as real business names. The superseded inputs
  data/clean/ct_licences.csv and vt_licences.csv still hold the test rows. They are not
  built into the site.
- Totals: New England 4,267 → 4,236; all three tables 52,706 → 52,675. verify.py passes.

## The legal-status map (19 Nov 2026)

The home page now opens with a clickable map of all 51 jurisdictions coloured by the legal
status of cannabis **under state law**. The colour comes from `data/clean/legal_status.csv`,
never from whether this project holds licence data for a state.

- **Where the status comes from.** `scripts/legal_status_data.py` restates section 1.1 ("Legal
  status") of each audited report, by hand, with the citation the report gives and a link the
  report itself cites in that section. Every citation was checked against the report's own text
  before it went in. One that came from memory rather than the report was corrected: South Dakota's
  measure is "IM 26", as the report writes it.
  `scripts/build_legal_status.py` writes the CSV and refuses on an unknown status, a link that
  is not on an official host in domains/all-domains.txt, a row with no link and no reason, or a
  report with no readable "Last audited" date. That date is read from the report, so it cannot
  drift from its source.
- **Four statuses, no more.** 25 adult use and medical (including DC and Virginia), 15 medical
  only, **3 limited (low-THC) medical only** (Georgia, Iowa, Texas), 8 no medical programme
  (Idaho, Indiana, Kansas, North Carolina, South Carolina, Tennessee, Wisconsin, Wyoming). The
  third class is not in HANDOFF's colour list, which names dark green, medium green and "lighter
  green adult-only if needed". No state is adult-use only, so that shade is used for low-THC
  instead. Folding Texas or Georgia into "medical only" would overstate the law, and folding them
  into "none" would erase a licensed programme. No medical programme is a neutral grey, not red:
  the map states the law, it does not grade it.
- **What the colour cannot say, the card says.** Hovering over a state, tabbing to it, or tapping it
  on a phone shows its citation, the official link, the date the law was checked, and a note
  where the colour alone would mislead. Virginia: adult possession is legal, but retail opens only on
  1 July 2027. Nebraska: patients are protected but no dispensary licence had been issued. Delaware,
  New Jersey, Washington: home grow limits. Hawaii, New Hampshire: decriminalised, not legal. Idaho:
  **"HJR 4 was voted on 3 Nov 2026 and the result is not yet certified"**, which is the
  wording item 1 above requires. The map note says the law was checked between 23 Oct and 1 Nov 2026 and that
  federal law differs, with a link to the federal page. A "map as a list" table under the map
  carries the same facts for screen readers and for anyone who wants all 51 at once.
- **Shapes.** US Census Bureau cartographic state boundaries (2017), already projected with
  Alaska and Hawaii inset, from the us-atlas 3.0.1 package. They are stored in data/raw/us-atlas/
  and logged in the manifest. They came from the npm registry because census.gov is not reachable
  from this sandbox. `scripts/us_map.py` turns them into SVG paths at build time (116 KB), so
  the site loads no mapping library and nothing from a CDN. The nine states too small to label
  (VT NH MA RI CT NJ DE MD DC) get a callout column to the right of the map, and each callout can also be clicked.
- **Checked in a real browser** (headless Chromium, desktop and iPhone 13): all 51 shapes
  render with no console errors and no horizontal scroll at 390 px. Hovering shows the card,
  clicking opens `state.html?state=XX`, and on touch the first tap shows the card and the
  second opens the page. `scripts/verify.py` now checks that the CSV is valid, current, and
  is what the site's map shows. Changing Texas's status by hand makes it fail on both counts.
- **verify.py now runs off a Mac.** Its PDF page counter called macOS `mdls` unconditionally and
  crashed on Linux. It now reports "?" pages when `mdls` is absent. Every other check is unchanged
  and all pass.

**Gaps this leaves, recorded rather than papered over:**
- **Tennessee and Wyoming carry no official link.** Their reports cite the statutes (Tenn. Code
  §39-17-402; W.S. 35-7-1001 et seq.) but link only Justia/FindLaw, which CLAUDE.md rules out. The
  card says "no official link captured yet". The fix is the official code page for each.
  Tennessee's official online code is published through LexisNexis.
- **Michigan's link is the medical act.** The report gives no official link for the adult-use act
  (MRTMA, MCL 333.27951 et seq.); the row's note says so.
- **Idaho must be re-checked on or after 24 Nov 2026** (item 1). If HJR 4 is certified, update
  the Idaho row in scripts/legal_status_data.py as well as the report. The map is the most visible
  place an outcome would show.
- The map colours by **state** law only. Tribal programmes (e.g. the Eastern Band of Cherokee in
  North Carolina) are noted on the card, not coloured.

## What needs a person, in one worksheet (14 Nov 2026)

`scripts/build_review_worksheet.py` gathers every decision a script cannot make into
`data/clean/review_worksheet.csv` — **805 rows**, each with the question, the page to open and
what the record says now. Filling in the `decision` column is what applies it.

**18 are priority 1**, the ones that change what the database says:
- **16 licence matches.** 11 match only a licensee's trading name (Treez, Nabis, High Times,
  Cookies, incredibles, STIIIZY, Old Pal, Papa & Barkley, Harvest Moon Hydroponics, Healer,
  CannaBiz Consulting Group) — HANDOFF's "operates under another company's licence", but which
  brand it is needs a person. 4 match by legal name with no geography to check against (Green Acres
  Organic Pharms, Simply Sol, New River Distilling, Treadwell Farms). 1 is A1 Organics, where the
  evidence says different business and a person need only confirm the drop.
- **2 Vermont licences in a class that no longer exists.** Vermont Patients Alliance (Middlesex)
  and FWR, Inc. (Brandon) are `Integrated`, which Act 176 repealed on 1 July 2026 (§909 repealed;
  §901(d) now lists six types). Their current class needs checking against the CCB portal.

The remaining 787 are the directory entries an audit could not confirm. They are already held back
from the public site, and a decision releases one.

Still blocked on a person with a browser, and nothing else:
- **Minnesota** — https://mn.gov/ocm/data-reports/application-data/ serves a Radware Bot Manager
  hCaptcha. Solving one is off limits, so this is the only route. Save into data/raw/minnesota/.
- **New York hemp producers** — both files return HTTP 403 to every scripted client:
  `agriculture.ny.gov/system/files/documents/2025/12/licensed_hemp_producers.pdf` and
  `agriculture.ny.gov/plant-industry/licensed-hemp-producers`. CONTAINS PERSONAL EMAILS — private
  columns only.
- **New Hampshire** — the DHHS PDF its 7 hand-transcribed ATC rows came from. Those are the only 7
  rows of 50,697 whose source document is not on disk to re-verify against.
- **26 regulators that publish no licensee list** — **the 26 letters are drafted**, in
  `outreach/data-requests/` (scripts/draft_data_requests.py). A person still has to send them: a
  records request needs a real requester and a reply address.
  - The ask is written to work whatever a state licenses — every licence, permit or registration
    under any cannabis, marijuana or hemp programme — rather than naming programmes that may not
    exist there. It requests the regulator's own licence number, its own type and status wording,
    legal name, DBA, premises address **including county**, and issue and expiry dates.
  - It asks for **nothing exempt**: no personal contact details, no owners, no application
    materials, no security plans, nothing about patients or employees. That is this project's own
    privacy rule, and it also makes the request cheap to fulfil and hard to refuse.
  - **No statute is cited and no address is invented.** Every state's public-records law has its
    own name and number; a request citing the wrong one invites a brush-off and misinforms the
    sender. Both are marked slots.
  - **16 of the 26 are now VERIFIED against the agency's own site (14 Nov 2026)** — the agency, what
    it licenses in its own words, and the route to send to: AZ, IA, KY, LA, MN, MT, ND, NE, NM, OK,
    SD, UT, GA, MS, AR, WI. Those letters carry a real records-request URL or form where the agency publishes one,
    and say plainly where it does not.
  - **Verifying corrected four letters that would otherwise have gone to the wrong place:**
    - **Kentucky** was addressed to Alcoholic Beverage Control, which states on its own site that
      it runs no cannabis programme. The licensing body is the Office of Medical Cannabis, in the
      Cabinet for Health and Family Services.
    - **Utah** was addressed to a "Cannabis Establishment Review Board". Business licensing is the
      Department of Agriculture and Food's; the health department runs the patient programme.
    - **Montana**'s division is the Cannabis & Alcohol Regulation Division (CARD), not the
      "Cannabis Control Division".
    - **Arizona**'s licensing body inside ADHS is the Bureau of Marijuana Licensing.
  - **Two findings worth more than the letters.** Minnesota publishes a **Data Requests** page
    (https://mn.gov/ocm/connect/data-requests/index.jsp) and a **Public Licensing Data** page — so
    the CAPTCHA that blocked this project was in front of one page, not the data itself; check the
    licensing-data page before sending anything. And South Dakota issues **certificates**, not
    licences, which is the word to use when asking it.
  - **Georgia and Mississippi are verified too, and getting there corrected a mistake of mine.** I
    reported both as blocked on hosts missing from the allowlist, naming gmcc.georgia.gov,
    msdh.ms.gov and medicalcannabis.ms.gov. **Those were hostnames I had invented**; gmcc.georgia.gov
    does not resolve at all. The real hosts — **www.gmcc.ga.gov** (resolved from the link on
    dph.georgia.gov's own medical-cannabis page) and **www.mmcp.ms.gov** (cited in Mississippi's own
    audited report) — **were already in the allowlist the whole time.** Nothing needed adding for
    them; I had checked names I made up and reported their absence as a blocker. Exactly one genuine
    addition came out of it: **data.mmcp.ms.gov**, taken verbatim from the MMCP site, bringing the
    allowlist to 1,257.
    - Georgia: the GA Access to Medical Cannabis Commission licenses Class 1 Production, Class 2
      Production and Dispensing. The Department of Public Health runs only the patient card, so it
      was never the right recipient.
    - Mississippi: MSDH runs the MMCP and licenses cultivation and processing, while **dispensary
      licensing sits with the Department of Revenue's ABC division** — two recipients, not one. Its
      Transparency Portal was checked through the Socrata catalog API: the datasets are aggregate
      counts and anonymised per-record rows (record type, status, county) with **no business name
      and no licence number**, so the roster really is unpublished. The letter says so, which shows
      the agency the ask is informed.
    - A trap worth recording: the unscoped Socrata catalog API federates across every Socrata
      domain, so a first call returned Dallas Police and NHTSA datasets. It has to be scoped with
      `?domains=<host>&search_context=<host>` or it tells you about somebody else's data.
  - **3 more were checked and the result recorded in the letter rather than left open:** Michigan
    and Alaska return HTTP 403 to automated clients (michigan.gov/cra,
    commerce.alaska.gov/web/amco), and West Virginia's health department names no cannabis office
    at all on its homepage.
  - **Arkansas and Wisconsin verified too (14 Nov 2026).** Arkansas: the Arkansas Department of
    Agriculture runs a Hemp Program that licenses growers and processors, with a FOIA page at
    https://agriculture.arkansas.gov/resources/public-information/foia-requests/ and (501) 225-1598
    — but its site does not name the agency that licenses medical marijuana, so Arkansas needs a
    second recipient found. Wisconsin: DATCP discontinued its hemp programme on 1 January 2022 and
    its growers are USDA-licensed, so it may issue no cannabis or hemp licence at all; its letter
    now says a one-line reply confirming that is a complete answer.
  - **Every letter now states what is already held.** Where USDA licenses hemp producers in that
    state, the letter gives the count from the project's own USDA extract and narrows the ask to
    whatever the STATE itself issues, so no agency is asked to duplicate a federal list.
  - The remaining 7 keep a candidate agency extracted from that state's own audited report, marked
    unverified; 3 are deliberately blank (ID, KS, WY). Most are states that license no cannabis at
    all, where the recipient is probably an agriculture department's hemp programme — and where
    Next item 4 may mean no letter is needed.
  - **The known limit, stated on each letter it applies to:** a name lifted from report prose
    cannot distinguish a body that licenses today from one proposed in a bill, and these are
    precisely the jurisdictions with no licence data, several of which run no programme at all.
    Two extraction faults were caught and fixed before this shipped — Mississippi's letter was
    addressed to the *Alabama* Medical Cannabis Commission, which its report mentions
    comparatively, and four letters carried sentence fragments as the recipient ("Office of
    Medical Cannabis ceased accepting permit").

## State pages and the federal page (14 Nov 2026)

`site/state.html` serves all 50 jurisdictions from the per-state JSON rather than 50 generated
files, with HANDOFF's six tabs. Three are backed by data and three are not, and the three that are
not say so:

- **Overview** — record counts, how many carry the regulator's own number, counties with at least
  one, records with no county published, programmes as the regulator classifies them, a county
  table, and the sources the data came from.
- **Licences** — the state's own licence names first, which is what HANDOFF asks for ("Show the
  state's own licence name on state pages; use the standard type for search"). Colorado reads
  `Retail Marijuana Store` 636, `RMJ Delivery Permit` 10, `Hospitality & Sales Business` 4 beside
  the standard types. Clicking a standard type or a county opens the Database already filtered.
- **Business** — points at the services side of the Database.
- **Laws, Taxes, Market** — each explains what it will cover and why it is empty: it rests on the
  law rather than on licence data, the research exists in that state's audited report, and
  publishing an unsourced summary of the law would be worse than publishing nothing.

A state with no licence data at all (only Alaska now) says so and points at the drafted data
request rather than rendering an empty frame.

`site/federal.html` publishes the federal baseline as sourced, dated statements: the split
scheduling at 91 FR 22714 from 28 April 2026 with adult-use remaining Schedule I, 280E lifted for
medical only, the hemp definition changing on 11 December 2026 to total THC with a 0.4 mg per
container cap under PL 119-37 §781 as limited by PL 119-103 §2019, the 31 December 2026 USDA
DEA-lab testing deadline, the medical rider through 11 December 2026, and the absence of any
federal banking statute. It also carries the two things the audited federal report leaves open —
how a state follows or blocks a federal schedule change (Idaho §37-2702(d) follows, Tennessee
Pub. Ch. 789 blocks) and whether a tribal medical programme counts as "state-licensed".

**Verified in the browser this time, and it caught a bug the static checks could not.** `state.html`
called `render()` during module evaluation while the `const` arrow functions it uses were still in
their temporal dead zone — valid syntax, and the page rendered nothing but its tab strip. Those are
now hoisted function declarations. Checked afterwards: Colorado's full tab set, Alaska's no-data
message, Wisconsin's Laws tab, the federal page, and the drill-through from Colorado's county table
into the Database, which lands on 553 of 1,832 Denver licences — the same 553 the state page shows.

A reminder for the next session: Bash cannot reach localhost in this sandbox, so a `curl` smoke test
hangs rather than failing. The browser pane and `preview_logs` are the only usable evidence.

## The USDA hemp list: 25 jurisdictions to 50 (14 Nov 2026)

Found while verifying the data-request recipients, by following Wisconsin's own statement that its
growers are USDA-licensed. `data/clean/usda_hemp_licensees_national.csv` had held the USDA's 5 May
2026 FOIA extract — 3,635 federally licensed hemp producers — since the earlier chat, and it had
never been built into a licence table. So 25 jurisdictions read as having no licence data at all
while a real, dated, official licence universe for them sat in data/clean.

**2,009 rows are now built, and licence coverage goes from 25 of 51 jurisdictions to 50.** Only
Alaska has none in the extract. NC 666, WI 290, MN 194, TN 175, MS 119, IN 104, KS 83, GA 71,
KY 51, NE 41, OK 34, IA 23, LA 22, SD 20, AZ 19, WV 19, UT 17, AR 13, MI 12, ID 9, NM 8, SC 6,
MT 5, WY 5, ND 3.

**Scope is deliberately narrow, because the extract OVERLAPS state data.** 166 of its licence
numbers already existed as licence_ids here — 153 Florida and 13 Connecticut, the same businesses
at the same towns. Florida's overlap hides behind different name fields: FDACS publishes the
responsible person where USDA publishes the business, so a name check finds 6 where a number check
finds 153. Building the list wholesale would have double-counted. So only the 25 jurisdictions with
no data of their own are built from it, verified against every existing licence_id to collide with
nothing.

**That leaves 1,623 USDA producers in states that DO have their own data, deliberately not built,
and it is an open question.** Deciding whether each is a licence the state's own list missed or the
same business under a different number is per-state work: FL 339, TX 325, CO 112, MO 108, NY 107,
VA 107, CA 81, PA 73 and the rest.

What the rows carry: a real federal licence number, holder name, city, ZIP, the regulator's own
status, issue and expiry dates, source URL and extract date. Every row says on its face that it is
a **federal** USDA licence and not a state one — a state running its own USDA-approved plan
licenses its own growers, who do not appear in this extract, which is precisely why it is the right
universe for the states where USDA administers instead.

Three judgements:
- **"Active on Corrective Action Plan" (76 rows) maps to Active**, because it is still a live
  licence. The regulator's own wording stays in `status` and the plan is named in `extra_details`,
  so the distinction the standard statuses cannot carry is not lost.
- **Puerto Rico's 3 producers are reported and left out.** This project covers the 50 states and
  DC; dropping them silently would have been the wrong kind of quiet.
- **8 rows needed the existing `~n` id suffix** to stay distinct, 3 of them because the USDA
  extract itself repeats a licence number.

**No county, and the reason is specific.** USDA withholds the producer's street address — it is
present on 118 of 3,635 rows — and the Census geocoder returns no match without one, tested on
14 Nov 2026 with city+ZIP and with the ZIP as the street line: 0 matches both ways. So county gaps
rise from 1,005 to 3,037, every new one saying exactly that. **A ZIP-to-county crosswalk is the
official route**, and the next pass needs one host approved (www2.census.gov, where the Census
publishes its ZCTA relationship files, is not in the allowlist) plus a decision about a ZIP that
spans counties — it must not pick one silently.

**The pipeline order, which I had been running incomplete.** `fill_counties.py` has a third step,
`--validate`, that writes the `county not valid for this state=` flag verify.py exempts against.
Rebuilding this table wrote fresh rows without it, and two Ohio rows failed the county check —
rows where Ohio's own DCC GIS layer publishes "Painesville Township" and "Lewis Center" in its
county field. The flag is the record of a regulator's error, not a workaround, and it has to be
re-applied after any rebuild:

```
scripts/build_states.py
scripts/fill_counties.py --apply
scripts/fill_counties.py --canonicalise
scripts/fill_counties.py --validate        <- this one
scripts/add_standard_type.py --apply
scripts/build_site_data.py
scripts/verify.py
```

## Maryland publishes licence numbers after all (14 Nov 2026)

Part 5 recorded the MCA data dashboard as a 404 and concluded Maryland published no downloadable
registry. The 12 Nov build found the dashboard live and captured its "Accessible Data Extract"
XLSX — then could not read it, because openpyxl was not installed, so it sat in data/raw/ and the
table was built from the dispensary locator instead: 130 rows, no licence numbers, no dates, no
statuses. The tooling is there now, and the extract is the real registry.

| | before | after |
|---|---|---|
| MD rows | 130 (dispensaries only) | **191** (128 dispensary, 31 processor, 27 grower, 5 testing lab) |
| real licence numbers | 0 | **191** |
| issue dates | 0 | 190 |
| expiry dates | 0 | 190 |
| counties | 127 | 128 |
| websites | 0 | 123 |
| coordinates | 0 | 124 |

The MCA's own "License Data Summary Metrics" tab states the total as 214 — 27 grower, 31 processor,
128 dispensary, 5 testing lab, 23 ancillary — which the build reproduces exactly, so the parse is
checked against the regulator's own arithmetic.

Four judgements, each following a precedent already set here rather than a new rule:

- **23 ancillary business registrations are NOT in the licence table.** They are security guard
  agencies, waste haulers and the like, and HANDOFF puts a business that serves the industry in the
  directory. There is also no standard type among the 16 that fits a security guard agency, and
  inventing one in passing would be a schema change by the back door. They are counted and named
  in the build output. The five that are *also* an Independent Testing Lab do have a standard type
  and are included.
- **Maryland's "Micro" is a tier, not a Microbusiness.** 8 licences are Micro (3 dispensary, 3
  processor, 2 grower) and the rest Standard. A micro grower only grows, so this is the same call
  already made for Connecticut's micro-cultivator: the activity decides the standard type, and
  Standard/Micro goes in `tier`.
- **152 conditional social-equity awards are not licences.** The Social Equity tab holds 197
  records but only 45 licence numbers: the other 152 read "Pending" in both the number *and* the
  address field, and their Region/Jurisdiction is a broad region ("Southern"), not a county.
  CLAUDE.md forbids mixing approved with licensed, so they are counted in the build output and not
  built as rows. Their award categories (75 Standard Dispensary, 39 Standard Processor, 26 Micro
  Grower, 25 Micro Processor, 23 Standard Grower, 9 Micro Dispensary) and rounds (183 Social Equity
  2024, 9 HB2, 5 2023 Expansion) are the programme summary HANDOFF's Licences tab wants.
- **`standard_status` stays EMPTY for all 191.** The extract carries no status column. It carries
  licence start and expiry dates, which are not a status, and the MCA's own operational flag — but
  only for its 45 social-equity licences (37 Yes, 8 No). That flag is recorded per row and labelled
  a different measure from being licensed, never read as one.

What Maryland still does not publish: **a premises address for a grower, processor or testing lab.**
63 of the 191 rows have none, in either the extract or the locator, and each says so. The locator
is still the only address source for dispensaries, joined by trading name — 123 of 128 match, and
the 5 that do not say so on the row.

`scripts/xlsx_reader.py` now addresses sheets by NAME rather than index, because the MCA records in
its own notes tab that it "updated the look and feel of the licensee tabs" — a positional index
would one day read the wrong sheet and quietly build from it.

**Colorado's dated zero is no longer counted as a gap.** `co-med-rd-cultivators-tab2` was reported
"not captured: only 41 bytes". Those 41 bytes are `License Number,Date Updated` and `NA,11/2/2026`
— the MED publishing, with a date, that it has no retail-and-medical dual cultivators to list. The
byte-size rule was right to flag it; the conclusion drawn from it was wrong. Captured sources go
from 575 to 576, and the 2 that remain are the New York hemp-producer files, which return HTTP 403
to every scripted client and need a person with a browser.

## The site: the public build, and the Database page (13 Nov 2026)

**The public data build is the safety-critical part, and it uses an allowlist.** The clean tables
hold 35,520 premises phone numbers, 20,842 emails and 21,276 owner records, and CLAUDE.md requires
the public build to drop the private columns *explicitly*. scripts/build_site_data.py therefore
names the columns that may be published rather than the ones that may not: a denylist fails open —
add a private column next year and it ships — while an allowlist fails closed, so a new column is
absent from the site until someone decides it is public. 39 of the 43 licence columns and 25 of the
32 business columns are allowlisted, and the script refuses to write any object carrying a private
key at any depth.

Output is `site/data/`, git-ignored because it is generated from data/clean and 66 MB of it would
churn on every rebuild — which also means a public build can never be committed by accident.
Licences are written per state and split list/detail: California alone is 20,984 rows, and its
detail file is 20 MB, so a results table loads the 6 MB list and the full record only when a row
is opened.

CLAUDE.md's "unverified entries stay off the public site until checked" is enforced here too:
of 1,945 business profiles, **1,158 are published and 787 are held back**. The held-back entries
are written to their own file rather than dropped, so the count stays visible and nothing is lost.

**verify.py proves no private data reaches the build, two ways.** A column-name test catches a
whole field being copied across. A value test catches the same data arriving under a different
key, which is what would actually happen if someone mapped `owners` into a "principals" field.
Every private email and phone is tested — **27,455 values** — by pulling every contact-shaped
string out of the built JSON and intersecting, not by sampling. An earlier version sampled 400 per
column, capped out on New England, and so never tested one of the 20,842 regions_3_to_9 emails: it
would have missed a leak of any of them. Both tests were confirmed to fail on an injected leak,
including one hidden under an innocuous key name.

**One real cross-contamination surfaced, and it is not a leak.** 413-539-3059 is Blue Skies
Unlimited's own published business line in the New England directory, *and* the regulator's
contact_phone on two Massachusetts licences (Ezdelivery LLC, Clovercraft llc) — that consultant is
the listed contact for his clients' applications. The site publishes the first and never the
second. So the invariant is narrower than "no private value appears": no value that exists ONLY in
a private column may appear. 75 values are excluded on that basis, and the exclusion is printed
rather than silent.

**The Database page is built** (`site/database.html`): the Licensed Operators / Industry Services
toggle, search, type/status/county/category filters, sortable columns, a detail panel, CSV export
of exactly what is on screen, and filters in the URL so a state page can later open it already
narrowed. The default view is Active + Provisional, as HANDOFF specifies. The regulator's own
licence name and status sit beside the standard ones, and a licence with no published status shows
"not published" rather than anything that could read as Active.

**What is NOT built, and why.** HANDOFF's home page opens with a US map coloured by legal status.
That colour is a statement about the law, so it needs a sourced status for each of the 51
jurisdictions, quoted from that state's own statute and regulator — not inferred from whether this
project holds licence data. Texas licenses no adult-use or broad medical operator but does run a
limited medical programme, so colouring from licence coverage would misstate the law in several
states. The research is in the audited reports, which carry a "Legal status." paragraph each, but
it is prose; turning 51 of those into a status with a citation is the next job, and the home page
says so on its face rather than shipping a map that guesses.

**Verification.** The browser pane went unresponsive partway through, so the pages were not
confirmed by screenshot. They were confirmed another way: the inline module scripts parse, and the
real module was exercised in node against the real built data — CT's default view is 223 rows
against the build's published 223, every table column has data, sort and search work, and CSV
escaping was tested directly (a comma stays inside its quotes, an inner quote doubles). verify.py
now also holds the page/data contract: every column the page renders must exist in the built data,
the default view must match the published count, and every page must mount the footer. Note Bash
cannot reach localhost in this sandbox — a connection opens and the response never arrives — so
the server log and the browser are the only usable evidence there.

## The business directory: profiles, California's contact detail (13 Nov 2026)

Four jobs, all of them Next item 6.

**California's contact detail now exists.** All 371 California rows carried a verdict and nothing
else — no website, phone, email, address or description — because build_businesses.py parsed the
report's PART 1 audit table, and the contact detail is in PART 2, the "corrected rewrite".
scripts/fill_california_contacts.py reads it:

| field | before | after |
|---|---|---|
| website | 0 | 212 |
| phone | 0 | 217 |
| address | 0 | 215 |
| description | 0 | 238 |
| email | 0 | 102 |
| key_people_private | 0 | 158 |

Part 2 uses **four** layouts, none tabular — numbered headings with label/value lines; id headings
("9-11b-01 — Humboldt Hydroponics — Eureka") over `<ul><li><strong>Label:</strong>` bullets; one
paragraph per business with the labels inline; and "Row 1 — Spokes Digital — Unverified" headings,
sometimes with the report's own row id in the middle. So the parse keys on the labels, which are
consistent, not the markup, which is not. 302 entry starts yield 284 distinct businesses, 271 of
which match an audit-table row.

**No placeholder was published, and that mattered more than it looked.** "Not published — Verify"
appears 1,359 times in Part 2 and is treated as absent. The subtler trap was a value *led* by
"Verify": the report writes `Phone: Verify — conflict: directory (415) 651-4613 ...; opened page
footer 707-380-7058` and `Email: Verify — opened page footer lists jared@harris-sliwoski.com, a
non-schwasslaw.com domain`. A regex happily pulls a phone and an email out of both, and the first
pass did exactly that — publishing two values the auditor had explicitly declined to confirm. A
leading "Verify", "conflict" or "unverified" now means the field is absent.

**The California report is double-escaped** — 59 instances of `&amp;amp;` — so a single unescape
left 19 rows carrying entities, 7 of them in a published business name reading "Sheppard, Mullin,
Richter &amp; Hampton LLP". `txt()` now unescapes until stable, and build_businesses.py gained a
`--refresh REGION` flag so a region can be re-parsed rather than only appended to. verify.py fails
if a business name ever carries an entity again.

**One profile per business, nothing deleted.** 2,087 directory entries are 1,945 businesses: a
national firm legitimately appears in the national directory and again in each regional one.
HUB International is in 8 of them, Vicente LLP and Dark Horse CPAs in 7, GrowGeneration and ARCO
National Construction in 5 — Brink's, Colliers, Loomis and GardaWorld in 4 each, which is exactly
the pattern HANDOFF names. Five columns mirror the licence tables' group_id convention
(`profile_id`, `is_primary_profile`, `duplicate_of`, `entries_in_profile`, `regions_in_profile`),
so the public build filters to the primary and reads `regions_in_profile` for "serves" instead of
deleting a separately audited entry. The primary is the National row where one exists — that is
the parent profile HANDOFF asks for — otherwise the fullest row, and **238 blank cells on primaries
were filled from their own group**, because a regional audit often found a phone the national one
did not.

**10 profiles are categorised differently by different directories** — Green Rush Packaging is
Marketing in one and Packaging in another, Blue Line Protection Group is Cash Management and
Security, GrowGeneration is Grow Supplies and Marketing. The category is NOT reconciled: the row
says which directories disagree and what they each said, because picking a winner would bury a
real disagreement between two audits.

**The 22 licence matches are reviewed, on evidence rather than brand knowledge.** The matcher keys
on the licensee's legal name AND its DBA, which is what makes a verdict possible:

| verdict | n | what it means |
|---|---|---|
| same business — belongs in the licence database | 6 | legal name matched, geography agrees |
| name matches, geography unknown | 4 | the directory gives the business no state or address, so there is nothing to check against — silence is not confirmation |
| trades under another company's licence | 11 | only the DBA matched: HANDOFF's "operates under another company's licence", but which brand needs a person |
| likely a different business with the same name | 1 | A1 Organics, a composting firm in Eaton, Colorado, against a California cultivation licence in Trinity County |

GAIACA needed care: "Gaiaca, LLC" is a *shorter* form of "GAIACA Waste Revitalization", not a
different name, so a legal name counts as matching when one name's words are a subset of the
other's. Still nothing deleted and nothing moved — each verdict and its reason sit on the row and
in business_licence_matches.csv, so the public build can hold an entry back while a person settles
the 15 uncertain ones.

Pipeline order, because several of these steps write onto rows another step produced:

```
scripts/build_businesses.py [--refresh REGION]
scripts/fill_california_contacts.py
scripts/merge_business_profiles.py
scripts/match_businesses_to_licences.py
scripts/review_business_licence_matches.py
scripts/verify.py
```

## Connecticut's villages, and a geocoder asked the wrong question (13 Nov 2026)

Connecticut's last 13 county-less rows were two different problems wearing one label.

**Seven were villages and boroughs, not towns** — Terryville, Mystic, Cornwall Bridge, Kensington,
Baltic. The route that closed them uses the Census geocoder's **County Subdivisions** layer, which
the build had not been reading. CT's Counties layer is useless here (it returns "Naugatuck Valley
Planning Region", the post-2022 vocabulary this project does not use), but the very same response
names the county subdivision — "Plymouth town" — which IS a Connecticut town and maps straight to a
traditional county through the cached ACS2021 table. Two official sources, no invention.

Address-level resolution turned out to be better than the assumption recorded here earlier:
- Terryville → Plymouth → Litchfield, as expected.
- Mystic → Stonington → New London. Mystic spans Stonington and Groton, and 37 Willow Street
  settles which, where a village-level mapping could only have said "one of two".
- Cornwall Bridge → **two different towns**. 226 Kent Rd S is in Cornwall; 56 River Rd is in
  **Sharon**, across the Housatonic. Both are Litchfield, so the county is unaffected, but the
  earlier note that "Cornwall Bridge is in Cornwall" was not true of every address in it.
- Kensington → Berlin → Hartford, and Baltic → Sprague → New London, as expected.

**The other six are premises in other states**, and they exposed a real bug: the geocoder was
being asked about the *licensing* state, not the state the premises are in. Connecticut's
hemp-consumables credential is held by out-of-state manufacturers, so the build was asking for
"4811 Dusharme Dr, Brooklyn Center, **CT**" — which of course returns no match, and that no-match
was recorded as though the address were unfindable. Asked about Minnesota it resolves immediately
to Hennepin. The query now takes the state from the address itself and falls back to the licensing
state. Only these six rows were affected across all three tables, and the fix also closed 34 Texas
rows whose cached lookups were re-run.

Five remain, and they are genuine: Peachtree Corners GA (whose street field contains a ZIP, not a
street), Hancock NY, Deep Gap NC, Stoneham MA and Charlotte Amalie **VI** — the Census address
geocoder does not cover the US Virgin Islands. Each says so on the row.

**107 rows asserted a county and denied it in the same breath.** CT 72, TX 34, MA 1 carried a
county *and* a leftover "county unavailable=" note, because the county had arrived later from a
different source while the earlier no-match note stayed behind — a live caveat on a settled value,
which is the placeholder-as-published-value CLAUDE.md forbids. Every fill now clears the note as
part of setting the county, the gap-note branch no longer fires on a row that already has one, and
verify.py fails if any row ever asserts a county and denies it again.

That also fixed a misleading count: fill_counties reported Connecticut as 24 gaps when it had 5,
because a row whose `county_source` invites a revisit passed through the unfilled branch on every
run. The figure is now counted from the rows themselves.

## The business directory: 355 to 2,087 entries

All 11 audited directories are now data rather than HTML. Three layouts, three parsers: six are category tables (Great Lakes, Plains, Mountain, Southwest, South Central, Pacific), two are one block per business (Mid-Atlantic, Southeast), and California is an audit table plus a category-number key.

Two independent checks that the parse is faithful, both against figures the reports state themselves:
- **California: exactly 371 businesses, exactly 242 unverified** — the two numbers HANDOFF records for R9c.
- **Mid-Atlantic: exactly 173 kept, exactly 50 confirmed** — the numbers its own report states.

Every row uses one of HANDOFF's 17 standard categories, none blank. The national and New England directories describe each category in a sentence rather than naming it, so 431 rows were mapped to the standard name with the directory's own wording kept.

**A source that disagrees with itself.** The Mid-Atlantic directory's tally line says 71 corrected and 52 unverified, but its own per-entry badges say 63 and 60. The total (173) and the confirmed count (50) agree; the split does not.

**22 directory entries hold a state licence.** Matched by normalised name against all 50,636 licence rows (re-run after the New Jersey rebuild gave NJ real licence numbers; the match is unchanged at 22) and written to data/clean/business_licence_matches.csv — Cookies (12 licences across CA, CO and OR), STIIIZY, Papa & Barkley, Old Pal, Treez and others. HANDOFF puts a licensed operator in the licence database rather than the directory, so each is flagged on its row with its licence numbers. **Nothing was deleted**: the match is on name alone, and a false positive would quietly drop a real directory entry, which is worse than a missed match. California's three show why it is a judgement call — GAIACA (waste services) holds two distributor licences and Capitol Compliance Management holds an event-organizer licence, so they are genuinely both a service business and a licensee.

All three of those jobs are now done (13 Nov 2026) — California's contact detail is parsed out of
the report's PART 2 prose, and the entries are grouped into 1,945 profiles with national firms
under a parent. See "The business directory: profiles, California's contact detail" above.

## Counties: 92% to 97%, filled from official sources only

CLAUDE.md requires a county on every row. 4,039 of 50,544 rows had none because their regulator does not publish one. 2,925 are now filled and **every county in all three tables carries a source** (it was 3,677 with none). Nothing was inferred from a town name alone.

Two sources, both official:
- **The US Census geocoder** (`geocoding.geo.census.gov`, no key, benchmark `Public_AR_Current`, vintage `Current_Current`) resolved 1,886 of 2,229 distinct street addresses to a county. Address-level, which is what makes it safe for the township states HANDOFF warns about — Ohio, Michigan, Indiana, Illinois, Minnesota, North Dakota, New Jersey and Pennsylvania all have town names that repeat across counties, and a name-only lookup would mis-assign them. Results are cached in data/raw/census_county_lookup.csv so a re-run is free and the provenance stays on disk.
- **New Jersey's own CRC Government Relations table**, already in data/raw/, pairs County with Municipality. It filled 498 of the old 586 NJ rows, leaving 88 unincorporated places inside townships (Somerset, Williamstown, Marlton, Atco). Superseded on 12 Nov 2026: NJ is now built from its permit PDFs, which print a county on every facility address, so only 2 of 678 rows lack one. The CRC table still fills the locations that have no permit.

An authoritative county list now lives in data/raw/census_counties_by_state.csv — 3,229 counties across 56 states and territories, from Census TIGERweb — and verify.py checks every county against its own state. That check found four distinct problems, all now fixed or flagged:

- **A bug of mine.** `title()` mangles Mc- names, so Texas's McLennan became "Mclennan" — 135 TX rows, plus McCulloch, McMullen and Missouri's McDonald. Normalised to the Census spelling.
- **Variant spellings**: NY "St Lawrence", FL "Saint Lucie", FL "Dade" (renamed Miami-Dade in 1997), and the independent cities MD "Baltimore City" and MO "St. Louis City". 174 rows normalised in total.
- **Placeholders in a county column**: Texas DSHS writes "Out Of State/Unknown" and "Private". 71 rows blanked, with the original value recorded on the row — a placeholder must never be published as a county.
- **Premises outside the licensing state.** 41 rows. Connecticut's hemp-consumables credential is held by manufacturers in Buffalo, Atlanta, Bend and Chattanooga, so their premises county is genuinely in another state. The county is kept and the row says it must be left off a Connecticut county map. A further 24 rows have county names ambiguous across several states and say so.

## Mid-Atlantic counts: what this table says vs what the reports say

These figures are different measures on different dates and must not be reconciled into single numbers.

| Jurisdiction | This table | Regulator / report figure | Why they differ |
|---|---|---|---|
| NY | 3,056 rows; 2,286 distinct licence numbers; 2,452 rows Active; 385 rows are live applications with no licence number | OCM 2025 Annual Report: 2,008 active across the five headline categories (30 Nov 2025) | A year later, one row per location rather than per licence, and the dataset includes proximity-protected applicants |
| DC | 79 retailers (77 Active) plus 21 non-retail facilities | ABCA August 2026 report: 66 total retailers | Different source and date; the GIS layer includes internet retailers. Do NOT treat 79 as a correction to 66 |
| PA | 181 dispensary locations | MMAB: 196 locations operational (1 June 2026); Auditor General: 195 "actively" | PASDA's layer is DOH Jan 2025 vintage, well before both |
| NJ | 586 organisation-location rows across 517 organisations | CRC: 541 businesses opened (Feb 2026); 397 licensed under CREAMM (Dec 2025) | CRC publishes organisations, not licences, and counts operating facilities in Metrc on a different basis |
| MD | 191 licences: 128 dispensary, 31 processor, 27 grower, 5 testing lab (from the MCA's own licence extract, Sept 2026) | MCA Jan 2026 briefing: 109 dispensaries operating | Different measures: the extract counts credentials of every type, the briefing counts operating dispensaries eight months earlier. The MCA's own operational flag covers only its 45 social-equity licences (37 Yes, 8 No) and is recorded per row as a separate measure |
| DE | 14 storefronts across 6 operator brands | The DE report read 13 addresses across 5 brands in Oct 2026 | A sixth brand now appears: Field Supply Cannabis & Provisions, 4555 Kirkwood Hwy, Wilmington |

Data defects found in the official sources and recorded per row rather than silently repaired:
- **NY**: OCM attaches one `Location ID` to two different addresses on 4 applicant rows (Brooklyn/Woodside and Brooklyn/Bronx). Flagged in `extra_details`; ids carry a local suffix so the rows stay distinct.
- **PA**: PASDA carries both typos the audit flagged. `Bulter` is corrected to Butler in `town` (the facility's own name says Butler County) with `Bulter` kept in `town_as_listed`. The `RISE - King of Prussia` ZIP 19706 is left as published and flagged — its two sibling King of Prussia rows carry 19406.
- **MD**: the locator table's header columns are mislabelled relative to its cells — the header reads Dispensary, County, Address while the cells are Dispensary, Address, County. The build keys on cell position. A header-order parse would file every address as a county.
- **MD**: one address cannot be split into street and town (`782 State Route 3 N Gambrills Maryland 21054` — no comma and no street suffix); its town is left empty and flagged.

## Open loose ends
- NY hemp producer list: agriculture.ny.gov returns HTTP 403 to programmatic clients and a file download to the browser pane, so neither the HTML list nor the PDF could be captured. Needs a manual download. Note it carries personal emails — private columns only.
- ~~MD dashboard extract (XLSX) is stored raw but unparsed.~~ **PARSED 14 Nov 2026** — it is the source Maryland is now built from. See "Maryland publishes licence numbers after all" below.
- MD dispensary locator also drives an ArcGIS instant app (appid 51f75b68c70f4c6d8ab0aa4f4de74f55 on maryland.maps.arcgis.com); its feature service is still unresolved, but the value of doing so dropped on 14 Nov 2026: Maryland is now built from the MCA's own licence extract, and the locator's addresses and counties are already parsed. The app would at most supply addresses for the 5 dispensaries whose trading name does not match the locator. It would NOT supply the 63 grower/processor/lab addresses, which the MCA does not publish anywhere.
- PA hemp permit map: **attempted 14 Nov 2026 and recorded UNAVAILABLE** (`pa-hemp-permit-sites` in sources.json). It is a Power BI report on a Power BI Report Server, so its rows render client-side — Part 5 saw only "Loading data...". Tried the report URL over http and https and the SSRS export parameters `rs:Format=CSV` and `rs:Command=Render&rs:Format=CSV` (which work for a paginated report, not a .pbix). All timed out at the network level, and so did the host root, so the host did not respond to this network at all — which says nothing about what it publishes. Needs the browser pane or a person. PA still has no hemp data; its 197 rows are medical dispensaries only.
- DC: the GIS retailer count (77 Active, Nov 2026) is NOT a correction to ABCA's 66 retailers (Aug 2026 report) — different source and date. Do not reconcile them into one number.
- NY: the OCM dataset has 3,056 rows but only 2,286 distinct licence numbers, and 385 rows carry no licence number at all — those are applicants under proximity protection. Row count is not a licence count, and neither figure should be compared directly with the OCM 2025 Annual Report's 2,008 active (30 Nov 2025).
- CT: 465 records in the fresh download are applications that never became licences (DENIED, EXPIRED APPLICATION / NSF PAYMENT DUE, WITHDRAWN, INSPECTION INCOMPLETE) and are excluded from the licence table. The rule is in scripts/build_new_england.py; it keys on statusreason, not status, because "EXPIRED APPLICATION / PROVISIONAL LICENSE EXPIRED" was a real licence.
- Talaria: FULLY SETTLED (12 Nov 2026). Excluded from businesses_master.csv because the Mid-Atlantic audit marks it MOVED OUT as an NJ wholesaler, and HANDOFF puts a licensed operator in the licence database — where it now sits as **W000018**, Class 3 — Wholesaler, 950 Mount Holly Rd, Edgewater Park (Burlington), expiring 2026-11-25, from the CRC's own permit PDF.
- CropLine (NV): link to Green Therapeutics' licence, not the directory.
- Crested River Cannabis Company (MN): confirm licence and move.
- Coastal Cannabis Consulting (LA): founder tied to a pharmacy licensee; decide.
- American Cannabis Company (CO): ownership unverified.
- California businesses: the DCC match is DONE and the three hits are now reviewed on evidence (13 Nov 2026) — GAIACA Waste Revitalization and Capitol Compliance Management are the same business as their licensee and belong in the licence database; CannaBiz Consulting Group matched only a licensee's trading name ("Coachella Sc, LLC") and needs a person. The 242 unverified entries are still unverified — a separate job from the licence match. CDPH hemp registrations are still unmatched.
- California state report (R91) and Michigan (R56) audits are light; check law and tax pages against official sites.
- New Hampshire audit is light (about 42 rows). Its 7 ATC rows were hand-transcribed from a DHHS PDF and still have no stored raw file.
- New Jersey audit is lighter than the rest (about 78 claims).
- Arkansas Act 629 enrolled text and Act 934 changes: check before quoting.
- Market figures for Utah, Arizona, New Mexico and Mississippi came from secondary summaries; replace with official figures.
- Thin domain lists (Iowa, Arkansas, Wyoming, Tennessee): add official sites as found.
