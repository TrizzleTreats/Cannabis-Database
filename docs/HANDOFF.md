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
- Standard types (16): Cultivation, Nursery, Manufacturing, Retail, Delivery, Transport & Distribution, Testing Lab, Microbusiness, Consumption Lounge, Research, Caregiver, Event Organizer, Operator, Hemp Grower, Hemp Processor, Hemp Retail. Medical vs adult-use is a separate filter.
  - Event Organizer and Operator were added on 12 Nov 2026 after the build met them in real data: California issues 193 Event Organizer licences and Colorado 8 Operator licences (a company running a licensed business on the licensee's behalf). Neither fits any of the original 14.
  - **The standard type is carried in two columns, added 12 Nov 2026** (`scripts/add_standard_type.py`, mapping in `scripts/standard_types.py`). `standard_type` holds exactly one of the 16 — the LEAD activity, so a facet has one value per licence and counts cannot double. `standard_types_all` holds every one of the 16 the licence authorises, `; `-joined in the canonical order this list is written in. It is always populated and equals `standard_type` on the 50,612 single-activity rows; 24 rows carry more than one. The regulator's own official licence name stays in `licence_type` and the build's own grouping stays in `category` — neither is rewritten, exactly as `status` keeps the regulator's own status wording.
  - The lead is picked by a **fixed precedence, most downstream (most consumer-facing) first**: Retail, Consumption Lounge, Delivery, Transport & Distribution, Hemp Retail, Manufacturing, Hemp Processor, Cultivation, Hemp Grower, Nursery, then the types that never appear in a compound. Source order cannot be the rule: the same New Jersey combination arrives as "Cultivation; Manufacturing; Retail Store", as "Retail Store; Cultivation" and as "Dispensing, Cultivating", so keying on it would scatter one real combination across three different leads. Downstream-first means someone searching for a place that can sell to them finds every licence that may.
  - Where a regulator's or the build's own category word has no standard of its own, the mapping is **fixed and documented here rather than improvised**, the same rule the standard statuses follow:
    - "Retail Store" → **Retail** (8,618 rows); this list's name is Retail. "Medical Caregiver" → **Caregiver**; "Hemp Retailer" (178) → **Hemp Retail**, a near-duplicate spelling of the same type, not a second type.
    - "Medical Dispensary" (262) and Connecticut's "Hybrid Retailer" (52) → **Retail**. Medical vs adult-use is a separate filter and `program` already carries it, so a dispensary is retail and "hybrid" is the programme pair rather than an extra activity.
    - Connecticut's "Micro-Cultivation" (17) → **Cultivation**, NOT Microbusiness. §21a-420 needs ≥15,000 sq ft of grow space for a cultivator and 2,000–10,000 for a micro-cultivator: the same activity at a smaller cap. A microbusiness (California, New York, Massachusetts) covers several activities under one licence, so folding the two together would merge two genuinely different things. The cap is in `tier`.
    - Hemp-side manufacture is **Hemp Processor**: Connecticut's "Manufacturer Of Hemp Consumables" (89) and "THC Beverage Manufacturer" (32, hemp programme), and Rhode Island's "Industrial Hemp Handler" (7). Texas's "Consumable Hemp Product" licence is the same activity and this table already categorised it Hemp Processor, and Oregon's "Hemp Handler Certificate" likewise — the in-table precedent decides both.
    - Connecticut's "Packager" (7) → **Manufacturing**, because Packaging is one of the Manufacturing activity tags below.
    - Hemp distribution → **Transport & Distribution**: Rhode Island's "Hemp Distributor" (21) and Connecticut's "THC Beverage Wholesaler" (10). They sell to retailers, not to the public, so they are not Hemp Retail; there is no hemp-specific distribution type among the 16, and `program` = Hemp keeps them separable from cannabis distributors. (Rhode Island's own rule pairs § 1.7 distributor/retailer in one fee class; the standard type tracks the activity, not the fee schedule.) Vermont's "Wholesaler" (9) and the Massachusetts/Connecticut "Transporter" (18) map there too.
    - The genuinely multi-activity licences, where the tag list earns its keep: New Jersey's compound CRC classes (133 rows, e.g. "Cultivator, Manufacturer, Retailer" → Cultivation; Manufacturing; Retail); Rhode Island's "Industrial Hemp Dual" (3) → Hemp Grower; Hemp Processor; Rhode Island's **Compassion Center (Hybrid)** (9) → Cultivation; Manufacturing; Retail, because the RI report's Part 11 licence table reads "medical retail + cultivation/manufacture for patients; vertically integrated" (§ 21-28.6-12; 560-10-10-1 § 1.8), with § 1.9 "(Hybrid)" adding adult-use sales; and Vermont's **Integrated** (2) → Cultivation; Manufacturing; Retail, from § 971(b)(1) "operate vertically integrated under one license", § 973(a) (cultivate/package/label/test/transport and produce products) and the CCB Municipal FAQ's "the retail portion of an integrated license". NB Vermont's integrated licence was repealed on 1 July 2026 by Act 176 (§ 909 repealed), so those 2 rows are legacy and their status needs a check.
  - `standard_types_all` is NOT the activity-tags column in the licence-column list above. That column, still to be built, uses the Manufacturing vocabulary immediately below; this one uses the 16 standard types. Two different vocabularies, so two different columns.
- Manufacturing activity tags (multiple allowed): Extraction, Infusion/Edibles, Pre-rolls, Vapes, Packaging; "Unknown" when not confirmed.
- Standard statuses (10), roughly from most to least live: Active, Provisional, Limited Operations, Pending, Suspended, Expired, Inactive, Surrendered, Canceled, Revoked. Default search shows Active + Provisional.
  - Limited Operations, Inactive and Canceled were added on 12 Nov 2026, again from real data: California publishes 1,622 Canceled and 156 Limited Operations, and Oregon 796 Inactive. None of them fits the original 7, and folding them into the nearest neighbour would have erased a real distinction — Canceled is an administrative end, Surrendered is a voluntary hand-back, Revoked is an enforcement outcome.
  - Where a regulator's word still has no standard of its own, the mapping is fixed and documented rather than improvised. Washington's "Closed (Permanent)" maps to Surrendered and "Closed (Temporary)" to Suspended; its "Active Title Certificate" maps to Active and "Former Title Certificate" to Expired; "On Hold" maps to Suspended. Oregon's "Not Approved" is a refused application, not a licence — it is kept as Pending and flagged, the same way Connecticut's DENIED records are excluded.
  - The state's own wording always stays in `status`. `standard_status` is for one search to span every state.
- Business categories (17): Legal; Accounting and Tax; Insurance; Real Estate; Construction and Facilities; Security; Cash Management; Waste Services; Staffing and Recruiting; Compliance and Consulting; Marketing and Advertising; Software; Packaging and Labelling; Grow Supplies and Equipment; Extraction and Lab Equipment; Consumer Brands; Hemp and CBD Products. Each tagged Local / Regional / National AND cannabis-only / hemp-only / both / general.
- Licences tied to one company are grouped under a parent profile (matched by legal name and company email domain).
- Businesses that hold a state or tribal cannabis licence, or operate under another company's licence, go in the licence database, not the business directory (link them to the licensee's parent profile).
- "Hemp licence only" entries (growers, processors, plain resellers) come from licence data, not the business directory.
- Plain state-registered hemp retail shops (e.g. Tennessee TABC, Kentucky ABC, Louisiana ATC/LDH, Alabama ABC, Texas DSHS) are licence data, not directory entries. Only hemp makers/brands go in Category 12.
- California business directory is grouped by 10 sub-regions with a county field.
- Counts must carry a date and must not mix "issued", "approved", "licensed", "pending renewal" and "operating".
- Unverified entries stay out of the public site until checked.

## New Jersey: built from the permit PDFs (decided 12 Nov 2026)

The CRC publishes no licence number in any list. Its permitted-businesses page gives
organisations — business types per organisation, locations in one cell, an expiration YEAR — and
links an issued permit PDF per business. That PDF **is** the licence, so New Jersey is built from
the permits, one row per permit, not from the HTML table.

`licence_type` keeps the Commission's own class wording in title case (`Class 5 — Retailer`,
`Medical Retailer`) with the verbatim all-caps string in `extra_details`; the all-caps is
typography, not wording. `category` uses only values `standard_types.py` already knows, so the
permits introduced no new vocabulary:

| CRC class | category | standard_type |
|---|---|---|
| CLASS 1 - CULTIVATOR, MEDICAL CULTIVATOR | Cultivation | Cultivation |
| CLASS 2 - MANUFACTURER, MEDICAL MANUFACTURER | Manufacturing | Manufacturing |
| CLASS 3 - WHOLESALER, CLASS 4 - DISTRIBUTOR | Transport & Distribution | Transport & Distribution |
| CLASS 5 - RETAILER, MEDICAL RETAILER | Retail Store | Retail |
| CLASS 6 - DELIVERY | Delivery | Delivery |

A **medical retailer is Retail Store with `program` = Medical**, not a separate category: HANDOFF
already holds that medical vs adult-use is a filter and never a type, and this table already
categorises Pennsylvania's 197 medical-only dispensaries that way. A **wholesaler and a
distributor are both Transport & Distribution**, the value NJ's rows already used and the one VT's
own "Wholesaler" maps to.

**Status rests on the regulator's own heading, never on the expiry date.** The CRC publishes both
tables under "Active Cannabis Business Permits & Licenses", which is the only status wording it
gives these businesses, so `standard_status` is Active and `status` quotes the heading. 72 permits
print an expiry already past; that is flagged per row and the two are not reconciled, because a
past expiry is not proof a licence is dead — the CRC may simply not have posted the renewal.

**A licence number belongs to the premises**, as in Washington. Two numbers are each printed on
two permits at one address under different holders (RE000774 at Plainfield, RE001037 at
Willingboro), so those rows take NY's own `~n` discriminator and must never be merged.

**Consumption-area endorsements are not licences.** Five exist, numbered from the retailer's own
licence plus `-CA000n`. They are named on the licence they attach to, in `extra_details`, the way
Oregon's endorsements are — counting them as licences would inflate the licence count.

**Counties are adjudicated on the permit's own ZIP.** Every facility address goes through the
Census geocoder; where it disagrees with the permit's printed county AND the permit's ZIP matches
the ZIP of the address the geocoder matched, the two describe the same building and the permit's
county field is wrong, so the Census value is published with the printed one kept on the row.
Where the ZIPs differ the geocoder settles nothing and the regulator's value stands, flagged.

**Pipeline order.** Several of these columns are derived and no builder writes them, so a rebuild
must be followed by the rest of the chain or verify.py fails loudly:

```
scripts/fetch_nj_permits.py            # 517 PDFs, URLs read out of the saved CRC page
scripts/parse_nj_permits.py            # -> data/clean/nj_crc_permits.csv
scripts/verify_nj_permit_counties.py   # adds county_geocoded / county_check
scripts/build_mid_atlantic.py          # NJ rows from the permits
scripts/fill_counties.py --apply       # fills what the permits do not cover
scripts/fill_counties.py --canonicalise
scripts/add_standard_type.py --apply   # derived, not written by any builder
scripts/verify.py
```

One trap found the hard way: `fill_counties.py` re-processes any row whose `county_source` starts
with "US Census geocoder", so an already-adjudicated NJ county must not be labelled that way or a
later pass relabels it. verify.py now fails if any NJ row does.

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
- **Connecticut: use the traditional eight counties.** DECIDED 12 Nov 2026. Census replaced CT's eight counties with nine Councils of Governments / Planning Regions as its county-equivalents in 2022, so current TIGER and the Census geocoder return e.g. "Capitol Planning Region" where other states return "Hartford County". This project uses the traditional eight — Fairfield, Hartford, Litchfield, Middlesex, New Haven, New London, Tolland, Windham — because that is what ct_towns.csv, the CT reports and the public expect. The two vocabularies must never share the county column, and scripts/verify.py fails if a Planning Region appears in a CT row. The town-to-county mapping comes from the Census ACS2021 vintage, the last published before the change, cached in data/raw/census_ct_town_county_2021.csv (173 towns). CT county values are therefore NOT comparable with the current Census county list, which is why verify.py checks CT against the traditional set instead.
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
