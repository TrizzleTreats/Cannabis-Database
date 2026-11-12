# Cannabis Database Project — Handoff (updated 2 Nov 2026)

## Goal
A free, hands-off public website: a clickable US map of cannabis and hemp laws plus a searchable database of every licensed operator and the businesses serving the industry. A private version keeps full contact details for my own outreach. Research was done with Meta Muse deep research (research run, then audit in a fresh chat). The site will be built in Claude Code, with scripts/agents updating it daily.

## Status
- Research phase COMPLETE for all 9 regions: every state + DC, federal, the national business directory, and all regional business directories have been researched and audited.
- Next:
  1. Post-election re-checks after 3 Nov 2026. Idaho HJR 4 is on the ballot (constitutional amendment: only the Legislature could legalise marijuana/narcotics). Re-check Part 0 and Part 9 for any state with a cannabis measure once results are certified. Florida and Arkansas had no cannabis measure on the 2026 ballot.
  2. Claude Code build: set up folders and docs, then add domain lists, then download and build licence files for every state.
  3. Settle the loose ends listed below.

## Regions and report numbers
Final audited reports are named by region and state. "b" = regional business directory.

| Region | States | Files |
|---|---|---|
| 1 New England | ME, NH, VT, MA, CT, RI | Maine_edits, NH_audit, Vern (VT), Ma_audit, Ct_audit, Ri_audit, Ne_audits (business directory, Categories 1–12), Ne_audit.pdf (detailed audit of directory Categories 1–6) |
| 2 Mid-Atlantic | NY, NJ, PA, DE, MD, DC | R21 NY, R22 PA, R23 NJ, R24 DE, R25 DC, R26 MD, R2b |
| 3 Southeast | VA, WV, NC, SC, GA, FL | R31 WV, R32 VA, R33 NC, R34 SC, R35 GA, R36 FL, R3b |
| 4 South Central | KY, TN, AL, MS, LA, AR | R41 LA, R42 AR, R43 AL, R44 TN, R45 MS, R46 KY, R4b |
| 5 Great Lakes | OH, MI, IN, IL, WI, MN | R51 IL, R52 OH, R53 IN, R54 WI, R55 MN, R56 MI, R5b |
| 6 Plains | IA, MO, KS, NE, ND, SD, OK | R61 IA, R62 ND, R63 SD, R64 KS, R65 MO, R66 NE, R67 OK, R6b |
| 7 Southwest | TX, NM, AZ, NV | R71 TX, R72 NV, R73 AZ, R74 NM, R7b |
| 8 Mountain | CO, UT, ID, MT, WY | R81 MT, R82 CO, R83 ID, R84 UT, R85 WY, R8b |
| 9 Pacific | CA, OR, WA, AK, HI | R91 CA, R92 HI, R93 OR, R94 AK, R95 WA, R9b (OR/WA/AK/HI businesses), R9c (California businesses) |

Plus: Fed (federal research audit) and National (national business directory audit — not the longer-named unaudited file).

Only the complete versions of R31, R34, R36, R53 and R63 should be kept (earlier half versions covered only Parts 7–12). R9c must be the California business directory, not a copy of R91.

## Data files (from the earlier chat)
- new_england_licences.csv — 3,986 licences, all six New England states, one schema
- Per-state: ma_licences.csv, ct_licences.csv, ri_licences.csv, vt_licences.csv; ma_towns.csv, ct_towns.csv
- usda_hemp_licensees_national.csv — 3,281 USDA hemp licences, all states (May 2026 FOIA PDF)
- ct_backers_private.csv — 207 CT cannabis backers (PRIVATE ONLY)
- national_businesses.csv, new_england_businesses.csv, businesses_master.csv (355 combined)
- Maine_Cannabis_Licensees.xlsx

## Key federal facts (verified)
- Split scheduling: state-licensed MEDICAL + FDA products in Schedule III from 28 Apr 2026 (91 FR 22714); all adult-use stays Schedule I. 2024 broad proposal not final.
- 280E generally lifted for Schedule III medical; adult-use still fully subject. Dual medical/adult-use licensees must split activity.
- Hemp: PL 119-37 §781 effective 12 Nov 2026, but PL 119-103 §2019 limits it until 11 Dec 2026; full total-THC definition + 0.4 mg/container cap after 11 Dec 2026.
- USDA DEA-lab testing enforcement delayed to 31 Dec 2026; medical rider runs through 11 Dec 2026; no federal banking law.
- Some states' laws follow federal schedule changes automatically or by board action (e.g. Idaho §37-2702(d)); some block it (e.g. Tennessee Pub. Ch. 789). Whether tribal medical programmes count as "state-licensed" is unresolved — mark Verify.

## Data decisions
- One master licence table with private columns; the public site reads a public view without them. Public records (incl. individuals' published contacts) are kept in private columns.
- Licence columns: state, licence number, programme (medical/adult-use/hemp/testing), state's official licence name, standard type, activity tags, tier, state status wording, standard status, issue/expiry/first-issue dates, legal name, DBA, individual flag, parent company/group, vertical integration flag, owners, address, town, town as listed, county + county source, location basis, town opt-in/allows activity, website, contact name/phone/email, law-firm-contact flag, social equity status, latitude/longitude, endorsements, operating yes/no, source name/link/date, notes, "extra details" field (state-specific items; promote to a column once several states share it).
- Standard types: Cultivation, Nursery, Manufacturing, Retail, Delivery, Transport & Distribution, Testing Lab, Microbusiness, Consumption Lounge, Research, Caregiver, Hemp Grower, Hemp Processor, Hemp Retail. Medical vs adult-use is a separate filter.
- Manufacturing activity tags (multiple allowed): Extraction, Infusion/Edibles, Pre-rolls, Vapes, Packaging; "Unknown" when not confirmed.
- Standard statuses (7): Active, Provisional, Pending, Suspended, Expired, Surrendered, Revoked. Default search shows Active + Provisional.
- Business categories (17): Legal; Accounting and Tax; Insurance; Real Estate; Construction and Facilities; Security; Cash Management; Waste Services; Staffing and Recruiting; Compliance and Consulting; Marketing and Advertising; Software; Packaging and Labelling; Grow Supplies and Equipment; Extraction and Lab Equipment; Consumer Brands; Hemp and CBD Products. Each tagged Local / Regional / National AND cannabis-only / hemp-only / both / general.
- Licences tied to one company are grouped under a parent profile (matched by legal name and company email domain).
- Businesses that hold a state or tribal cannabis licence, or operate under another company's licence, go in the licence database, not the business directory (link them to the licensee's parent profile).
- "Hemp licence only" entries (growers, processors, plain resellers) come from licence data, not the business directory.
- Plain state-registered hemp retail shops (e.g. Tennessee TABC, Kentucky ABC, Louisiana ATC/LDH, Alabama ABC, Texas DSHS) are licence data, not directory entries. Only hemp makers/brands go in Category 12.
- California business directory is grouped by 10 sub-regions with a county field.
- Counts must carry a date and must not mix "issued", "approved", "licensed", "pending renewal" and "operating".
- Unverified entries stay out of the public site until checked.

## Site layout
- Home: US map colour-coded by legal status (dark green medical+adult, medium green medical only, lighter green adult-only if needed); two-letter state labels; Alaska/Hawaii inset. Database and Federal Laws buttons next to the map. Footer on every page: "legal information, not legal advice" linking to full terms. Glossary. No report-error button, no separate news feed.
- State page tabs: Overview, Laws, Licences, Taxes, Business, Market.
  - Overview: clickable county map (counties/parishes/boroughs/independent cities/consolidated city-counties/DC wards; click county → towns/cities → local page), then headlines, then quick-reference boxes (legal status, possession, home grow, medical yes/no, licences open/capped, combined tax rate, regulator, last updated).
  - Laws: possession/use, home grow, medical, hemp, business rules, employment, consumer rules, pending bills — plain-English summary beside exact text and official link.
  - Licences: types under the state's official names; clicking a type opens the database pre-filtered (filters in URL); windows/lotteries; social equity; hemp; data sources.
  - Taxes, Business, Market tabs as previously agreed.
- County/city pages: single scrolling page — map, quick facts, local rules, database link.
- Federal page tabs: Overview, Laws, Taxes, Licences, Pending bills, plus a state hemp-plan table and a section on federal rules for people.
- Database page: toggle "Licensed Operators" / "Industry Services", search, side filters, sortable results, export, compare tab.
- Profiles: name/DBA + parent link, status/type badges, contacts, small map, all licences, activity tags, violations, sources.
- Later, not now: county colour-coding, radius search, map pins, CRM notes, AI assistant, claim-your-listing, paid tiers.

## Local government quirks to model
- Townships (OH, MI, IN, IL, MN, ND, NJ, PA) share names across counties — always store the county.
- Parishes in Louisiana; boroughs and the Unorganized Borough in Alaska; independent cities in Virginia; consolidated city-counties (e.g. Denver, Broomfield, San Francisco, Jacksonville, Louisville Metro, Lexington-Fayette, Nashville-Davidson, Butte-Silver Bow, Carson City, Honolulu); Wisconsin has cities, villages AND towns with shared names; Hawaii has no municipal governments below county.
- Unincorporated areas (e.g. the Las Vegas Strip is Clark County, not the City of Las Vegas; Los Angeles city vs unincorporated LA County).
- Montana green/red counties; Colorado local opt-in by business type; Michigan opt-in (medical) vs opt-out (adult-use); Missouri local bans need a public vote; New Mexico and Minnesota towns cannot ban.

## Lessons from the research
- Always check an audit covers Parts 0–12 (several came back covering only Parts 7–12: WV, SC, FL, IN, SD).
- Check for duplicate or wrong files (R9c first came back as a copy of R91). Start a new chat with no other files attached when this happens.
- Some files keep leftover lines from earlier runs (e.g. "Run 1 remains a separate document", "no audit commissioned") — check the headings, not the last line.
- PDFs cut off tables — always use HTML.
- Statute quotes from Justia/LawServer are not official; check against official code sites (flagged in GA, TN, MS).
- Some states renumbered statutes (Indiana IC 35-48-1 → 35-48-1.1 in 2025) — link to current numbers.
- Market figures in Utah, Arizona, New Mexico and Mississippi came from secondary summaries — pull from official sources in the build.
- "Already listed" duplicate checks only work when other directories are attached; do de-duplication across all directories in the build instead.
- Claude can download official files itself once their domains are allowed; some sites need a headless browser. USDA's hemp search site has a broken certificate; use the FOIA PDF on www.ams.usda.gov.
- Most states don't publish owners in their downloads; owner lookup is a later, per-business step.

## Loose ends to settle in the build
- Talaria: moved out of the Mid-Atlantic directory as a licensed NJ wholesaler, but kept in Great Lakes — treat as a licensed operator everywhere.
- CropLine (NV): transports under Green Therapeutics' CCB licence — link to that licensee, not the business directory.
- Crested River Cannabis Company (MN): likely OMA/OCM licensee — confirm and move.
- Coastal Cannabis Consulting (LA): founder linked to a Louisiana pharmacy licensee — decide.
- American Cannabis Company (CO): moved out as a historical MED operator; current ownership unverified.
- R9c California businesses: 242 of 371 unverified; DCC licence-list matching not done for any entry — match all business and owner names against the DCC download. Same for CDPH hemp registrations.
- R91 California state report: light audit (claim groups, 96 of 186 unverified) — check law and tax pages against DCC/CDTFA during the build.
- Michigan (R56) audit is light — treat finer details with caution.
- National firms appear in several regional directories (e.g. Baker Donelson, HUB, Brink's, Holland & Hart) — merge under parent profiles.
- Arkansas Act 629 enrolled text and Act 934 changes need checking before quoting.

## Domains
MASTER_DOMAINS.md (grouped by region and state) and all-domains.txt (one per line) hold 1,238 official sites, pulled from every audited state report (Regions 1–9) and the federal audit, merged with the earlier hand-made New England and Mid-Atlantic lists.

- NH_audit is light (about 42 audit rows) — treat finer New Hampshire details with caution.
- R23 New Jersey audit is lighter than the others (about 78 claims checked).
- R2b Mid-Atlantic businesses: 173 kept (50 confirmed, 71 corrected, 52 unverified).
