"""Market facts for each state page's Market tab: the size of the legal market, and the
number of registered medical patients. Official figures only.

Hand-restated from each state's audited report (reports/regions/), almost always from a
row of its audit tables marked Confirmed or Corrected with an official source, so the
figure carries the audit's own verdict. Each fact has the same shape as the quick
reference (scripts/quick_reference_data.py):

  text       the figure, with exactly what it measures and the period or date it covers
  cite       who publishes it (the regulator, tax agency or official dataset)
  url        an official link the report itself cites (a host in domains/all-domains.txt)
  confirmed  False when the audit marks the figure Unverified, secondary-only, or "do not
             use"; the page then says "not yet confirmed" and shows only the reason
  note       what the one-line text would otherwise mislead about

Measures are never mixed. A state that publishes tax collections rather than sales is
shown as tax collections, never converted into a sales estimate; a point-in-time count
of active cards is not a count of patients who bought anything; a month is not a year.

scripts/build_market.py checks, among other things, that every number in a fact's text
appears in that state's own audited report.
"""

FIELDS = ["market", "patients"]


def F(text, cite, url, confirmed=True, note=""):
    return {"text": text, "cite": cite, "url": url, "confirmed": confirmed, "note": note}


def NOT_CONFIRMED(why, cite="", url=""):
    return F(None, cite, url, confirmed=False, note=why)


def NONE(text, cite, url):
    """A confirmed absence: there is no legal market, or no medical programme."""
    return F(text, cite, url)


MARKET = {
    "AL": {
        "market": NOT_CONFIRMED("Sales began in June 2026. No official total of sales or medical tax "
                                "collections had been published when the report was audited."),
        "patients": NOT_CONFIRMED("The patient registry opened in spring 2026, but no official patient "
                                  "count was found."),
    },
    "AK": {
        "market": F("Alaska publishes no statewide retail sales figure. The state taxes cannabis "
                    "once, by weight, when a grower sells it, so its official data records weight "
                    "taxed, not what consumers spent.", "Department of Revenue (AS 43.61)",
                    "https://www.commerce.alaska.gov/web/amco/"),
        "patients": NOT_CONFIRMED("The only count found (97 active registry patients, 31 Dec 2025) reached "
                                  "the report through a secondary source."),
    },
    "AZ": {
        "market": F("Marijuana tax collected, fiscal year 2026: $281,961,540, counted when the "
                    "Department of Revenue received it (state, county and city sales tax plus the "
                    "16% excise).", "Arizona Department of Revenue",
                    "https://azdor.gov/sites/default/files/document/MJ_byTotalCollectionsCategory.pdf",
                    note="This is tax collected, not sales. Arizona sales totals in circulation come "
                         "from secondary summaries and are not shown."),
        "patients": F("70,444 qualifying patients (86,770 cardholders including caregivers), July 2026.",
                      "Arizona Department of Health Services, monthly report",
                      "https://www.azdhs.gov/documents/licensing/medical-marijuana/reports/2026/mm-jul26.pdf"),
    },
    "AR": {
        "market": NOT_CONFIRMED("The sales series (e.g. 2025) reached the report through press reports of "
                                "Department of Finance and Administration figures; the department's own "
                                "release was not opened."),
        "patients": F("119,452 active patient cards, 17 Oct 2026.", "Arkansas Department of Health",
                      "https://healthy.arkansas.gov/programs-services/data-statistics-registries/medical-marijuana/",
                      note="A point-in-time count of active cards."),
    },
    "CA": {
        "market": F("Cannabis tax revenue, April-June 2026: $152.0m excise and $109.7m sales tax, "
                    "$261.7m in all, as first reported (it excludes returns still outstanding).",
                    "California Department of Tax and Fee Administration",
                    "https://cdtfa.ca.gov/industry/cannabis/retailers.htm",
                    note="Annual cannabis sales totals in circulation are marked \"do not use\" in the "
                         "audit: they do not reconcile with CDTFA's own quarterly figures."),
        "patients": NOT_CONFIRMED("No statewide count of registered medical patients was found."),
    },
    "CO": {
        "market": F("Marijuana sales, calendar 2025: $1,315,678,364 (2024: $1,397,131,978).",
                    "Colorado Department of Revenue, marijuana sales reports",
                    "https://cdor.colorado.gov/data-and-reports/marijuana-data/marijuana-sales-reports"),
        "patients": F("53,384 registered patients and 888 caregivers, February 2026.",
                      "Colorado Department of Public Health and Environment, Medical Marijuana Registry",
                      "https://cdphe.colorado.gov/medical-marijuana-registry-providers"),
    },
    "CT": {
        "market": F("Retail cannabis sales, calendar 2025: $290,029,618 (2024: $293,600,093), "
                    "summed from the state's weekly retail sales dataset.",
                    "Department of Consumer Protection, data.ct.gov ucaf-96h6",
                    "https://data.ct.gov/api/views/f382-bnu5"),
        "patients": F("31,617 registered patients, 2,787 caregivers, December 2025.",
                      "Department of Consumer Protection, data.ct.gov 6rq7-6x2s",
                      "https://data.ct.gov/resource/6rq7-6x2s.json"),
    },
    "DE": {
        "market": F("Adult-use sales in the first month of legal sales (August 2025): $7,354,293.",
                    "Office of the Marijuana Commissioner",
                    "https://news.delaware.gov/2025/09/02/omc-reports-strong-first-month-of-recreational-cannabis-sales/",
                    note="The most recent official figure found; it covers one month, not a year."),
        "patients": NOT_CONFIRMED("The patient count found (July 2024) is from a secondary source."),
    },
    "DC": {
        "market": F("Medical cannabis sales, August 2026: $9,846,506 across the programme "
                    "(July: $10,605,830).", "Alcoholic Beverage and Cannabis Administration, monthly report",
                    "https://abca.dc.gov",
                    note="A monthly figure. DC licenses no adult-use sales."),
        "patients": F("143,556 registered DC-resident patients, August 2026.",
                      "Alcoholic Beverage and Cannabis Administration, monthly report", "https://abca.dc.gov",
                      note="Registered patients, not patients who bought: 39,382 were served in August."),
    },
    "FL": {
        "market": NOT_CONFIRMED("No official dollar figure for sales was found in the audited report."),
        "patients": F("943,271 qualified patients with an active ID card, 23 Oct 2026.",
                      "Office of Medical Marijuana Use, weekly update (23 Oct 2026)", "",
                      note="Published on knowthefactsmmj.com, the Department of Health's medical marijuana "
                           "site. That host is not yet on this project's list of official domains, so no "
                           "link is shown until it is added."),
    },
    "GA": {
        "market": NOT_CONFIRMED("No official sales figure for Georgia's low-THC programme was found."),
        "patients": NOT_CONFIRMED("No official registry count was found."),
    },
    "HI": {
        "market": F("General excise tax collected on medical cannabis sales, 2025: $2,828,019 "
                    "(a tax figure, not sales).", "Hawaii Department of Health, annual report to the Legislature",
                    "https://health.hawaii.gov/opppd/files/2026/01/OMCCR_MCDLS-AR-to-2026Leg_sub-20260120.pdf"),
        "patients": F("29,142 registered patients, September 2026.",
                      "Hawaii Department of Health, Medical Cannabis Registry program statistics",
                      "https://health.hawaii.gov/medicalcannabisregistry/submenu/program-statistics/"),
    },
    "ID": {
        "market": NONE("None: there is no legal marijuana market.", "Idaho Code §37-2701",
                       "https://legislature.idaho.gov/statutesrules/idstat/Title37/T37CH27/SECT37-2701"),
        "patients": NONE("None: Idaho has no medical programme.", "Idaho Code §37-2701",
                         "https://legislature.idaho.gov/statutesrules/idstat/Title37/T37CH27/SECT37-2701"),
    },
    "IL": {
        "market": F("Adult-use cannabis sales, calendar 2025: $1,506,740,852.75.",
                    "Department of Financial and Professional Regulation, monthly sales figures",
                    "https://idfpr.illinois.gov/content/dam/soi/en/web/idfpr/forms/auc/adult-use-cannabis-monthly-sales-figures.pdf",
                    note="Adult-use only; medical sales are reported separately."),
        "patients": F("133,887 active registered patients, 30 Apr 2025 (56,389 were served that month).",
                      "Department of Public Health, Medical Cannabis Patient Program update",
                      "https://mcpp.illinois.gov/updates/mcpp-update-display.mcpp-update-04302025.html",
                      note="The latest official count found; no 2026 count was published in a form the audit could open."),
    },
    "IN": {
        "market": NONE("None: there is no legal marijuana market.", "IC 35-48",
                       "https://www.in.gov/dor/i-am-a/business-corp/business-faq/"),
        "patients": NONE("None: Indiana has no medical programme.", "IC 35-48",
                         "https://www.in.gov/dor/i-am-a/business-corp/business-faq/"),
    },
    "IA": {
        "market": F("Medical cannabidiol sales, 2025: $13,749,665, before tax.",
                    "Iowa Department of Health and Human Services, Medical Cannabidiol Board reporting",
                    "https://hhs.iowa.gov/health-prevention/medical-cannabis"),
        "patients": F("18,012 active patients at the end of 2025.",
                      "Iowa Department of Health and Human Services",
                      "https://hhs.iowa.gov/health-prevention/medical-cannabis"),
    },
    "KS": {
        "market": NONE("None: there is no legal marijuana market.", "K.S.A. 21-5706",
                       "https://kslegislature.gov/li_2022/b2021_22/statute/065_000_0000_chapter/065_041_0000_article/065_041_0001_section/065_041_0001_k/"),
        "patients": NONE("None: Kansas has no medical programme.", "K.S.A. 65-4101",
                         "https://kslegislature.gov/li_2022/b2021_22/statute/065_000_0000_chapter/065_041_0000_article/065_041_0001_section/065_041_0001_k/"),
    },
    "KY": {
        "market": NOT_CONFIRMED("Sales began in December 2025; no official sales figure was found."),
        "patients": NOT_CONFIRMED("The patient counts found are secondary; the Office of Medical Cannabis "
                                  "publishes no dashboard the audit could open."),
    },
    "LA": {
        "market": NOT_CONFIRMED("No official sales figure for therapeutic marijuana was found."),
        "patients": NOT_CONFIRMED("Louisiana has no patient registry, and no official patient count was found."),
    },
    "ME": {
        "market": F("Adult-use cannabis sales, 2025: $246.4m.", "Office of Cannabis Policy, annual report",
                    "https://www11.maine.gov/dafs/ocp/resources/annual-reports",
                    note="Adult use only. Medical sales by caregivers and dispensaries are not in this figure."),
        "patients": F("112,547 patient certifications printed in 2025, including reprints. Maine "
                      "publishes no count of unique patients.", "Office of Cannabis Policy, 2025 medical programme annual report",
                      "https://www.maine.gov/dafs/ocp/sites/maine.gov.dafs.ocp/files/inline-files/2025%20MMCP%20Annual%20Report.pdf"),
    },
    "MD": {
        "market": NOT_CONFIRMED("Calendar 2025 sales (about $1.17bn) reached the report through secondary "
                                "sources; the Maryland Cannabis Administration's dashboard was not confirmed directly."),
        "patients": NOT_CONFIRMED("No official patient count was confirmed in the audit."),
    },
    "MA": {
        "market": F("Adult-use gross sales, calendar 2025: more than $1.65 billion, a record, across "
                    "46.3 million transactions.", "Cannabis Control Commission",
                    "https://masscannabiscontrol.com/2026/01/massachusetts-adult-use-cannabis-sales-generated-1-65-billion-in-2025/"),
        "patients": F("Nearly 100,000 registered patients, July 2023.", "Cannabis Control Commission, industry report (Feb 2025)",
                      "https://masscannabiscontrol.com/2025/02/cannabis-control-commission-releases-industry-report-assessing-adult-and-medical-use-cannabis-markets/",
                      note="The latest official count found is from 2023."),
    },
    "MI": {
        "market": NOT_CONFIRMED("Calendar 2025 adult-use sales ($3.17bn) reached the report as Cannabis "
                                "Regulatory Agency figures republished by secondary sources."),
        "patients": NOT_CONFIRMED("The registry figures found are secondary republications."),
    },
    "MN": {
        "market": F("First year of licensed retail (from September 2025): more than $250 million in "
                    "sales, about $150 million adult-use and $100 million medical, at state-licensed "
                    "businesses.", "Office of Cannabis Management, one-year update (15 Sept 2026)",
                    "https://content.govdelivery.com/accounts/MNOCM/bulletins/426f237",
                    note="Tribal businesses are not included; no aggregate tribal sales total is published."),
        "patients": NOT_CONFIRMED("The registry figures found (over 90,000 by September 2026) are secondary; "
                                  "the registry page was not opened directly."),
    },
    "MS": {
        "market": NOT_CONFIRMED("Sales figures in circulation conflict and come from secondary summaries."),
        "patients": F("66,041 registered patients, 15 Dec 2025.",
                      "Mississippi State Department of Health, Medical Cannabis Program annual report 2025",
                      "https://www.mmcp.ms.gov/"),
    },
    "MO": {
        "market": F("Marijuana sales, calendar 2025: $1,517.26 million ($1,343.57 million adult-use, "
                    "$173.69 million medical), summed from the regulator's monthly figures.",
                    "Department of Health and Senior Services, Division of Cannabis Regulation",
                    "https://health.mo.gov/business-professionals/cannabis-regulation",
                    note="Monthly figures are revised slightly after reconciliation; the rounded total "
                         "reported elsewhere is $1.52bn."),
        "patients": NOT_CONFIRMED("The patient counts found reached the report through secondary sources."),
    },
    "MT": {
        "market": F("Cannabis sales, January-September 2026: $249,241,577 ($225,104,330 adult-use, "
                    "$24,137,247 medical).", "Montana Department of Revenue, cannabis sales reports",
                    "https://revenue.mt.gov/card/cannabis/sales-reports/",
                    note="Nine months, not a full year."),
        "patients": NOT_CONFIRMED("No current official count of medical cardholders was found."),
    },
    "NE": {
        "market": NONE("None yet: no dispensary licence had been issued when the report was audited.",
                       "Neb. Rev. Stat. §71-24,111", "https://mcc.nebraska.gov"),
        "patients": NOT_CONFIRMED("No official count of qualified patients was found."),
    },
    "NV": {
        "market": F("Taxable cannabis sales, fiscal year 2026 (July 2025-June 2026): $695,995,234 "
                    "(fiscal 2025: $757,714,911).", "Nevada Department of Taxation",
                    "https://tax.nv.gov/wp-content/uploads/2026/09/NV-Cannabis-Revenue-FY27.pdf"),
        "patients": F("8,718 medical cardholders, September 2026.",
                      "Division of Public and Behavioral Health, monthly cardholder report",
                      "https://www.dpbh.nv.gov/siteassets/regulatory/mm-patient-cardholder-registry/dta/monthly-reports/mmr-monthly-stats-eom-september-2026.pdf"),
    },
    "NH": {
        "market": NOT_CONFIRMED("No official sales figure for New Hampshire's alternative treatment centres was found."),
        "patients": F("14,705 registered patients (14,698 adults and 7 minors), 2024.",
                      "Department of Health and Human Services, Therapeutic Cannabis Program 2024 data report",
                      "https://dhhs.nhdoit.acsitefactory.com/sites/g/files/ehbemt476/files/documents2/tcp-data-report-2024.pdf"),
    },
    "NJ": {
        "market": F("Cannabis sales, calendar 2025: $1,164,220,150 ($1,118,003,986 adult-use, "
                    "$46,216,164 medical).", "Cannabis Regulatory Commission",
                    "http://www.state.nj.us/cannabis/documents/meetings/2026-05-14/May%2014%202026%20slides.pdf"),
        "patients": F("52,877 registered patients and 3,397 caregivers, end of 2025.",
                      "Cannabis Regulatory Commission", "https://www.nj.gov/cannabis/medicinalcannabis/caregivers/"),
    },
    "NM": {
        "market": NOT_CONFIRMED("Calendar 2025 sales figures conflict ($567m-$568m against a rejected $628m) "
                                "and all reached the report through secondary sources; none is adopted."),
        "patients": F("60,400 active enrolled patients, data as of 3 Aug 2026.",
                      "New Mexico Department of Health, July 2026 report",
                      "https://www.nmhealth.org/publication/view/report/9756/"),
    },
    "NY": {
        "market": F("Cannabis sales, 2025 to the date of the annual report: $1,577.8M ($1,482.3M "
                    "adult-use, $95.5M medical).", "Office of Cannabis Management, Annual Report 2025 (Table 8)",
                    "https://cannabis.ny.gov/ocm-annual-report-2025",
                    note="Year to date when the report was written, not the full calendar year."),
        "patients": F("69,031 registered patients and 4,820 certifying practitioners, 1 Oct 2026.",
                      "Office of Cannabis Management", "https://cannabis.ny.gov/medical-cannabis"),
    },
    "ND": {
        "market": F("Medical marijuana sales, fiscal year 2024 (July 2023-June 2024): $22,424,000.",
                    "North Dakota Department of Health and Human Services, annual report FY2024",
                    "https://www.hhs.nd.gov/sites/default/files/documents/DOH%20Legacy/MM/Annual-Report-FY-2024-archive.pdf",
                    note="The latest official annual figure found."),
        "patients": F("Cards issued: 10,982, as of 8 Oct 2026 (the programme page's own counter).",
                      "North Dakota Department of Health and Human Services, Division of Medical Marijuana",
                      "https://www.hhs.nd.gov/mm/dispensary-locations",
                      note="The counter's wording is \"Cards Issued\"; it is not stated to be a count of unique patients."),
    },
    "OH": {
        "market": NOT_CONFIRMED("Ohio's adult-use sales totals in circulation (e.g. calendar 2025) come from "
                                "secondary summaries of Division of Cannabis Control data."),
        "patients": F("476,589 registered patients, of whom 73,396 had both an active registration and "
                      "an active recommendation, 30 Sept 2026.",
                      "Department of Commerce, Division of Cannabis Control, By the Numbers",
                      "https://com.ohio.gov/cannabis",
                      note="Registered is not the same as active: only the 73,396 could buy that day."),
    },
    "OK": {
        "market": F("Medical marijuana excise tax collected, 2025: $45,300,591 (January-September 2026: "
                    "$32,024,393).", "Oklahoma Medical Marijuana Authority, licensing and tax data",
                    "https://oklahoma.gov/omma/about/licensing-and-tax-data.html",
                    note="Tax collected, not sales. OMMA publishes no sales total; dividing the 7% excise "
                         "back into sales is arithmetic, not an official figure."),
        "patients": F("304,186 licensed patients and 1,036 caregivers, 1 Oct 2026.",
                      "Oklahoma Medical Marijuana Authority, licensing and tax data",
                      "https://oklahoma.gov/omma/about/licensing-and-tax-data.html"),
    },
    "OR": {
        "market": NOT_CONFIRMED("Calendar 2025 sales figures (about $926m) reached the report through secondary "
                                "sources that disagree with each other; none is confirmed from the OLCC."),
        "patients": NOT_CONFIRMED("The Oregon Medical Marijuana Program's patient total was not extracted from "
                                  "its statistics in a form the audit could confirm."),
    },
    "PA": {
        "market": F("Medical marijuana sales since the programme began: $9.6B, as of June 2026.",
                    "Department of Health, Medical Marijuana Advisory Board (24 June 2026)",
                    "https://www.pa.gov/content/dam/copapwp-pagov/en/health/documents/topics/documents/programs/medical-marijuana/June%2024%202026%20MMAB%20Mtg.pdf",
                    note="A cumulative total since 2018, not an annual figure."),
        "patients": F("438,727 patient certifications and 1,937 practitioners, June 2026.",
                      "Department of Health, Medical Marijuana Advisory Board (24 June 2026)",
                      "https://www.pa.gov/content/dam/copapwp-pagov/en/health/documents/topics/documents/programs/medical-marijuana/June%2024%202026%20MMAB%20Mtg.pdf",
                      note="Certifications, the board's own measure; registrations since the programme began "
                           "(1,129,606) are a different, larger count."),
    },
    "RI": {
        "market": F("Retail cannabis sales, July-September 2025: $31,118,759. The Cannabis Control "
                    "Commission's combined figure of $43,763,017 adds $12,644,258 of wholesale sales.",
                    "Cannabis Control Commission, Q3 2025 sales release",
                    "https://ccc.ri.gov/sites/g/files/xkgbur991/files/2025-11/Press%20Release-%20Cannabis%20Sales%202025%20Q3.pdf",
                    note="One quarter, not a year."),
        "patients": F("7,097 registered medical patients, Q3 2025.",
                      "Cannabis Control Commission, Q3 2025 sales release",
                      "https://ccc.ri.gov/sites/g/files/xkgbur991/files/2025-11/Press%20Release-%20Cannabis%20Sales%202025%20Q3.pdf"),
    },
    "SC": {
        "market": NONE("None: there is no legal marijuana market.", "S.C. Code §44-53-370",
                       "https://www.scstatehouse.gov/code/t44c053.php"),
        "patients": NONE("None: South Carolina has no medical programme.", "S.C. Code §44-53-110(27)",
                         "https://www.scstatehouse.gov/code/t44c053.php"),
    },
    "SD": {
        "market": NOT_CONFIRMED("No official sales figure was found; the Department of Health reports programme "
                                "fee revenue, which is not sales."),
        "patients": NOT_CONFIRMED("The patient count adopted in the report (19,821, 2 Sept 2026) reached it through "
                                  "a secondary source."),
    },
    "TN": {
        "market": NONE("None: there is no legal marijuana market.", "Tenn. Code §39-17-418",
                       "https://www.tn.gov/agriculture/farms/hemp-industry.html"),
        "patients": NONE("None: Tennessee has no medical programme.", "Tenn. Code §39-17-402",
                         "https://www.tn.gov/agriculture/farms/hemp-industry.html"),
    },
    "NC": {
        "market": NONE("None: there is no legal marijuana market under state law.", "N.C.G.S. 90-95(a)",
                       "https://ncleg.gov/EnactedLegislation/SessionLaws/HTML/2021-2022/SL2022-32.html"),
        "patients": NONE("None: North Carolina has no state medical programme.", "N.C.G.S. 90-94",
                         "https://ncleg.gov/EnactedLegislation/SessionLaws/HTML/2021-2022/SL2022-32.html"),
    },
    "TX": {
        "market": NOT_CONFIRMED("No official sales total exists for the Compassionate Use Program or for "
                                "consumable hemp; the estimates in circulation are secondary."),
        "patients": NOT_CONFIRMED("Registry figures (e.g. 135,470 at the end of 2025) reached the report through "
                                  "press reports of DPS figures, not a DPS publication."),
    },
    "UT": {
        "market": F("Medical cannabis sales, September 2026: $16,661,000.",
                    "Utah medical cannabis programme, monthly report (September 2026)",
                    "https://medicalcannabis.utah.gov/wp-content/uploads/2026-09-Monthly-Report.pdf",
                    note="A monthly figure. Annual totals in circulation were not confirmed from a primary table."),
        "patients": F("117,285 active patient cardholders, September 2026.",
                      "Utah medical cannabis programme, monthly report (September 2026)",
                      "https://medicalcannabis.utah.gov/wp-content/uploads/2026-09-Monthly-Report.pdf"),
    },
    "VT": {
        "market": F("Cannabis tax revenue, fiscal year 2026: $30,758,285 ($21,752,769 excise, $9,005,517 "
                    "sales tax).", "Joint Fiscal Office, FY26 cannabis revenue tracker",
                    "https://ljfo.vermont.gov/assets/Subjects/Cannabis-Revenue-Tracking/FY26-Cannabis-Revenue-Tracker-Jun.pdf",
                    note="Tax revenue, not sales."),
        "patients": NOT_CONFIRMED("No official count of registered medical patients was found."),
    },
    "VA": {
        "market": NOT_CONFIRMED("No official medical sales figure was found; adult-use retail does not open "
                                "until 1 July 2027."),
        "patients": F("Nearly 115,000 patients, fiscal year 2025.",
                      "Cannabis Control Authority report to the General Assembly (RD974, 2025)",
                      "https://rga.lis.virginia.gov/Published/2025/RD974",
                      note="The report's own wording; a precise 114,859 in circulation is a secondary tabulation."),
    },
    "WA": {
        "market": NOT_CONFIRMED("Calendar 2025 sales ($1.14bn) are listed in the report as still to be confirmed "
                                "from the Department of Revenue's own tables."),
        "patients": F("27,749 adult and 85 minor patients in the medical database, July 2026.",
                      "Washington State Department of Health",
                      "https://doh.wa.gov/you-and-your-family/cannabis/medical-cannabis"),
    },
    "WV": {
        "market": F("No annual total is published. Monthly sales reported in Metrc ranged from "
                    "$6,954,344.81 (November 2023) to $8,401,200.12 (August 2024).",
                    "Office of Medical Cannabis, biennial report (Nov 2023-Oct 2025)", "https://omc.wv.gov"),
        "patients": F("35,394 active patients, 31 Oct 2025.",
                      "Office of Medical Cannabis, biennial report (Nov 2023-Oct 2025)", "https://omc.wv.gov",
                      note="The report's table gives 35,395 for the same date; its narrative gives 35,394."),
    },
    "WI": {
        "market": NONE("None: there is no legal marijuana market.", "Wis. Stat. ch. 961",
                       "https://docs.legis.wisconsin.gov/document/acts/2019/68,54n"),
        "patients": NONE("None: Wisconsin has no medical programme.", "Wis. Stat. ch. 961",
                         "https://docs.legis.wisconsin.gov/document/acts/2019/68,54n"),
    },
    "WY": {
        "market": NONE("None: there is no legal marijuana market.", "W.S. 35-7-1031",
                       "https://agriculture.wy.gov/divisions/wsf/index.php?section=hemp-program"),
        "patients": NONE("None: Wyoming has no medical programme.", "W.S. 35-7-1031",
                         "https://agriculture.wy.gov/divisions/wsf/index.php?section=hemp-program"),
    },
}
