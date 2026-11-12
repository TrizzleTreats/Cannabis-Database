# Cannabis Database

A free public website: a clickable US map of cannabis and hemp laws, plus a searchable database of every licensed operator and of the businesses that serve the industry. A private version keeps full contact details for the owner's own outreach. Research came from Meta Muse deep research (research run, then an independent audit). The site will update itself daily with scripts and agents.

Read docs/HANDOFF.md before any work. It is the master plan: data schema, site layout, local government quirks, lessons and loose ends. Keep docs/STATUS.md up to date as work happens.

## Key rules
- Primary sources only: official government sites (see domains/). News, blogs, law firms, Justia, FindLaw, LegiScan and Wikipedia are never a source of truth.
- Private data never goes public. data/private/ is git-ignored and must never be deployed. Personal phone numbers and emails of individuals stay in private columns only.
- Massachusetts licence file: drop the EIN/TIN column. Never use it.
- Every fact and every count carries a source link and a date. Never mix "issued", "approved", "licensed", "pending renewal" and "operating" in one count.
- Unverified entries stay off the public site until checked.
- Private columns — strip before any deploy. `key_people_private` in businesses_master.csv, national_businesses.csv and new_england_businesses.csv; `contact_name`, `contact_phone`, `contact_email` and `owners` in the master licence table. All of data/private/. data/clean/ is tracked in git with these columns present, so the public build must drop them explicitly — git-ignoring data/private/ is not by itself enough.
- Always store the county for towns, townships and other same-name places.
- Federal baseline (as of Nov 2026): state-licensed MEDICAL marijuana and FDA products are Schedule III from 28 Apr 2026 (91 FR 22714); all adult-use stays Schedule I. 280E lifted for medical only. Hemp: PL 119-37 §781 effective 12 Nov 2026, limited by PL 119-103 §2019 until 11 Dec 2026; then total-THC definition and 0.4 mg/container cap. USDA DEA-lab testing enforcement delayed to 31 Dec 2026. Medical rider through 11 Dec 2026. No federal banking law.
- Standard licence types (14), statuses (7) and business categories (17) are listed in docs/HANDOFF.md. Show the state's own licence name on state pages; use the standard type for search.

## Where things live
- docs/ — HANDOFF.md (plan), STATUS.md (progress), FILE_INDEX.md (every file and its original name)
- domains/ — official sites Claude Code may use (MASTER_DOMAINS.md by state; all-domains.txt one per line)
- reports/federal/ — federal law report
- reports/regions/<region>/<state>/ — audited state reports (Parts 0–12)
- reports/businesses/ — national and regional business directories (California has its own)
- data/raw/<state>/ — original downloaded files, never edited
- data/clean/ — processed licence and business tables
- data/private/ — private-only data (never published)
- site/ — the website (later)
- scripts/ — download and update scripts (later)
