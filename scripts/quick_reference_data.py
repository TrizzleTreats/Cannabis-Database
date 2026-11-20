"""Quick-reference facts for each state page: possession, home grow, the state's own
cannabis tax, and the regulator. HANDOFF's state Overview asks for these boxes.

Hand-restated from the audited report for each state (reports/regions/), never from
memory. The usual places: section 1.3 (possession and home grow), 1.4 (medical),
2.1 (tax), 9.1 (regulators). Each fact carries:

  text       what the page shows, in plain words, or None when not confirmed
  cite       the statute, rule or act the report gives for it
  url        an official link the report itself cites (a host in domains/all-domains.txt).
             Where the report gives no section-level link, the nearest official page it
             cites; `cite` then names the exact section. Never a URL built by hand.
  confirmed  False when the report marks the figure itself Verify / Unverified /
             secondary-only. The page then says "not yet confirmed" and shows nothing
             else: CLAUDE.md keeps unverified facts off the public site.
  note       anything the one-line text would otherwise mislead about

The date of each fact is the report's own "Last audited" date, which
data/clean/legal_status.csv already reads from the report.

A Verify marker on the *verbatim wording* of a quotation, where the figure itself is
stated as fact in the final report, does not unconfirm the figure; a Verify on the
figure does.

"state_tax" is the state's cannabis-specific tax only. General sales tax and local
taxes are named where the report confirms them, never totalled into one rate: the
combined rate varies by town, and adding rates from different bases would be wrong.

Written out by scripts/build_quick_reference.py to data/clean/quick_reference.csv.
"""

FIELDS = ["possession", "home_grow", "state_tax", "regulator", "public_use", "employment", "driving",
          "medical", "edibles"]


def F(text, cite, url, confirmed=True, note=""):
    return {"text": text, "cite": cite, "url": url, "confirmed": confirmed, "note": note}


def NOT_CONFIRMED(why, cite="", url=""):
    return F(None, cite, url, confirmed=False, note=why)


# Re-checked against official pages on 20 Nov 2026 (see docs/STATUS.md).
CHK = 'Re-read in the official text on 20 Nov 2026.'
NM_PDF = 'https://www.rld.nm.gov/wp-content/uploads/2023/08/ARTICLE-2C-Cannabis-Regulation-_-Chapter-26-Drugs-and-Cosmetics.pdf'
NM_NOTE = "From the Regulation and Licensing Department's own copy of the Act (posted August 2023). Re-read in the official text on 20 Nov 2026."
IA_URL = 'https://www.legis.iowa.gov/docs/code/124E.pdf'


QUICK = {
    "AK": {
        "possession": F("Adults 21+: 1 oz or less. At home, more than 1 oz and under 4 oz is "
                        "protected for personal use by the state constitution's privacy right.",
                        "AS 17.38.020(1); Ravin v. State, 537 P.2d 494 (Alaska 1975)",
                        "https://www.akleg.gov/",
                        note="Home-grown harvest kept where it was grown is not capped by weight "
                             "(AS 17.38.020(2)). A store's daily sale limit is a separate rule."),
        "home_grow": F("6 plants per adult, no more than 3 mature; 12 per household, no more "
                       "than 6 mature.", "AS 17.38.020(2)", "https://www.akleg.gov/"),
        "state_tax": F("No state retail cannabis tax and no state sales tax. The only state "
                       "cannabis tax is a by-weight excise paid by cultivators. Many local "
                       "governments add their own retail taxes.", "AS 43.61.010",
                       "https://www.akleg.gov/"),
        "regulator": F("Alcohol and Marijuana Control Office (AMCO) and the Marijuana Control "
                       "Board", "AS 17.38", "https://www.commerce.alaska.gov/web/amco/"),
    },
    "AZ": {
        "possession": F("Adults 21+: 1 oz or less, of which no more than 5 g may be concentrate.",
                        "A.R.S. §36-2852(A)(1)",
                        "https://www.azleg.gov/viewdocument/?docName=https://www.azleg.gov/ars/36/02850.htm"),
        "home_grow": F("6 plants per adult at their primary residence; 12 per residence where "
                       "two or more adults live. Locked and out of public view.",
                       "A.R.S. §36-2852(A)(2)",
                       "https://www.azleg.gov/viewdocument/?docName=https://www.azleg.gov/ars/36/02850.htm"),
        "state_tax": F("16% excise on adult-use sales, on top of transaction privilege (sales) "
                       "tax. It does not apply to medical sales to registered patients.",
                       "A.R.S. §42-5452(A)", "https://www.azleg.gov/ars/42/05452.htm"),
        "regulator": F("Arizona Department of Health Services (ADHS)", "A.R.S. Title 36, ch. 28.1, 28.2",
                       "https://www.azdhs.gov/licensing/marijuana/"),
    },
    "AR": {
        "possession": F("Registered patients and caregivers: up to 2.5 oz of usable marijuana. "
                        "Not legal for anyone else.", "Ark. Const. Amendment 98 §3",
                        "https://www.dfa.arkansas.gov/wp-content/uploads/Medical_Marijuana_Rules_1.pdf"),
        "home_grow": F("Not allowed, including for patients and caregivers.",
                       "Ark. Const. Amendment 98 §21 (\"Limitation on growing\")",
                       "https://www.dfa.arkansas.gov/office/medical-marijuana-commission/"),
        "state_tax": F("4% special privilege tax on each sale of usable marijuana by a "
                       "cultivator, dispensary or other marijuana business.",
                       "Act 1098 of 2017",
                       "https://www.arkleg.state.ar.us/Home/FTPDocument?path=%2FACTS%2F2017R%2FPublic%2FACT1098.pdf"),
        "regulator": F("Medical Marijuana Commission, within the Department of Finance and "
                       "Administration", "Ark. Const. Amendment 98",
                       "https://www.dfa.arkansas.gov/office/medical-marijuana-commission/"),
    },
    "CA": {
        "possession": F("Adults 21+: 28.5 g of cannabis and 8 g of concentrated cannabis.",
                        "HSC §11362.1(a)(1)-(2) (Proposition 64)",
                        "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=HSC&sectionNum=11362.1"),
        "home_grow": F("6 living plants per private residence, in a locked space not visible "
                       "from a public place. Local ordinances may add rules.",
                       "HSC §11362.1(a)(3), §11362.2",
                       "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=HSC&sectionNum=11362.1"),
        "state_tax": F("15% cannabis excise on retail gross receipts, collected by the retailer, "
                       "from 1 Oct 2025 through 30 June 2028 (it was 19% from 1 July to 30 Sept 2025).",
                       "RTC §34011.2 as amended by AB 564 (Ch. 127, Stats. 2025)",
                       "https://cdtfa.ca.gov/industry/cannabis/retailers.htm"),
        "regulator": F("Department of Cannabis Control (DCC)", "AB 141 (2021)",
                       "https://www.cannabis.ca.gov/cannabis-laws/"),
    },
    "CO": {
        "possession": F("Adults 21+: 1 oz is protected by the state constitution; state law "
                        "raises the possession ceiling to 2 oz.",
                        "Colo. Const. art. XVIII §16; HB 21-1090", "https://med.colorado.gov/"),
        "home_grow": F("6 plants per adult, no more than 3 mature, in an enclosed, locked space.",
                       "Colo. Const. art. XVIII §16", "https://med.colorado.gov/"),
        "state_tax": F("Adult use: 15% state retail marijuana sales tax at the register, and a "
                       "15% excise on the first sale from a cultivator. Exempt from the 2.9% "
                       "general sales tax. Medical: 2.9% state sales tax only.",
                       "C.R.S. Title 39, art. 28.8; SB 17-267",
                       "https://content.leg.colorado.gov/agencies/legislative-council-staff/marijuana-taxes%C2%A0"),
        "regulator": F("Marijuana Enforcement Division (MED), Department of Revenue",
                       "C.R.S. §44-10-201", "https://med.colorado.gov/"),
    },
    "CT": {
        "possession": F("Adults 21+: 1.5 oz on the person, and up to 5 oz in a locked container "
                        "at home or in a locked glove box or trunk.", "Conn. Gen. Stat. §21a-279a(a)",
                        "https://cga.ct.gov/current/pub/chap_420b.htm"),
        "home_grow": F("3 mature and 3 immature plants per adult at their primary residence; "
                       "no more than 12 per household.", "Conn. Gen. Stat. §21a-278c",
                       "https://www.cga.ct.gov/current/pub/chap_420h.htm"),
        "state_tax": F("From 1 Oct 2026, a flat 10.75% adult-use cannabis tax (it was "
                       "THC-based before), plus the 6.35% state sales tax and a 3% municipal "
                       "cannabis tax.", "Conn. Gen. Stat. §12-330ll as changed by PA 26-68 §264; §12-330mm",
                       "https://www.cga.ct.gov/2026/act/pa/pdf/2026PA-00068-R00SB-00001-PA.pdf"),
        "regulator": F("Department of Consumer Protection (DCP)", "Conn. Gen. Stat. ch. 420f, 420h",
                       "https://portal.ct.gov/cannabis/knowledge-base/articles/mmp/qualifying-conditions"),
    },
    "DE": {
        "possession": F("Adults 21+: a personal-use quantity of 1 oz of leaf marijuana, or 12 g "
                        "of concentrate, or products containing up to 750 mg THC.",
                        "16 Del.C. §4701(36)", "https://delcode.delaware.gov/title16/c047/sc01/index.html",
                        note="Registered medical patients may possess up to 6 oz of usable marijuana "
                             "(16 Del.C. §4903A). " + CHK),
        "home_grow": F("Not allowed: home cultivation remains prohibited.",
                       "Office of the Marijuana Commissioner", "https://omc.delaware.gov/adult-use/",
                       note=CHK),
        "state_tax": F("15% of the retail price on adult-use sales. Medical sales are exempt, and so "
                       "are infused beverages sold by a package store or marijuana retail store.",
                       "4 Del.C. §1382(a)-(b)", "https://delcode.delaware.gov/title4/c013/sc08/index.html",
                       note="The tax infused beverages pay instead is not yet confirmed from official "
                            "text. " + CHK),
        "regulator": F("Office of the Marijuana Commissioner (OMC), Department of Safety and "
                       "Homeland Security", "4 Del.C. ch. 13; HB 425 (2024)", "https://omc.delaware.gov/"),
    },
    "DC": {
        "possession": F("Adults 21+: 2 oz or less, and may give up to 1 oz to another adult "
                        "without payment.", "D.C. Code §48-904.01(a)(1)(A)-(B)",
                        "https://code.dccouncil.gov/us/dc/council/code/sections/48-904.01",
                        note="A congressional appropriations rider bars DC from licensing adult-use sales."),
        "home_grow": F("6 plants per adult, no more than 3 mature, inside their principal "
                       "residence; no more than 12 per household, 6 mature.",
                       "D.C. Code §48-904.01(a)(1)(C)",
                       "https://code.dccouncil.gov/us/dc/council/code/sections/48-904.01"),
        "state_tax": F("6% sales tax on medical cannabis. There is no licensed adult-use sale "
                       "to tax.", "D.C. Code §47-2002(a)(7)(A)",
                       "https://code.dccouncil.gov/us/dc/council/code/sections/47-2002"),
        "regulator": F("Alcoholic Beverage and Cannabis Administration (ABCA)", "D.C. Code Title 7, Chapter 16B",
                       "https://abca.dc.gov"),
    },
    "FL": {
        "possession": F("Qualified patients only, within the supply their physician certifies "
                        "(per-route limits in 35- or 70-day supplies). Not legal for anyone else.",
                        "Fla. Stat. §381.986(4)(f)",
                        "https://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0300-0399/0381/Sections/0381.986.html"),
        "home_grow": F("Not allowed, including for patients.", "Fla. Stat. §381.986",
                       "https://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0300-0399/0381/Sections/0381.986.html"),
        "state_tax": F("No cannabis excise tax. Medical marijuana is exempt from sales tax.",
                       "Fla. Stat. §212.08(2)(l)", "https://www.flsenate.gov/Laws/Statutes/2025/212.08"),
        "regulator": F("Office of Medical Marijuana Use (OMMU), Florida Department of Health. "
                       "Hemp: Department of Agriculture and Consumer Services (FDACS).",
                       "Fla. Stat. §381.986",
                       "https://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0300-0399/0381/Sections/0381.986.html"),
    },
    "GA": {
        "possession": F("Registered patients only: low-THC products totalling up to 12,000 mg "
                        "THC, in labelled containers. Marijuana is not legal.",
                        "O.C.G.A. §31-2A-18",
                        "https://dph.georgia.gov/low-thc-oil-registry/patients-and-caregivers"),
        "home_grow": F("Not allowed, for patients, caregivers or anyone else.",
                       "O.C.G.A. §16-13-30", "https://dph.georgia.gov/low-thc-oil-registry/patients-and-caregivers"),
        "state_tax": NOT_CONFIRMED("The audit found no Georgia cannabis-specific tax, but records that as a "
                                   "search result rather than a confirmed negative, and marks the sales-tax "
                                   "treatment of medical products to be checked with the Department of Revenue."),
        "regulator": F("Georgia Access to Medical Cannabis Commission (GMCC); the Department of "
                       "Public Health runs the patient registry.", "O.C.G.A. §16-12-200 et seq.",
                       "https://www.gmcc.ga.gov/"),
    },
    "HI": {
        "possession": F("Registered patients and caregivers: an \"adequate supply\" of up to 4 oz "
                        "of usable cannabis. Adult use is not legal; 3 g or less is a $130 "
                        "violation, not legal possession.", "HRS §329-121; Act 273, SLH 2019",
                        "https://health.hawaii.gov/medicalcannabisregistry/growing-cannabis/"),
        "home_grow": F("Registered patients and caregivers only: up to 10 plants, at a "
                       "registered grow site. Not allowed for anyone else.", "HRS §329-121",
                       "https://health.hawaii.gov/medicalcannabisregistry/growing-cannabis/"),
        "state_tax": F("No cannabis excise tax. Dispensary sales pay the 4% general excise tax, "
                       "plus a county surcharge where one applies.", "HRS ch. 237",
                       "https://health.hawaii.gov/opppd/files/2026/01/OMCCR_MCDLS-AR-to-2026Leg_sub-20260120.pdf"),
        "regulator": F("Department of Health, Office of Medical Cannabis Control and Regulation "
                       "(OMCCR)", "HRS ch. 329D",
                       "https://health.hawaii.gov/medicalcannabisregistry/general-information/marijuana-laws-and-related-documents/"),
    },
    "ID": {
        "possession": F("Not legal in any amount, for any purpose.", "Idaho Code §37-2732(c)(3)",
                        "https://legislature.idaho.gov/statutesrules/idstat/title37/t37ch27/sect37-2732/"),
        "home_grow": F("Not allowed. Growing is \"production\" of a controlled substance.",
                       "Idaho Code §§37-2701(ee), 37-2732(a)",
                       "https://legislature.idaho.gov/statutesrules/idstat/title37/t37ch27/sect37-2732/"),
        "state_tax": F("No cannabis sales tax: there is no legal sale to tax. Idaho's illegal "
                       "drug stamp tax is still on the books, at $3.50 per gram of marijuana.",
                       "Idaho Code §§63-4202, 63-4203",
                       "https://legislature.idaho.gov/statutesrules/idstat/title63/t63ch42/sect63-4203/"),
        "regulator": F("No cannabis regulator. Hemp: Idaho State Department of Agriculture (ISDA).",
                       "Idaho Code Title 22, Chapter 17", "https://agri.idaho.gov/main/hemp/"),
    },
    "IL": {
        "possession": F("Adults 21+ who live in Illinois: 60 g of flower, 10 g of concentrate and "
                        "1,000 mg THC in infused products, counted together. Visitors: half "
                        "those amounts.", "410 ILCS 705/10-10 (P.A. 104-463, eff. 12 June 2026)",
                        "https://ilga.gov/legislation/ILCS/details?ActID=3992&ActName=Cannabis+Regulation+and+Tax+Act.",
                        note="The limits doubled on 12 June 2026; older sources give 30 g."),
        "home_grow": F("Registered medical patients only: up to 5 plants in an enclosed, locked "
                       "space. Not allowed for other adults.", "410 ILCS 705/10-5(b)",
                       "https://ilga.gov/legislation/ILCS/details?ActID=3992&ActName=Cannabis+Regulation+and+Tax+Act."),
        "state_tax": F("Purchaser excise on adult-use sales: 10% on cannabis at or under 35% "
                       "THC, 20% on infused products, 25% above 35% THC. No excise on registered "
                       "patients' purchases. Growers also pay a 7% cultivation privilege tax.",
                       "410 ILCS 705/65-10; 410 ILCS 705/60",
                       "https://witnessslips.ilga.gov/legislation/ilcs/fulltext?DocName=041007050K65-10"),
        "regulator": F("Shared: Department of Financial and Professional Regulation (dispensaries), "
                       "Department of Agriculture (growers), coordinated by the Cannabis Regulation "
                       "Oversight Officer.", "410 ILCS 705",
                       "https://cannabis.illinois.gov/about/meet-the-cannabis-team.html"),
    },
    "IN": {
        "possession": F("Not legal in any amount. Simple possession is a Class B misdemeanor.",
                        "IC 35-48-4-11(a)",
                        "https://public.courts.in.gov/Decisions/api/Document/Opinion?Id=DmYIl2h3bOKWWdQQvJyPZ_rjZgo14Y_LmDtP2-HSBr7Uf3wsJD127SUP1Lq0Mzh20"),
        "home_grow": F("Not allowed. Growing marijuana is an offence under the same section as "
                       "possession.", "IC 35-48-4-11(a)",
                       "https://public.courts.in.gov/Decisions/api/Document/Opinion?Id=DmYIl2h3bOKWWdQQvJyPZ_rjZgo14Y_LmDtP2-HSBr7Uf3wsJD127SUP1Lq0Mzh20"),
        "state_tax": F("None: there is no legal marijuana sale to tax.", "IC 35-48",
                       "https://www.in.gov/dor/i-am-a/business-corp/business-faq/"),
        "regulator": F("No cannabis regulator. Hemp: Office of the Indiana State Chemist (OISC), "
                       "at Purdue University.", "IC 15-15-13", "https://oisc.purdue.edu/hemp/contact.html"),
    },
    "IA": {
        "possession": F("Registered patients only: medical cannabidiol products, up to 4.5 g of "
                        "total THC per 90 days (more only in the cases the statute lists). Marijuana is "
                        "not legal in any amount.", "Iowa Code §124E.9(14)-(15); §124.401(5)",
                        IA_URL, note=CHK),
        "home_grow": F("Not allowed, including for patients: only licensed manufacturers may cultivate.",
                       "Iowa Code §124E.6", IA_URL, note=CHK),
        "state_tax": F("No cannabis-specific tax. Medical cannabidiol pays the 6% state sales tax "
                       "with no exemption, plus a 1% local option tax where adopted.",
                       "Iowa Code §423.2", "https://www.legis.iowa.gov/docs/code/2024/124E.pdf",
                       note="The Medical Cannabidiol Board has recommended a sales-tax exemption; that is not law."),
        "regulator": F("Iowa Department of Health and Human Services, Office of Medical Cannabidiol",
                       "Iowa Code ch. 124E", "https://hhs.iowa.gov/health-prevention/medical-cannabis"),
    },
    "KS": {
        "possession": F("Not legal in any amount. A first conviction is a Class B misdemeanor.",
                        "K.S.A. 21-5706",
                        "https://kslegislature.gov/li_2022/b2021_22/statute/065_000_0000_chapter/065_041_0000_article/065_041_0001_section/065_041_0001_k/"),
        "home_grow": F("Not allowed.", "K.S.A. 21-5706; K.S.A. 65-4101",
                       "https://kslegislature.gov/li_2022/b2021_22/statute/065_000_0000_chapter/065_041_0000_article/065_041_0001_section/065_041_0001_k/"),
        "state_tax": F("No cannabis sales tax: there is no legal sale to tax. The drug tax stamp "
                       "law still requires a dealer holding more than 28 g of marijuana to buy "
                       "stamps at $3.50 per gram.", "K.S.A. 79-5201 et seq.",
                       "https://kslegislature.gov/li_2022/b2021_22/statute/065_000_0000_chapter/065_041_0000_article/065_041_0001_section/065_041_0001_k/"),
        "regulator": F("No cannabis regulator. Hemp: Kansas Department of Agriculture.",
                       "K.S.A. 2-3901 et seq.",
                       "https://www.agriculture.ks.gov/divisions-programs/plant-protection-weed-control/industrial-hemp"),
    },
    "KY": {
        "possession": F("Registered patients: a 30-day supply at home and a 10-day supply on "
                        "their person. Not legal for anyone else.", "KRS 218B.025(1)(a), (c)",
                        "https://apps.legislature.ky.gov/law/statutes/statute.aspx?id=54279"),
        "home_grow": F("Not allowed, including for patients.", "KRS ch. 218B",
                       "https://kymedcan.ky.gov/FAQs/Pages/General-Questions.aspx"),
        "state_tax": F("Medical cannabis sold to cardholders is exempt from state sales and "
                       "excise taxes.", "Office of Medical Cannabis, Banking and Taxes FAQ",
                       "https://kymedcan.ky.gov/FAQs/Pages/Banking-and-Taxes-Questions.aspx",
                       note="The audit did not find the exempting statute section; the source is the regulator's own FAQ."),
        "regulator": F("Cabinet for Health and Family Services, Office of Medical Cannabis (OMC)",
                       "KRS ch. 218B", "https://kymedcan.ky.gov"),
    },
    "LA": {
        "possession": F("Patients with a clinician's recommendation, through LDH-permitted "
                        "pharmacies: up to 71 g of flower per 14 days. For anyone else, 14 g or "
                        "less carries a fine of up to $100 and no jail; it is not legal.",
                        "La. R.S. 40:1046; R.S. 40:966(C)(2)(a)(i)",
                        "https://www.ldh.la.gov/bureau-of-sanitarian-services/medical-marijuana"),
        "home_grow": F("Not allowed: no provision lets a patient or caregiver cultivate.",
                       "La. R.S. 40:1046", "https://www.legis.la.gov/Legis/Law.aspx?p=y&d=96986"),
        "state_tax": F("7% fee on the gross sales of therapeutic marijuana, paid by the licensee.",
                       "La. R.S. 40:1046(H)(4)(c)", "https://www.legis.la.gov/Legis/Law.aspx?p=y&d=96986"),
        "regulator": F("Louisiana Department of Health (LDH), since 1 August 2022",
                       "Acts 491 and 492 of 2022", "https://ldh.la.gov/page/medical-marijuana"),
    },
    "ME": {
        "possession": F("Adults 21+: 2.5 oz, of which no more than 10 g may be concentrate. "
                        "Medical patients: up to 8 lb of harvested cannabis.",
                        "28-B MRS §1501(1)(B); 22 MRS §2423-A",
                        "https://legislature.maine.gov/statutes/28-B/title28-Bch1.pdf"),
        "home_grow": F("Adults 21+: 6 mature and 12 immature plants, and unlimited seedlings, per "
                       "person. Medical patients: the same plant counts.",
                       "28-B MRS §1502; 22 MRS §2423-A",
                       "https://legislature.maine.gov/statutes/28-B/title28-Bch1.pdf"),
        "state_tax": F("Adult use: 14% sales tax from 1 Jan 2026 (10% before), plus an excise on "
                       "cultivators' transfers of $223 per lb of flower and $63 per lb of trim. "
                       "No excise on medical cannabis.", "36 MRS §1811(5); 36 MRS §4923",
                       "http://legislature.maine.gov/statutes/36/title36sec1811.html"),
        "regulator": F("Office of Cannabis Policy (OCP), Department of Administrative and "
                       "Financial Services", "28-B MRS; 22 MRS ch. 558-C",
                       "https://www.maine.gov/dafs/ocp/medical-use"),
    },
    "MD": {
        "possession": F("Adults 21+ (the \"personal use amount\"): 1.5 oz of flower, or 12 g of "
                        "concentrate, or products totalling 750 mg THC.",
                        "Maryland Cannabis Administration FAQ; Md. Const. art. XX",
                        "https://cannabis.maryland.gov/pages/cannabisfaq.aspx",
                        note="More, up to 2.5 oz, is a civil fine rather than a crime."),
        "home_grow": F("2 plants per household of adults 21+ (4 in a medical patient's "
                       "household), out of public view. A landlord may prohibit it.",
                       "Maryland Cannabis Administration FAQ",
                       "https://cannabis.maryland.gov/pages/cannabisfaq.aspx"),
        "state_tax": F("12% sales tax on adult-use cannabis from 1 July 2025 (9% before).",
                       "Md. Tax-General §11-104(k); Budget Reconciliation and Financing Act of 2025",
                       "https://cannabis.maryland.gov"),
        "regulator": F("Maryland Cannabis Administration (MCA)", "Alc. Bev. & Cann. Title 36",
                       "https://cannabis.maryland.gov"),
    },
    "MA": {
        "possession": F("Adults 21+: 2 oz (1 oz before 19 April 2026), and up to 10 oz at home.",
                        "M.G.L. c.94G §7 as amended by St. 2026, c.65 §29",
                        "https://malegislature.gov/Laws/GeneralLaws/PartI/TitleXV/Chapter94G/Section7"),
        "home_grow": F("6 plants per adult at their primary residence; no more than 12 on the "
                       "premises.", "M.G.L. c.94G §7",
                       "https://malegislature.gov/Laws/GeneralLaws/PartI/TitleXV/Chapter94G/Section7"),
        "state_tax": F("Adult use: 10.75% cannabis excise plus the 6.25% sales tax, and a local "
                       "option tax of up to 3%. Medical sales are exempt.",
                       "M.G.L. c.64N §2 and §3; c.64H",
                       "https://malegislature.gov/Laws/GeneralLaws/PartI/TitleIX/Chapter64N/Section2"),
        "regulator": F("Cannabis Control Commission (CCC)", "M.G.L. c.94G, c.94I",
                       "https://masscannabiscontrol.com"),
    },
    "MI": {
        "possession": F("Adults 21+: 2.5 oz, of which no more than 15 g may be concentrate; up to "
                        "10 oz at home.", "MCL 333.27955(1)(a)-(b)", "https://www.michigan.gov/cra"),
        "home_grow": F("Up to 12 plants per residence, for personal use.", "MCL 333.27955(1)(b)",
                       "https://www.michigan.gov/cra"),
        "state_tax": F("Adult use: 10% retail excise, plus the 6% sales tax charged on the price "
                       "including the excise. From 1 Jan 2026, a 24% wholesale excise on adult-use "
                       "transfers to retailers. Medical: 6% sales tax only.",
                       "MCL 333.27963; Comprehensive Road Funding Tax Act (2025 PA 23)",
                       "https://www.michigan.gov/cra"),
        "regulator": F("Cannabis Regulatory Agency (CRA), Department of Licensing and Regulatory "
                       "Affairs", "MRTMA; MMFLA", "https://www.michigan.gov/cra"),
    },
    "MN": {
        "possession": F("Adults 21+: 2 oz of flower in public and 2 lb at home, 8 g of "
                        "concentrate, and edibles totalling 800 mg THC.",
                        "Minn. Stat. §342.09, subd. 1(a)", "https://www.revisor.mn.gov/statutes/cite/342.09"),
        "home_grow": F("8 plants per residence, no more than 4 mature, in an enclosed, locked space.",
                       "Minn. Stat. §342.09, subd. 2(a)", "https://www.revisor.mn.gov/statutes/cite/342.09"),
        "state_tax": F("Adult use: 15% cannabis gross receipts tax (10% before 1 July 2025), plus "
                       "the 6.875% state sales tax and any local sales tax. Medical sales to "
                       "registered patients are exempt from both.", "Minn. Stat. ch. 342; ch. 295",
                       "https://www.revenue.state.mn.us/guide/sales-7"),
        "regulator": F("Office of Cannabis Management (OCM)", "Minn. Stat. ch. 342",
                       "https://www.revisor.mn.gov/statutes/cite/342"),
    },
    "MS": {
        "possession": F("Residents with a registry card: 28 MMCEUs, and may buy 24 per 30 days "
                        "(1 MMCEU is 3.5 g of flower). Visiting cardholders: 14. For anyone else it is "
                        "not legal.", "Mississippi Medical Cannabis Act (SB 2095, 2022)", "https://www.mmcp.ms.gov/",
                        note="The penalty for a small amount without a card is not shown: the report reads "
                             "it only from a Justia copy of the Code."),
        "home_grow": NOT_CONFIRMED("The report's statement that home grow is not allowed rests only on a "
                                   "Justia copy of the Code (§41-137-39).", "Miss. Code §41-137-39"),
        "state_tax": F("5% excise on a cultivator's first sale of flower or trim, and the 7% "
                       "state sales tax on retail sales to cardholders.",
                       "Miss. Code §27-72-1(2)-(3)", "https://www.mmcp.ms.gov/"),
        "regulator": F("Mississippi State Department of Health, Medical Cannabis Program (MMCP); "
                       "the Department of Revenue licenses dispensaries.", "Miss. Code §41-137-1 et seq.",
                       "https://www.mmcp.ms.gov/"),
    },
    "MO": {
        "possession": F("Adults 21+: 3 oz of dried, unprocessed marijuana or its equivalent.",
                        "Mo. Const. art. XIV §2.10(1)(a)",
                        "https://revisor.mo.gov/main/OneSection.aspx?section=XIV%20Section%202&bid=51541"),
        "home_grow": F("With a cultivation registration card: 6 flowering plants, 6 non-flowering "
                       "plants and 6 clones.", "Mo. Const. art. XIV §2.10(1)(b)",
                       "https://revisor.mo.gov/main/OneSection.aspx?section=XIV%20Section%202&bid=51541"),
        "state_tax": F("Adult use: 6% state tax on retail sales, plus a local tax of up to 3%. "
                       "Medical: 4%.", "Mo. Const. art. XIV §1.4(1); art. XIV §2",
                       "https://dor.MO.gov/taxation/business/marijuana.html"),
        "regulator": F("Department of Health and Senior Services, Division of Cannabis "
                       "Regulation (DCR)", "Mo. Const. art. XIV; 19 CSR 100",
                       "https://health.mo.gov/business-professionals/cannabis-regulation"),
    },
    "MT": {
        "possession": F("Adults 21+: 1 oz of usable marijuana, including no more than 8 g of "
                        "concentrate and 800 mg THC in edibles.", "MCA §16-12-106(1)(a)",
                        "https://leg.mt.gov/bills/mca/title_0160/chapter_0120/"),
        "home_grow": F("Adults 21+: 2 mature plants and 2 seedlings each, no more than twice that "
                       "per residence. Medical cardholders: 4 mature and 4 seedlings.",
                       "MCA §16-12-106(1)(c)", "https://leg.mt.gov/bills/mca/title_0160/chapter_0120/"),
        "state_tax": F("20% on adult-use sales and 4% on medical sales, plus a local option tax "
                       "of up to 3% where voters adopt one.", "MCA §15-64-102",
                       "https://revenue.mt.gov/card/cannabis/cannabis-licenses/combined-use-licenses"),
        "regulator": F("Department of Revenue, Cannabis Control Division", "MCA Title 16, ch. 12",
                       "https://revenue.mt.gov/card/cannabis/cannabis-licenses/combined-use-licenses"),
    },
    "NE": {
        "possession": F("Qualified patients and caregivers: up to 5 oz. Not legal for anyone else.",
                        "Neb. Rev. Stat. §71-24,105",
                        "https://nebraskalegislature.gov/laws/statutes.php?statute=71-24,105",
                        note="No dispensary licence had been issued when the report was audited, so "
                             "there is no licensed place to buy."),
        "home_grow": F("Not allowed: neither the initiative nor the Commission's rules authorise "
                       "patient cultivation.", "Neb. Rev. Stat. §71-24,105",
                       "https://nebraskalegislature.gov/laws/statutes.php?statute=71-24,105"),
        "state_tax": F("None enacted: the medical cannabis statutes set no sales or excise tax.",
                       "Neb. Rev. Stat. §§71-24,103 to 71-24,111",
                       "https://www.nebraskalegislature.gov/laws/statutes.php?statute=71-24,111&print=true"),
        "regulator": F("Nebraska Medical Cannabis Commission (MCC)", "Neb. Rev. Stat. §71-24,109",
                       "https://mcc.nebraska.gov"),
    },
    "NV": {
        "possession": F("Adults 21+: 2.5 oz of cannabis and 1/4 oz of concentrate. Medical "
                        "patients: 2.5 oz.", "NRS 678D.200; NRS 678C.200",
                        "https://www.leg.state.nv.us/nrs/NRS-678D.html"),
        "home_grow": F("6 plants per adult, 12 per residence, enclosed and locked, but only if "
                       "the home is more than 25 miles from a licensed retail store.",
                       "NRS 678D.200; NRS 678D.310(1)", "https://www.leg.state.nv.us/nrs/NRS-678D.html"),
        "state_tax": F("15% excise on the first wholesale sale (medical and adult use), and a 10% "
                       "excise on adult-use retail sales, on top of state and local sales tax. Medical "
                       "sales to cardholders are exempt from the 10%.", "NRS 372A.290(1)-(3), (8)",
                       "https://www.leg.state.nv.us/NRS/NRS-372A.html", note=CHK),
        "regulator": F("Cannabis Compliance Board (CCB)", "NRS ch. 678A, 678B",
                       "https://ccb.nv.gov/faq/"),
    },
    "NH": {
        "possession": F("Registered patients: up to 2 oz of usable cannabis, buying no more than "
                        "2 oz in any 10 days. Not legal for anyone else; a small amount is a "
                        "violation, not a crime.", "RSA 126-X:2; RSA 126-X:8, XIII(b); RSA 318-B:2-c",
                        "https://gc.nh.gov/rsa/html/X/126-X/126-X-mrg.htm"),
        "home_grow": F("Not allowed, including for patients and caregivers.", "RSA 126-X:1, XIII",
                       "https://gc.nh.gov/rsa/html/X/126-X/126-X-mrg.htm"),
        "state_tax": F("None: New Hampshire has no sales tax and no cannabis tax.",
                       "New Hampshire Department of Revenue Administration",
                       "https://gc.nh.gov/rsa/html/X/126-X/126-X-mrg.htm"),
        "regulator": F("Department of Health and Human Services, Therapeutic Cannabis Program (TCP)",
                       "RSA 126-X", "https://www.dhhs.nh.gov/tcp"),
    },
    "NJ": {
        "possession": F("Adults 21+: up to 6 oz. A single purchase is capped at 1 oz of flower, "
                        "4 g of concentrate or 1,000 mg of edibles.", "CREAMM Act, P.L.2021, c.16",
                        "https://www.nj.gov/cannabis/adult-personal/index.shtml"),
        "home_grow": F("Not allowed, for adults or for patients and caregivers.",
                       "Cannabis Regulatory Commission", "https://www.nj.gov/cannabis/medicinalcannabis/"),
        "state_tax": F("Adult use: the 6.625% sales tax, a Social Equity Excise Fee ($2.50 per oz "
                       "from 1 Jan 2026), and a municipal transfer tax of up to 2% where adopted. "
                       "Medical patients pay no sales tax and no fee.", "CREAMM Act, P.L.2021, c.16",
                       "https://www.nj.gov/treasury/taxation/"),
        "regulator": F("Cannabis Regulatory Commission (CRC)", "CREAMM Act, P.L.2021, c.16",
                       "https://www.nj.gov/cannabis/"),
    },
    "NM": {
        "possession": F("Adults 21+, outside the home: 2 oz of cannabis, 16 g of concentrate and "
                        "800 mg of edibles. At home, no weight limit if kept out of public view.",
                        "NMSA §26-2C-25(A)(2)", NM_PDF, note=NM_NOTE),
        "home_grow": F("6 mature and 6 immature plants per adult; no more than 12 mature plants "
                       "per household.", "NMSA §26-2C-25(A)(9)", NM_PDF, note=NM_NOTE),
        "state_tax": F("Cannabis excise: 12% until 1 July 2025, then rising gradually to 18% from "
                       "1 July 2030. Medical sales to patients are exempt.",
                       "NMSA §7-42-3", "https://www.rld.nm.gov/cannabis/compliance/tax-reporting/",
                       note="The rate for each year in between is set in §7-42-3, which is not yet checked "
                            "in official text. " + CHK),
        "regulator": F("Regulation and Licensing Department, Cannabis Control Division (CCD); the "
                       "Department of Health runs the medical programme.", "Cannabis Regulation Act",
                       "https://www.rld.nm.gov/cannabis/"),
    },
    "NY": {
        "possession": F("Adults 21+: 3 oz of cannabis and 24 g of concentrate; up to 5 lb at home.",
                        "Penal Law §222.05", "https://www.nysenate.gov/legislation/laws/PEN/222.05"),
        "home_grow": F("3 mature and 3 immature plants per adult; no more than 6 and 6 per residence.",
                       "Penal Law §222.15", "https://www.nysenate.gov/legislation/laws/PEN/222.15"),
        "state_tax": F("Adult use: 13% at retail (9% state and 4% local), plus a 9% distributor "
                       "tax on sales to retailers. Adult-use products are exempt from sales tax.",
                       "Tax Law art. 20-C", "https://www.tax.ny.gov/bus/auc/"),
        "regulator": F("Office of Cannabis Management (OCM) and the Cannabis Control Board",
                       "Cannabis Law (MRTA)", "https://cannabis.ny.gov"),
    },
    "NC": {
        "possession": F("Not legal in any amount under state law.", "N.C.G.S. 90-95(a); 90-94",
                        "https://ncleg.gov/EnactedLegislation/SessionLaws/HTML/2021-2022/SL2022-32.html",
                        note="On Eastern Band of Cherokee trust land, tribal law governs instead."),
        "home_grow": F("Not allowed: no statute authorises it, and growing is charged as manufacture.",
                       "N.C.G.S. 90-95(a)",
                       "https://ncleg.gov/EnactedLegislation/SessionLaws/HTML/2021-2022/SL2022-32.html"),
        "state_tax": F("None: there is no legal marijuana sale to tax.", "N.C.G.S. ch. 105",
                       "https://ncleg.gov/EnactedLegislation/SessionLaws/HTML/2021-2022/SL2022-32.html"),
        "regulator": F("No cannabis regulator. Hemp: Department of Agriculture and Consumer Services.",
                       "N.C.G.S. 90-87(16)", "https://www.ncagr.gov/divisions/plant-industry/hemp-nc"),
    },
    "ND": {
        "possession": F("Registered patients: up to 3 oz of flower and 500 mg of edibles at any "
                        "time, buying no more than 2.5 oz of flower per 30 days (6 oz with an "
                        "enhanced card). Not legal for anyone else.", "NDCC ch. 19-24.1",
                        "https://www.legis.nd.gov/cencode/t19c24-1.pdf"),
        "home_grow": F("Not allowed, including for patients.", "NDCC ch. 19-24.1 (SB 2344, 2017)",
                       "https://www.legis.nd.gov/cencode/t19c24-1.pdf"),
        "state_tax": F("No cannabis-specific tax. Medical marijuana pays the 5% state sales tax "
                       "plus any local sales tax.", "NDCC ch. 57-39.2", "https://www.tax.nd.gov"),
        "regulator": F("Department of Health and Human Services, Division of Medical Marijuana",
                       "NDCC ch. 19-24.1", "https://www.hhs.nd.gov/mm"),
    },
    "OH": {
        "possession": F("Adults 21+: 2.5 oz of plant material and 15 g of extract, counting "
                        "home-grown and purchased cannabis together.", "ORC 3796.221 (SB 56, eff. 20 Mar 2026)",
                        "https://codes.ohio.gov/ohio-revised-code/section-3796.221"),
        "home_grow": F("6 plants per adult, 12 per residence, at a primary residence, secured "
                       "and not visible from a public space.", "ORC 3796.04",
                       "https://codes.ohio.gov/ohio-revised-code/chapter-3796"),
        "state_tax": F("10% excise on adult-use sales, paid by the buyer. Medical sales are exempt "
                       "from it.", "ORC 3796.40(B)-(C)",
                       "https://codes.ohio.gov/ohio-revised-code/section-3796.40"),
        "regulator": F("Department of Commerce, Division of Cannabis Control (DCC)", "ORC ch. 3796",
                       "https://com.ohio.gov/cannabis"),
    },
    "OK": {
        "possession": F("Licensed patients: 3 oz on their person and 8 oz at home. Adult use is "
                        "not legal.", "63 O.S. §420(A) (State Question 788)",
                        "https://www.oklegislature.gov/cf_pdf/2019-20%20SUPPORT%20DOCUMENTS/BILLSUM/House/HB2612%20FULLPCS1%20BILLSUM.PDF",
                        note="Someone without a licence who states a medical condition and holds up to "
                             "1.5 oz faces a fine of up to $400, not jail (63 O.S. §420(B))."),
        "home_grow": F("Licensed patients: 6 mature plants and 6 seedlings.", "63 O.S. §420(A)",
                       "https://www.oklegislature.gov/cf_pdf/2019-20%20SUPPORT%20DOCUMENTS/BILLSUM/House/HB2612%20FULLPCS1%20BILLSUM.PDF"),
        "state_tax": F("7% excise on retail medical marijuana sales, collected at the point of sale.",
                       "63 O.S. §426", "https://oklahoma.gov/omma/"),
        "regulator": F("Oklahoma Medical Marijuana Authority (OMMA)", "63 O.S. §427.3",
                       "https://oklahoma.gov/omma/"),
    },
    "OR": {
        "possession": F("Adults 21+: 2 oz in public and 8 oz in total, plus 16 oz of solid "
                        "products, 72 oz of liquid products and 1 oz of extracts bought from a "
                        "retailer.", "ORS 475C.337",
                        "https://www.oregonlegislature.gov/bills_laws/ors/ors475C.html"),
        "home_grow": F("4 plants per household, not per person, out of public view.",
                       "ORS 475C.305(1), 475C.306",
                       "https://www.oregonlegislature.gov/bills_laws/ors/ors475C.html"),
        "state_tax": F("17% state retail tax on adult-use sales, plus a local tax of up to 3% where "
                       "voters approve one. Medical sales are exempt until 1 Jan 2028 unless extended.",
                       "ORS 475C.674", "https://www.oregonlegislature.gov/bills_laws/ors/ors475C.html"),
        "regulator": F("Oregon Liquor and Cannabis Commission (OLCC) for adult use; the Oregon "
                       "Health Authority runs the medical programme.", "ORS ch. 475C",
                       "https://www.oregonlegislature.gov/bills_laws/ors/ors475C.html"),
    },
    "PA": {
        "possession": F("Certified patients only: no weight limit, but no more than a 90-day "
                        "supply, kept in its original package. Not legal for anyone else.",
                        "Medical Marijuana Act (Act 16 of 2016) §§303, 405",
                        "https://www.legis.state.pa.us/WU01/LI/LI/US/HTM/2016/0/0016..HTM"),
        "home_grow": F("Not allowed: only permitted grower/processors may grow.",
                       "Act 16 of 2016 §304(3)",
                       "https://www.legis.state.pa.us/WU01/LI/LI/US/HTM/2016/0/0016..HTM"),
        "state_tax": F("5% gross receipts tax on grower/processors' sales to dispensaries; it may "
                       "not be added as a separate line on the dispensary's charge.",
                       "Act 16 of 2016 §901 (35 P.S. §10231.901)",
                       "https://www.pa.gov/agencies/revenue/resources/tax-types-and-information/medical-marijuana-tax.html"),
        "regulator": F("Department of Health, Office of Medical Marijuana", "Act 16 of 2016",
                       "https://www.pa.gov/agencies/health/programs/medical-marijuana/growers-processors"),
    },
    "RI": {
        "possession": F("Adults 21+: 1 oz, or the equivalent in concentrate; up to 10 oz per "
                        "resident at home.", "R.I. Gen. Laws §21-28.11-22",
                        "https://webserver.rilegislature.gov/Statutes/TITLE21/21-28.11/21-28.11-22.htm"),
        "home_grow": F("3 mature and 3 immature plants per dwelling, however many adults live there.",
                       "R.I. Gen. Laws §21-28.11-22",
                       "https://webserver.rilegislature.gov/Statutes/TITLE21/21-28.11/21-28.11-22.htm"),
        "state_tax": F("Adult use: 7% sales tax, 10% state cannabis excise and 3% local excise.",
                       "R.I. Gen. Laws §21-28.11-13",
                       "http://webserver.rilegislature.gov/Statutes/TITLE21/21-28.11/21-28.11-13.htm"),
        "regulator": F("Cannabis Control Commission (CCC)", "R.I. Gen. Laws §21-28.11-4",
                       "https://ccc.ri.gov/about-ccc"),
    },
    "SC": {
        "possession": F("Not legal. Simple possession of 1 oz (28 g) or less is a misdemeanor; "
                        "more is presumed to be distribution.", "S.C. Code §44-53-370(d)(5)",
                        "https://www.scstatehouse.gov/code/t44c053.php"),
        "home_grow": F("Not allowed: growing is charged as manufacture.", "S.C. Code §44-53-370",
                       "https://www.scstatehouse.gov/code/t44c053.php"),
        "state_tax": F("None: there is no legal marijuana sale to tax.", "S.C. Code §12-36-910",
                       "https://dor.sc.gov/"),
        "regulator": F("No cannabis regulator. Hemp: South Carolina Department of Agriculture.",
                       "S.C. Code §46-55-10 et seq.", "https://agriculture.sc.gov/hemp/"),
    },
    "SD": {
        "possession": F("Registered patients and confirmed nonresident cardholders, up to the "
                        "allowable amount the medical cannabis law sets. Not legal for anyone else: "
                        "2 oz or less is a Class 1 misdemeanor.", "SDCL ch. 34-20G; SDCL §22-42-6",
                        "http://sdlegislature.gov/api/Statutes/34-20G.html"),
        "home_grow": F("Patients whose card allows it: 2 flowering and 2 non-flowering plants, "
                       "in an enclosed, locked facility. Not allowed for anyone else.",
                       "SDCL ch. 34-20G", "http://sdlegislature.gov/api/Statutes/34-20G.html"),
        "state_tax": F("Medical cannabis pays the state sales tax: 4.2% in 2026, returning to 4.5% "
                       "on 1 July 2027, plus any municipal tax.", "SDCL §10-45-2",
                       "https://sdlegislature.gov/Statutes/10-45-2"),
        "regulator": F("Department of Health, Medical Cannabis Program", "SDCL ch. 34-20G; ARSD art. 44:90",
                       "http://sdlegislature.gov/api/Statutes/34-20G.html"),
    },
    "TN": {
        "possession": F("Not legal in any amount, apart from a narrow exclusion for low-THC oil.",
                        "Tenn. Code §39-17-418; §39-17-402(16)", "",
                        note="The audited report cites the Tennessee Code, but no official link for it "
                             "was captured."),
        "home_grow": F("Not allowed: there is no legal way to grow marijuana.",
                       "Tenn. Code §39-17-402(16)", "",
                       note="The audited report cites the Tennessee Code, but no official link for it "
                            "was captured."),
        "state_tax": F("No marijuana tax: there is no legal sale to tax. Hemp-derived cannabinoid "
                       "products carry their own taxes.", "Tenn. Code §67-6-232",
                       "https://revenue.support.tn.gov/hc/en-us/articles/360058231712-SUT-112-Hemp-Tennessee-Tax-Implications"),
        "regulator": F("No cannabis regulator. Hemp products: Tennessee Alcoholic Beverage "
                       "Commission; hemp growing: Department of Agriculture.", "Tenn. Code Title 57, ch. 7",
                       "https://www.tn.gov/agriculture/farms/hemp-industry.html"),
    },
    "TX": {
        "possession": F("Registered TCUP patients only: low-THC cannabis as prescribed. For anyone "
                        "else, 2 oz or less is a Class B misdemeanor.",
                        "Health & Safety Code ch. 487; §481.121(b)(1)",
                        "https://www.dps.texas.gov/section/compassionate-use-program"),
        "home_grow": F("Not allowed, including for patients.", "Health & Safety Code ch. 487",
                       "https://www.dps.texas.gov/section/compassionate-use-program"),
        "state_tax": NOT_CONFIRMED("The audit found no cannabis-specific tax, but the sales-tax treatment of "
                                   "TCUP sales rests on secondary guides; no Comptroller ruling was found.",
                                   "Tax Code ch. 151", "https://comptroller.texas.gov/taxes/sales/"),
        "regulator": F("Department of Public Safety, Compassionate Use Program. Consumable hemp: "
                       "Department of State Health Services.", "Health & Safety Code ch. 487",
                       "https://www.dps.texas.gov/section/compassionate-use-program"),
    },
    "UT": {
        "possession": F("Card holders: no more than a 30-day supply, capped at 113 g of "
                        "unprocessed cannabis and 20 g of THC in other forms. Not legal for "
                        "anyone else.", "Utah Code §26B-4-201; §4-41a-1102",
                        "https://le.utah.gov/xcode/Title26B/Chapter4/C26B-4-S203_2025070120250507.pdf"),
        "home_grow": F("Not allowed, for anyone.", "Utah Code §58-37-8", "https://medicalcannabis.utah.gov/"),
        "state_tax": NOT_CONFIRMED("The report records a sales-tax exemption for medical cannabis in dosage form "
                                   "from a secondary summary only, with the statute text still to be checked.",
                                   "Utah Code §59-12-104.10"),
        "regulator": F("Department of Agriculture and Food (UDAF), Specialized Products Division, "
                       "which took over the full medical programme under HB 389 and SB 121 (2026).",
                       "Utah Code §4-41a-103", "https://ag.utah.gov/"),
    },
    "VT": {
        "possession": F("Adults 21+: 2 oz of cannabis or 10 g of hashish (doubled on 1 July 2026). "
                        "Home-grown cannabis stored where it was grown does not count.",
                        "18 V.S.A. §4230a(a)(1) as amended by Act 176 (2026)",
                        "http://legislature.vermont.gov/statutes/section/18/084/04230a"),
        "home_grow": F("2 mature and 4 immature plants per dwelling, however many adults live there.",
                       "18 V.S.A. §4230e", "http://legislature.vermont.gov/statutes/section/18/084/04230a"),
        "state_tax": F("14% cannabis excise on retail sales, paid by the buyer, plus the 6% sales "
                       "tax and a 1% local option tax where adopted.", "32 V.S.A. §7902",
                       "https://legislature.vermont.gov/statutes/section/32/207/07902"),
        "regulator": F("Cannabis Control Board (CCB)", "7 V.S.A. ch. 31", "https://ccb.vermont.gov"),
    },
    "VA": {
        "possession": F("Adults 21+: 2 oz in public (since 1 July 2026). More is a civil fine up to "
                        "4 oz, and a crime above that.", "Va. Code §4.1-1100(A)",
                        "https://law.lis.virginia.gov/vacode/4.1-1100/"),
        "home_grow": F("4 plants per household, at the main residence, out of public view and "
                       "tagged.", "Va. Code §4.1-1101", "http://law.lis.virginia.gov/vacode/4.1-1101/"),
        "state_tax": NOT_CONFIRMED("There is no adult-use sale to tax until retail opens on 1 July 2027, and "
                                   "the audit records the sales-tax treatment of medical cannabis as "
                                   "unresolved: an official meeting summary and secondary guides disagree."),
        "regulator": F("Virginia Cannabis Control Authority (CCA)", "Va. Code Title 4.1, ch. 6",
                       "https://cca.virginia.gov/"),
    },
    "WA": {
        "possession": F("Adults 21+: 1 oz of flower, 7 g of concentrate, 16 oz of solid infused "
                        "products and 72 oz of liquid. These are also the most a store may sell in "
                        "one transaction.", "RCW 69.50.360", "https://app.leg.wa.gov/rcW/default.aspx?cite=69.50"),
        "home_grow": F("Not allowed without a medical authorisation.", "RCW 69.51A",
                       "https://app.leg.wa.gov/RCW/default.aspx?cite=69.51A"),
        "state_tax": F("37% cannabis excise on retail sales, plus sales tax charged on the price "
                       "before the excise. Qualifying medical sales are exempt from the excise.",
                       "RCW 69.50.535", "https://app.leg.wa.gov/RCW/default.aspx?cite=69.50.535"),
        "regulator": F("Washington State Liquor and Cannabis Board (LCB)", "RCW 69.50",
                       "https://lcb.wa.gov/se/history"),
    },
    "WV": {
        "possession": F("Certified patients with an ID card: no more than a 30-day supply. Not "
                        "legal for anyone else.", "W. Va. Code §16A-8-1(d); §16A-3-2",
                        "https://code.wvlegislature.gov/16A-3/"),
        "home_grow": F("Not allowed, including for patients.", "W. Va. Code ch. 16A",
                       "https://code.wvlegislature.gov/16A-3/"),
        "state_tax": F("10% privilege tax on dispensaries' gross receipts, not shown as a separate "
                       "line to the patient.", "W. Va. Code §16A-9-1",
                       "https://code.wvlegislature.gov/16A-9-1/"),
        "regulator": F("Office of Medical Cannabis (OMC)", "W. Va. Code ch. 16A", "https://omc.wv.gov"),
    },
    "WI": {
        "possession": F("Not legal in any amount. A first offence carries a fine of up to $1,000 "
                        "and up to 6 months in jail; a second is a felony.", "Wis. Stat. §961.41(3g)(e)",
                        "https://docs.legis.wisconsin.gov/document/acts/2019/68,54n"),
        "home_grow": F("Not allowed.", "Wis. Stat. §961.41(1)",
                       "https://docs.legis.wisconsin.gov/document/acts/2019/68,54n"),
        "state_tax": F("None: there is no legal marijuana sale to tax.", "Wis. Stat. ch. 77",
                       "https://www.revenue.wi.gov/"),
        "regulator": F("No cannabis regulator: Wisconsin has no medical or adult-use programme.",
                       "Wis. Stat. ch. 961", "https://hemp.wi.gov/"),
    },
    "WY": {
        "possession": F("Not legal in any amount.", "W.S. 35-7-1031(c)", "",
                        note="The audited report cites the Wyoming statutes, but no official link for "
                             "them was captured. The penalty tiers are not shown: the report reads them "
                             "only from a FindLaw copy."),
        "home_grow": F("Not allowed.", "W.S. 35-7-1031", "",
                       note="The audited report cites the Wyoming statutes, but no official link for "
                            "them was captured."),
        "state_tax": F("None: there is no legal marijuana sale to tax.", "W.S. 35-7-1001 et seq.", "",
                       note="The audited report cites the Wyoming statutes, but no official link for "
                            "them was captured."),
        "regulator": F("No cannabis regulator. Hemp: Wyoming Department of Agriculture.",
                       "W.S. 35-7-2101 et seq.",
                       "https://agriculture.wy.gov/divisions/wsf/index.php?section=hemp-program"),
    },
    "AL": {
        "possession": F("Registered patients and caregivers only, in the permitted non-smokable "
                        "forms, bought from a licensed dispensary. Not legal for anyone else.",
                        "Ala. Code §20-2A-1 et seq. (Act 2021-450)",
                        "https://alison.legislature.state.al.us/files/pdf/SearchableInstruments/2021RS/PrintFiles/213097-2.pdf",
                        note="The dose-based purchase and possession caps are not yet confirmed against "
                             "the official Code, so they are not shown."),
        "home_grow": F("Not allowed, including for patients.", "Ala. Code §20-2A-3(16)",
                       "https://alison.legislature.state.al.us/files/pdf/SearchableInstruments/2021RS/PrintFiles/213097-2.pdf"),
        "state_tax": F("9% tax on the gross proceeds of retail medical cannabis sales, on top of "
                       "all other taxes.", "Ala. Code §20-2A-80(a)",
                       "https://alison.legislature.state.al.us/files/pdf/SearchableInstruments/2021RS/PrintFiles/213097-2.pdf"),
        "regulator": F("Alabama Medical Cannabis Commission (AMCC)", "Ala. Code §20-2A-1 et seq.",
                       "https://amcc.alabama.gov/"),
    },
}


# Two further law topics for the Laws tab, added 20 Nov 2026 on the same terms:
# where consumption is allowed, and what protection employees have. Merged into
# QUICK so every check in build_quick_reference.py applies to them too.
LAW_MORE = {
    "ID": {
        "public_use": F("Not legal anywhere: possession itself is the offence.", "Idaho Code §37-2732(c)(3)",
                        "https://legislature.idaho.gov/statutesrules/idstat/title37/t37ch27/sect37-2732/"),
        "employment": F("None: there is no medical or adult-use programme, so no use is protected.",
                        "Idaho Code §37-2701",
                        "https://legislature.idaho.gov/statutesrules/idstat/Title37/T37CH27/SECT37-2701"),
    },
    "AL": {
        "public_use": NOT_CONFIRMED("The Act's limits on where patients may use medical cannabis are quoted "
                                    "in the report from a mirror of the Code, still to be checked against "
                                    "the official text.", "Ala. Code §20-2A-1 et seq."),
        "employment": NOT_CONFIRMED("The report finds essentially no employment protection, but quotes the "
                                    "governing section (§20-2A-6) from a mirror of the Code, still to be "
                                    "checked against the official text.", "Ala. Code §20-2A-6"),
    },
    "AK": {
        "public_use": F("Not in public. Public consumption is a violation with a fine of up to $100.",
                        "AS 17.38.020(4); AS 17.38.040", "https://www.akleg.gov/"),
        "employment": F("No protection, for medical patients either: employers need not permit or "
                        "accommodate use, and may keep and enforce drug-free workplace policies.",
                        "AS 17.38.220(a)", "https://www.akleg.gov/"),
    },
    "AZ": {
        "public_use": F("Smoking marijuana in a public place or open space is a petty offence.",
                        "A.R.S. §36-2853(C)",
                        "https://www.azleg.gov/viewdocument/?docName=https://www.azleg.gov/ars/36/02853.htm"),
        "employment": NOT_CONFIRMED("Registered patients have a qualified protection against discrimination, "
                                    "but the report quotes it from a secondary source, still to be checked "
                                    "against the official statute.", "A.R.S. §36-2813"),
    },
    "AR": {
        "public_use": F("Patients may not use medical marijuana in a public place, on public transport "
                        "or a school bus, on the grounds of a school, college or daycare, at a drug or "
                        "alcohol treatment facility or community centre, in a correctional facility, or "
                        "on military property; and may not smoke it inside a vehicle or wherever smoking "
                        "tobacco is banned.", "Ark. Const. amend. 98 §6(a)(2), (a)(4)",
                        "https://www.dfa.arkansas.gov/wp-content/uploads/Medical_Marijuana_Rules_1.pdf"),
        "employment": F("An employer may not discriminate in hiring, firing or the terms of employment "
                        "based on an applicant's or employee's status as a qualifying patient.",
                        "Ark. Const. Amendment 98 §6(f)",
                        "https://www.dfa.arkansas.gov/wp-content/uploads/Medical_Marijuana_Rules_1.pdf",
                        note="The amendment sets exceptions to this protection; see its full text."),
    },
    "CA": {
        "public_use": F("Not in a public place, by smoking or by eating, except at an on-site consumption "
                        "business the city or county has authorised.", "HSC §11362.3; BPC §26200",
                        "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=HSC&sectionNum=11362.1"),
        "employment": F("Since 1 Jan 2024 employers may not discriminate based on cannabis use off the job "
                        "and away from the workplace, or on a drug test that finds only non-psychoactive "
                        "metabolites.", "Gov. Code §12954 (AB 2188, SB 700)",
                        "https://www.cannabis.ca.gov/cannabis-laws/",
                        note="The statute has exceptions; see its full text."),
    },
    "CO": {
        "public_use": F("Illegal in public, including openly and publicly. Allowed on private property "
                        "with the owner's permission, or at a licensed hospitality business where the "
                        "town has opted in.", "Colo. Const. art. XVIII §16(3)(d)", "https://med.colorado.gov/"),
        "employment": NOT_CONFIRMED("The constitution preserves employers' policies (art. XVIII §16(6)), but the "
                                    "report could quote the exact wording only from a reproduction, still to be "
                                    "checked against the official text.", "Colo. Const. art. XVIII §16(6)"),
    },
    "CT": {
        "public_use": F("Smoking or vaping cannabis is banned wherever tobacco smoking is banned. Medical "
                        "patients may not use it in any public place.", "Conn. Gen. Stat. §§19a-342, 19a-342a; 21a-408a",
                        "https://cga.ct.gov/current/pub/chap_420f.htm"),
        "employment": F("A positive test only for the THC metabolite is not, without other evidence, proof "
                        "of impairment. Further limits on acting against employees for off-duty use apply, "
                        "except at \"exempted employers\" in listed industries such as utilities, "
                        "construction, manufacturing and transport.", "Conn. Gen. Stat. §§21a-422, 21a-422o to 21a-422s",
                        "https://www.cga.ct.gov/current/pub/chap_420h.htm"),
    },
    "DE": {
        "public_use": F("Public consumption is prohibited.", "Office of the Marijuana Commissioner FAQ",
                        "https://omc.delaware.gov/faq/"),
        "employment": F("Adult use: no protection; the law places no requirement on employers' "
                        "accommodation, policies or discipline. Registered medical patients may not be "
                        "penalised for being a cardholder or for a positive test, unless they used, "
                        "possessed or were impaired at work.", "4 Del.C. §1304; 16 Del.C. §4905A(a)(3)",
                        "https://delcode.delaware.gov/title4/c013/sc01/index.html", note=CHK),
    },
    "DC": {
        "public_use": F("Not in public: not on streets, alleys, sidewalks, parks or parking areas, in "
                        "vehicles there, or anywhere the public is invited.", "D.C. Code §48-911.01",
                        "https://oag.dc.gov/release/office-attorney-general-releases-frequently-asked"),
        "employment": F("Employers may not take adverse action for cannabis use, medical patient status, "
                        "or a test showing only metabolites without other signs of impairment. "
                        "Exceptions: safety-sensitive jobs, federal requirements, and use or impairment at work.",
                        "D.C. Law 24-190", "https://code.dccouncil.gov/us/dc/council/laws/24-190"),
    },
    "FL": {
        "public_use": F("Patients may not use it in a public place or on public transport (low-THC "
                        "cannabis not smoked is the exception), nor in a school bus, vehicle, aircraft "
                        "or motorboat, at work, in prisons or on school grounds.",
                        "Fla. Stat. §381.986(1)(k)5.",
                        "https://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0300-0399/0381/Sections/0381.986.html"),
        "employment": F("No protection: the law does not limit drug-free workplace programmes and does "
                        "not require any employer to accommodate medical use.", "Fla. Stat. §381.986(15)",
                        "https://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0300-0399/0381/Sections/0381.986.html"),
    },
    "GA": {
        "public_use": F("Vaping or otherwise heating medical cannabis in a public place is prohibited.",
                        "O.C.G.A. §16-12-234(a)(3)", "https://dph.georgia.gov/low-thc-oil-registry/patients-and-caregivers",
                        note="That section does not ban every form of public use; it targets vapour-producing devices."),
        "employment": NOT_CONFIRMED("The report finds no employment protection (§16-12-191(e)), but that "
                                    "reading rests only on a Justia copy of the Code; the report lists the "
                                    "live legis.ga.gov text as still unverified.", "O.C.G.A. §16-12-191(e)"),
    },
    "HI": {
        "public_use": F("Patients may not smoke or vape in public, in a vehicle, at work, on school "
                        "grounds, at parks, beaches or recreation centres, or anywhere open to the public. "
                        "Use by anyone else is not legal.", "HRS §329-122(e); HRS ch. 328J",
                        "https://health.hawaii.gov/medicalcannabisregistry/general-information/marijuana-laws-and-related-documents/"),
        "employment": NOT_CONFIRMED("The patient protections in §329-125.5 are quoted in the report from bill "
                                    "reproductions and secondary summaries, still to be checked against the "
                                    "current statute.", "HRS §329-125.5"),
    },
    "IL": {
        "public_use": F("Not in any public place, and the Smoke Free Illinois Act applies; private "
                        "businesses may ban it. A licensed consumption lounge does not count as a public place.",
                        "410 ILCS 705/10-35; 705/55-25(3)",
                        "https://ilga.gov/legislation/ILCS/details?ActID=3992&ActName=Cannabis+Regulation+and+Tax+Act."),
        "employment": F("Employers may adopt and enforce reasonable zero-tolerance or drug-free workplace "
                        "policies, including drug testing and rules on use at work, and may discipline "
                        "employees who break them.", "410 ILCS 705/10-50",
                        "https://ilga.gov/legislation/ILCS/details?ActID=3992&ActName=Cannabis+Regulation+and+Tax+Act."),
    },
    "IN": {
        "public_use": F("Not legal anywhere: possession itself is the offence.", "IC 35-48-4-11",
                        "https://public.courts.in.gov/Decisions/api/Document/Opinion?Id=DmYIl2h3bOKWWdQQvJyPZ_rjZgo14Y_LmDtP2-HSBr7Uf3wsJD127SUP1Lq0Mzh20"),
        "employment": F("None: there is no medical programme to protect, and no cannabis-specific "
                        "employment or drug-testing protection was found.", "IC 35-48",
                        "https://www.in.gov/dor/i-am-a/business-corp/business-faq/"),
    },
    "IA": {
        "public_use": F("For anyone but a patient, use is unlawful anywhere. Dispensaries and "
                        "manufacturers may not let anyone consume medical cannabidiol on their property.",
                        "Iowa Code §§124E.7(5), 124E.9(5); §124.401(5)", IA_URL, note=CHK),
        "employment": F("No protection: employers need not allow use or possession at work, and may "
                        "enforce zero-tolerance policies with drug testing.", "Iowa Code §124E.21; §730.5",
                        "https://www.legis.iowa.gov/docs/code/2024/124E.pdf"),
    },
    "KS": {
        "public_use": F("Not legal anywhere: possession itself is the offence.", "K.S.A. 21-5706",
                        "https://kslegislature.gov/li_2022/b2021_22/statute/065_000_0000_chapter/065_041_0000_article/065_041_0001_section/065_041_0001_k/"),
        "employment": F("None: there is no medical programme to protect, and no general private-employer "
                        "drug-testing statute was found.", "K.S.A. 44-1009",
                        "https://kslegislature.gov/li_2022/b2021_22/statute/065_000_0000_chapter/065_041_0000_article/065_041_0001_section/065_041_0001_k/"),
    },
    "KY": {
        "public_use": F("Smoking raw plant material is prohibited even for patients, and vaping is banned "
                        "on public transport, in public places and in places of public accommodation.",
                        "KRS 218B.035(1)(g)-(h), (3)(a)",
                        "https://apps.legislature.ky.gov/law/acts/24RS/documents/0195.pdf"),
        "employment": F("Narrow: for drug testing that state or local law requires, a registered patient "
                        "is treated as if prescribed a pharmaceutical drug. There is no general right to "
                        "use at work or to test positive.", "KRS 218B.045(1)",
                        "https://apps.legislature.ky.gov/law/statutes/statute.aspx?id=55795"),
    },
    "LA": {
        "public_use": F("Smoking or vaping in a vehicle is banned, with a $100 fine. No general statute "
                        "banning public consumption by patients was found.", "La. R.S. 32:300.4.1",
                        "https://www.legis.la.gov/Legis/Law.aspx?p=y&d=96986"),
        "employment": F("State employers only: they may not penalise an employee or applicant solely for a "
                        "positive marijuana test if a physician has recommended it for a diagnosed "
                        "debilitating condition. No private-employer protection was found.",
                        "La. R.S. 49:1016 (Act 651 of 2022)", "https://www.legis.la.gov/Legis/Law.aspx?p=y&d=96986"),
    },
    "ME": {
        "public_use": F("Only in a private residence (including its grounds), or on private property not "
                        "generally open to the public with the owner's explicit permission.",
                        "28-B MRS §1501(2)", "https://legislature.maine.gov/statutes/28-B/title28-Bch1.pdf"),
        "employment": F("Employers may not penalise or refuse to hire someone solely for off-duty, "
                        "off-premises use. They may prohibit use, possession and impairment at work, and "
                        "safety-sensitive and federally mandated roles are exempt.",
                        "28-B MRS §112; 26 MRS §681(8)", "https://legislature.maine.gov/statutes/28-B/title28-Bch1.pdf"),
    },
    "MD": {
        "public_use": F("Public consumption is unlawful, except at a licensed on-site consumption business.",
                        "Alc. Bev. & Cann. Title 36", "https://cannabis.maryland.gov/pages/cannabisfaq.aspx"),
        "employment": NOT_CONFIRMED("The report finds no general off-duty protection, but its account of the "
                                    "employer section (§36-1301) is a secondary summary still to be checked "
                                    "against the statute.", "Md. Alc. Bev. & Cann. §36-1301"),
    },
    "MA": {
        "public_use": F("Public consumption is a civil offence with a fine of up to $100; an open container "
                        "in a vehicle's passenger area, up to $500.", "M.G.L. c.94G §13(c)-(d)",
                        "https://malegislature.gov/Laws/GeneralLaws/PartI/TitleXV/Chapter94G"),
        "employment": F("No general protection for off-duty adult use was found. Employers may have their "
                        "own policies on marijuana use.", "M.G.L. c.94G; Cannabis Control Commission",
                        "https://masscannabiscontrol.com/know-the-laws/"),
    },
    "MI": {
        "public_use": F("Not in public, and not in a vehicle's passenger area on a public road.",
                        "MCL 333.27954(1)(a), (e)", "https://www.michigan.gov/cra"),
        "employment": F("Little protection: no statute stops a private employer from testing for "
                        "marihuana or requires it to accommodate off-duty use, and the act preserves "
                        "employers' policies.", "MCL 333.27954(3)", "https://www.michigan.gov/cra"),
    },
    "MN": {
        "public_use": F("Not in public, not in a vehicle and not at schools; no smoking or vaping where "
                        "smoking is banned.", "Minn. Stat. §342.09, subd. 1",
                        "https://www.revisor.mn.gov/statutes/cite/342.09"),
        "employment": F("Off-duty, off-premises use is protected in hiring, discipline and firing. Use, "
                        "possession or impairment at work, in working hours or with the employer's "
                        "vehicles or equipment is not.", "Minn. Stat. §181.951",
                        "https://www.revisor.mn.gov/statutes/cite/342"),
    },
    "MS": {
        "public_use": NOT_CONFIRMED("The report's reading of the public-use rules (§41-137-13(2), "
                                    "§41-137-3(gg)) rests only on a Justia copy of the Code; the report "
                                    "says every §41-137 quotation does, unless an official bill text "
                                    "corroborates it.", "Miss. Code §41-137-13(2)"),
        "employment": NOT_CONFIRMED("The report finds no employment protection (§41-137-13(1)(b)-(f)), "
                                    "but reads it only from Justia and FindLaw copies of the Code.",
                                    "Miss. Code §41-137-13(1)"),
    },
    "MO": {
        "public_use": F("The constitution does not allow public use; smoking in public draws a civil fine.",
                        "Mo. Const. art. XIV §2.1",
                        "https://revisor.mo.gov/main/OneSection.aspx?section=XIV%20Section%202&bid=51541"),
        "employment": NOT_CONFIRMED("Medical patients have a limited protection (art. XIV §1.7), but the report "
                                    "takes its text from secondary sources, still to be checked against the "
                                    "Revisor's official text.", "Mo. Const. art. XIV §1"),
    },
    "MT": {
        "public_use": F("Not in public: smoking in public carries a civil fine of up to $50. Not on public "
                        "transport, on school, health-care or correctional grounds, or where tobacco smoking "
                        "is banned.", "MCA §16-12-106(4); §16-12-108",
                        "https://leg.mt.gov/bills/mca/title_0160/chapter_0120/"),
        "employment": NOT_CONFIRMED("Two statutes must be read together: the cannabis act preserves employers' "
                                    "workplace policies (§16-12-108(5), confirmed), while the lawful-products law "
                                    "(§39-2-313) limits action over off-duty use, but the report describes that "
                                    "one only from secondary summaries.", "MCA §16-12-108(5); §39-2-313"),
    },
    "NE": {
        "public_use": F("No statute specifically permits or bans public use of medical cannabis; the "
                        "patient protection states no limit on where.", "Neb. Rev. Stat. §71-24,105",
                        "https://nebraskalegislature.gov/laws/statutes.php?statute=71-24,105"),
        "employment": F("None: the medical cannabis statutes say nothing about employers, hiring, "
                        "accommodation or drug testing.", "Neb. Rev. Stat. §§71-24,104 to 71-24,105",
                        "https://nebraskalegislature.gov/laws/statutes.php?statute=71-24,105"),
    },
    "NV": {
        "public_use": F("Public consumption is a misdemeanor (fine up to $600), except inside a licensed "
                        "consumption lounge.", "NRS 678D.310(3)", "https://www.leg.state.nv.us/nrs/NRS-678D.html"),
        "employment": NOT_CONFIRMED("Nevada restricts pre-employment marijuana screening (NRS 613.132), but the "
                                    "report quotes it from the bill's text, still to be checked against the "
                                    "codified statute.", "NRS 613.132"),
    },
    "NH": {
        "public_use": F("Patients may use it on private property only. Smoking or vaping in any public "
                        "place, including buses, parks and beaches, is not protected, nor is use at work, "
                        "school or in prison.", "RSA 126-X:3", "https://gc.nh.gov/rsa/html/X/126-X/126-X-mrg.htm"),
        "employment": F("No duty to accommodate use at work, and employers may discipline employees for "
                        "using cannabis in the workplace.", "RSA 126-X:3, III(c)",
                        "https://gc.nh.gov/rsa/html/X/126-X/126-X-mrg.htm"),
    },
    "NJ": {
        "public_use": F("Smoking, vaping or aerosolising cannabis is unlawful wherever the Smoke-Free Air "
                        "Act bans smoking.", "N.J. Smoke-Free Air Act; CREAMM Act",
                        "https://www.nj.gov/cannabis/adult-personal/index.shtml",
                        note="Towns enforce their own civil fines."),
        "employment": F("Employers may not refuse to hire, dismiss or act against someone because they "
                        "do or do not use cannabis, nor solely because of a positive drug test.",
                        "N.J.S.A. 24:6I-52 (as amended by P.L.2025, c.325)",
                        "https://www.njleg.state.nj.us/2020/Bills/PL21/16_.HTM",
                        note="The statute allows action for use or impairment at work; see its full text."),
    },
    "NM": {
        "public_use": F("Smoking in a public place is not allowed except in a licensed consumption area, "
                        "and carries a $50 civil penalty. The regulator says cannabis may only be "
                        "consumed at a licensed consumption lounge or at a private residence.",
                        "NMSA §26-2C-26(A)-(B)", NM_PDF, note=NM_NOTE),
        "employment": NOT_CONFIRMED("Medical patients have an employment protection (§26-2B-9), but the report "
                                    "quotes it from a search-index excerpt, still to be checked against the "
                                    "official statute.", "NMSA §26-2B-9"),
    },
    "NY": {
        "public_use": NOT_CONFIRMED("The report's account of where consumption is allowed (Penal Law §222.10) "
                                    "was only partly corrected in the audit.", "Penal Law §222.10",
                                    "https://www.nysenate.gov/legislation/laws/PEN/222.10"),
        "employment": F("Employers may not discriminate against an employee for lawful cannabis use "
                        "off duty, off the premises and without the employer's equipment.",
                        "Labor Law §201-d (as amended by the MRTA)",
                        "https://www.nysenate.gov/legislation/laws/CAN/3",
                        note="Exceptions apply, for example impairment at work; see the statute."),
    },
    "NC": {
        "public_use": F("Not legal anywhere under state law.", "N.C.G.S. 90-95(a)",
                        "https://ncleg.gov/EnactedLegislation/SessionLaws/HTML/2021-2022/SL2022-32.html"),
        "employment": F("No protection: employers may keep drug-free workplace policies and refuse to hire "
                        "or dismiss for a confirmed positive THC test.", "N.C.G.S. 90-95(a)",
                        "https://ncleg.gov/EnactedLegislation/SessionLaws/HTML/2021-2022/SL2022-32.html"),
    },
    "ND": {
        "public_use": F("Patients may not use it in the places the law lists, which include public places, "
                        "nor drive or control a vehicle under its influence.", "NDCC §19-24.1-33",
                        "https://www.legis.nd.gov/cencode/t19c24-1.pdf"),
        "employment": NOT_CONFIRMED("The statute is described as preserving employer discipline (§19-24.1-34), "
                                    "but the report's text comes from secondary summaries, still to be checked "
                                    "verbatim.", "NDCC §19-24.1-34"),
    },
    "OH": {
        "public_use": F("Public consumption is prohibited, and Ohio licenses no consumption lounges.",
                        "ORC ch. 3796", "https://codes.ohio.gov/ohio-revised-code/chapter-3796"),
        "employment": F("No protection: the law does not require employers to permit or accommodate use, "
                        "and preserves their right to act on it, for adult and medical use alike.",
                        "ORC 3796.28 (SB 56, eff. 20 Mar 2026)",
                        "https://codes.ohio.gov/ohio-revised-code/chapter-3796"),
    },
    "OK": {
        "public_use": F("No statewide ban on public consumption was confirmed. Property and business owners "
                        "may ban smoking and vaping on their premises and within 10 ft of an entrance.",
                        "63 O.S. §427.8(C)", "https://oklahoma.gov/omma/"),
        "employment": NOT_CONFIRMED("Patient protections changed on 1 Nov 2026 (HB 3127); the report describes the "
                                    "new text only from law-firm analyses, still to be checked against the "
                                    "enrolled bill.", "63 O.S. §427.8"),
    },
    "OR": {
        "public_use": F("Use in a public place is unlawful, a Class B violation.", "ORS 475C.377",
                        "https://www.oregonlegislature.gov/bills_laws/ors/ors475C.html"),
        "employment": F("No general protection for off-duty use or for a positive test, for adults or "
                        "medical patients.", "ORS ch. 475C",
                        "https://www.oregonlegislature.gov/bills_laws/ors/ors475C.html"),
    },
    "PA": {
        "public_use": F("Smoking medical marijuana is unlawful, and the Act authorises no public consumption.",
                        "Act 16 of 2016 §304(1)", "https://www.legis.state.pa.us/WU01/LI/LI/US/HTM/2016/0/0016..HTM"),
        "employment": F("Employers may not discriminate in pay, terms or conditions of employment solely "
                        "because someone is a certified patient.", "Act 16 of 2016 §2103(b)(1)",
                        "https://www.legis.state.pa.us/WU01/LI/LI/US/HTM/2016/0/0016..HTM",
                        note="Employers need not allow use on their premises; see §2103 in full."),
    },
    "RI": {
        "public_use": F("Smoking or vaping is prohibited in any public place or anywhere tobacco smoking is "
                        "banned, on school buses and public transport, on school grounds and in "
                        "correctional facilities.", "R.I. Gen. Laws §21-28.11-29(a)(2)",
                        "http://webserver.rilegislature.gov/Statutes/TITLE21/21-28.11/21-28.11-29.htm"),
        "employment": F("Employers need not accommodate use, possession or being under the influence at "
                        "work, including remote work, and may adopt policies banning it there.",
                        "R.I. Gen. Laws ch. 21-28.11",
                        "http://webserver.rilegislature.gov/Statutes/TITLE21/21-28.11/21-28.11-29.htm"),
    },
    "SC": {
        "public_use": F("Not legal anywhere: public use is charged as possession.", "S.C. Code §44-53-370",
                        "https://www.scstatehouse.gov/code/t44c053.php"),
        "employment": F("No protection: marijuana is illegal, and no statute restricts private-employer "
                        "drug testing.", "S.C. Code §41-1-15", "https://www.scstatehouse.gov/code/t44c053.php"),
    },
    "SD": {
        "public_use": F("Patients may not use it on public transport, in public places or in vehicles, "
                        "and those under 21 may not smoke or vape it.", "SDCL §34-20G-18",
                        "https://sdlegislature.gov/Statutes/34-20G-18"),
        "employment": F("For dealings with an employer and employer drug testing, a registered patient is "
                        "treated as if prescribed a pharmaceutical drug. In safety-sensitive jobs an "
                        "employer may still act on a positive test alone.", "SDCL §34-20G-22 (as amended by SB 12, 2024)",
                        "https://sdlegislature.gov/Statutes/34-20G-22"),
    },
    "TN": {
        "public_use": F("Not legal anywhere: public use is charged as possession.", "Tenn. Code §39-17-418", "",
                        note="The audited report cites the Tennessee Code, but no official link for it was captured."),
        "employment": F("None: marijuana is illegal, and no statute protects its use.", "Tenn. Code §39-17-418", "",
                        note="The audited report cites the Tennessee Code, but no official link for it was captured."),
    },
    "TX": {
        "public_use": F("Smoking is prohibited for Compassionate Use patients in any setting; inhalation "
                        "only as prescribed, through an approved device.", "Health & Safety Code ch. 487",
                        "https://www.dps.texas.gov/section/compassionate-use-program"),
        "employment": F("No protection for Compassionate Use patients: the law has no anti-discrimination, "
                        "accommodation or hiring protection.", "Health & Safety Code ch. 487",
                        "https://www.dps.texas.gov/section/compassionate-use-program"),
    },
    "UT": {
        "public_use": F("No use in public view, except in a medical emergency. A first offence is an "
                        "infraction with a fine of up to $100.", "Utah Code §26B-4-216(2)",
                        "https://medicalcannabis.utah.gov/"),
        "employment": F("State and local government employers must treat lawful medical use and card "
                        "status like any other prescribed medication, with exceptions for federal funding, "
                        "security clearances and federally licensed positions.", "Utah Code §26B-4-207(2)",
                        "https://medicalcannabis.utah.gov/",
                        note="This protection covers public employers; the section sets no rule for private ones."),
    },
    "VT": {
        "public_use": F("No one may consume cannabis in a public place unless the law specifically allows it.",
                        "7 V.S.A. §833", "https://ccb.vermont.gov/laws-rules-and-regulations"),
        "employment": F("Employers need not permit or accommodate use at work. Separately, Vermont law "
                        "restricts when an employer may require a drug test.", "18 V.S.A. §4230a(e); 21 V.S.A. §513",
                        "http://legislature.vermont.gov/statutes/section/18/084/04230a"),
    },
    "VA": {
        "public_use": F("Public consumption is a $25 civil penalty for a first offence and a Class 4 "
                        "misdemeanor from the third; the civil penalty rises to $250 on 1 July 2027.",
                        "Va. Code §4.1-1108", "https://law.lis.virginia.gov/vacode/title4.1/chapter6/"),
        "employment": F("Employers may not dismiss, discipline or discriminate against an employee for "
                        "lawful use of medical cannabis oil under a practitioner's written certification. "
                        "No such protection was found for adult use.", "Va. Code §40.1-27.4",
                        "https://law.lis.virginia.gov/vacode/title4.1/chapter6/"),
    },
    "WA": {
        "public_use": F("Only in private, out of public view; not in a public place.", "RCW 69.50.445",
                        "https://app.leg.wa.gov/rcW/default.aspx?cite=69.50"),
        "employment": F("In initial hiring, employers may not discriminate based on cannabis use off the job "
                        "and away from the workplace, or on a pre-employment test for non-psychoactive "
                        "metabolites.", "RCW 49.44.240 (SB 5123, 2023)",
                        "https://app.leg.wa.gov/rcW/default.aspx?cite=69.50",
                        note="The statute has exceptions; see its full text."),
    },
    "WV": {
        "public_use": NOT_CONFIRMED("The report records the claim that patients may use it only in private as a "
                                    "searched absence in the Act, still to be confirmed in the rules.",
                                    "W. Va. Code ch. 16A"),
        "employment": F("Employers may not dismiss, threaten, refuse to hire or otherwise discriminate "
                        "against an employee solely because they are certified to use medical cannabis.",
                        "W. Va. Code ch. 16A", "https://code.wvlegislature.gov/16A-3/"),
    },
    "WI": {
        "public_use": F("Not legal anywhere: possession itself is the offence.", "Wis. Stat. §961.41(3g)(e)",
                        "https://docs.legis.wisconsin.gov/document/acts/2019/68,54n"),
        "employment": F("None: marijuana is illegal, there is no medical programme, and no statute protects "
                        "an employee for use or a positive test.", "Wis. Stat. ch. 961",
                        "https://docs.legis.wisconsin.gov/document/acts/2019/68,54n"),
    },
    "WY": {
        "public_use": F("Not legal anywhere: possession itself is the offence.", "W.S. 35-7-1031", "",
                        note="The audited report cites the Wyoming statutes, but no official link for them was captured."),
        "employment": F("None: there is no programme to protect, and no statute stops an employer acting "
                        "on a positive marijuana test.", "W.S. 35-7-1031", "",
                        note="The audited report cites the Wyoming statutes, but no official link for them was captured."),
    },
}

for _code, _facts in LAW_MORE.items():
    QUICK[_code].update(_facts)


# Driving under the influence, added 20 Nov 2026: a THC blood limit ("per se"), zero
# tolerance, or proof of impairment. Same terms and checks as everything above.
DRIVING = {
    "AL": F("Impairment-based: Alabama has no per se THC limit for driving.", "Ala. Code tit. 32",
            "https://alison.legislature.state.al.us/files/pdf/SearchableInstruments/2021RS/PrintFiles/213097-2.pdf"),
    "AK": F("Impairment-based: driving under the influence of marijuana is DUI, with no per se THC blood level.",
            "AS 28.35.030", "https://www.akleg.gov/"),
    "AZ": F("Impairment-based: no per se THC blood limit. For adults 21+, impairment must be shown.",
            "A.R.S. §36-2852(B)", "https://www.azleg.gov/viewdocument/?docName=https://www.azleg.gov/ars/36/02850.htm"),
    "AR": NOT_CONFIRMED("The report reads Ark. Code §5-65-103 only from unofficial copies. The official "
                        "compilation of Amendment 98 confirms only that a patient may not drive under the "
                        "influence of marijuana, not whether there is a per se limit.", "Ark. Code §5-65-103"),
    "CA": F("Impairment-based: California has never set a per se limit for THC.", "Cal. Vehicle Code",
            "https://www.cannabis.ca.gov/cannabis-laws/"),
    "CO": F("No per se limit, but 5 ng/mL or more of delta-9 THC in whole blood allows a court to infer "
            "impairment.", "C.R.S. §42-4-1301(6)(a)(IV)", "https://med.colorado.gov/"),
    "CT": F("Impairment-based: no per se THC limit.", "Conn. Gen. Stat. §14-227a",
            "https://www.cga.ct.gov/current/pub/chap_248.htm"),
    "DE": F("No numeric THC limit. Driving under the influence of any drug is an offence, and so is having "
            "any amount of a drug in the blood within 4 hours of driving where its use was unlawful; lawful "
            "adult or medical use, which the driver must prove, falls outside that second rule.",
            "21 Del.C. §4177(a)(2), (a)(6), (c)(8)", "https://omc.delaware.gov/adult-use/",
            note="Inactive metabolites alone do not count."),
    "DC": F("Impairment-based: no per se THC limit; the question is whether driving ability was "
            "noticeably impaired.", "D.C. Code §50-2206.11",
            "https://oag.dc.gov/public-safety/driving-under-influence/marijuana-and-impaired-driving"),
    "FL": F("Impairment-based: no per se THC limit; the only per se limit is for alcohol.", "Fla. Stat. §316.193(1)",
            "https://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0300-0399/0316/Sections/0316.193.html",
            note=CHK),
    "GA": NOT_CONFIRMED("The report's reading of §40-6-391 (no numeric THC limit; the any-amount provision "
                        "narrowed by Love v. State) rests only on a Justia copy of the Code; the report "
                        "lists the live legis.ga.gov text as still unverified.",
                        "O.C.G.A. §40-6-391"),
    "HI": F("Impairment-based: no per se THC limit; the test is whether ability to drive carefully is impaired.",
            "HRS §291E-61(a)", "https://health.hawaii.gov/medicalcannabisregistry/general-information/marijuana-laws-and-related-documents/"),
    "ID": F("Impairment-based: no THC concentration, nanogram limit or metabolite threshold.", "Idaho Code §18-8004",
            "https://legislature.idaho.gov/statutesrules/idstat/title18/t18ch80/sect18-8004/"),
    "IL": F("Per se limit: 5 ng/mL or more of delta-9 THC in whole blood, or 10 ng/mL in another bodily "
            "substance, within two hours of driving.", "625 ILCS 5/11-501(a)(7); 5/11-501.2(a)(6)",
            "https://ilga.gov/legislation/ILCS/details?ActID=3992&ActName=Cannabis+Regulation+and+Tax+Act."),
    "IN": F("Zero tolerance: any amount of marijuana or its metabolite in the body while driving is an "
            "offence (Class C misdemeanor), with no impairment needed. A narrow defence applies if the "
            "driver was not intoxicated and caused no accident.", "IC 9-30-5-1(c)-(d)",
            "https://public.courts.in.gov/Decisions/api/Document/Opinion?Id=DmYIl2h3bOKWWdQQvJyPZ_rjZgo14Y_LmDtP2-HSBr7Uf3wsJD127SUP1Lq0Mzh20"),
    "IA": F("Zero tolerance: any amount of a controlled substance in blood or urine, even a non-impairing "
            "THC metabolite, is an offence. A medical card does not exempt the driver.",
            "Iowa Code §321J.2(1)(c); State v. Comried", "https://www.legis.iowa.gov/docs/code/2024/124E.pdf"),
    "KS": F("Impairment-based: no per se THC limit.", "K.S.A. 8-1567",
            "https://kslegislature.gov/li_2022/b2021_22/statute/065_000_0000_chapter/065_041_0000_article/065_041_0001_section/065_041_0001_k/"),
    "KY": F("Impairment-based: Kentucky has not adopted a per se THC limit.", "KRS 189A.010",
            "https://apps.legislature.ky.gov/law/statutes/statute.aspx?id=54279"),
    "LA": F("Impairment-based: no per se THC limit, and the standard applies to patients too.",
            "La. R.S. 14:98", "https://www.legis.la.gov/Legis/Law.aspx?p=y&d=96986"),
    "ME": NOT_CONFIRMED("The report finds no per se THC limit for adults, but from secondary reporting, "
                        "still to be checked against 29-A MRS §2411.", "29-A MRS §2411"),
    "MD": F("Impairment-based: no per se THC limit. Driving while impaired by cannabis is a criminal offence.",
            "Md. Transportation §21-902", "https://cannabis.maryland.gov/pages/cannabisfaq.aspx"),
    "MA": F("Impairment-based: the only numeric per se limit is for alcohol.", "M.G.L. c.90 §24(1)(a)(1)",
            "https://malegislature.gov/Laws/GeneralLaws/PartI/TitleXV/Chapter94G"),
    "MI": F("No per se THC limit; impaired driving is charged under the Vehicle Code. Registered patients "
            "are judged on impairment, not on the presence of THC.", "MCL 257.625; People v. Koon",
            "https://www.michigan.gov/cra"),
    "MN": F("Impairment-based: the \"any amount\" drug offence expressly excludes cannabis, so cannabis is "
            "charged under the impairment clause.", "Minn. Stat. §169A.20, subd. 1(7)-(8)",
            "https://www.revisor.mn.gov/statutes/cite/342"),
    "MS": NOT_CONFIRMED("The report reads §63-11-30 only from a Justia copy, and lists the per se question "
                        "among the sections it did not open.", "Miss. Code §63-11-30"),
    "MO": F("Impairment-based: a conviction needs evidence of actual influence, not THC or metabolites alone.",
            "Mo. Const. art. XIV §2.3(1)(d)",
            "https://revisor.mo.gov/main/OneSection.aspx?section=XIV%20Section%202&bid=51541"),
    "MT": F("Per se limit: 5 ng/mL or more of THC, not counting inactive metabolites. Drivers under 21: any THC.",
            "MCA §61-8-1002(1)(d), (1)(e)(ii)", "https://leg.mt.gov/bills/mca/title_0160/chapter_0120/"),
    "NE": F("Impairment-based: no per se THC limit.", "Neb. Rev. Stat. §60-6,196(1)",
            "https://nebraskalegislature.gov/laws/statutes.php?statute=60-6,196"),
    "NV": F("Impairment-based for ordinary DUI since 1 July 2021. Per se blood limits (2 ng/mL delta-9 THC, "
            "5 ng/mL metabolite) now apply only to felony DUI.", "NRS 484C.110(4); AB 400 (2021)",
            "https://www.leg.state.nv.us/nrs/NRS-678D.html"),
    "NH": NOT_CONFIRMED("The report finds no per se THC limit, but relies on the DWI statute's text as "
                        "reproduced secondarily, still to be checked on the official RSA page.", "RSA 265-A:2"),
    "NJ": F("Impairment-based: no per se THC limit.", "N.J.S.A. 39:4-50",
            "https://www.nj.gov/cannabis/adult-personal/index.shtml"),
    "NM": NOT_CONFIRMED("The report finds no per se THC limit, judged under the DWI statute, but marks the "
                        "finding unverified pending the statute text.", "NMSA §66-8-102"),
    "NY": F("Impairment-based: no per se THC limit; driving while ability is impaired by a drug is the offence.",
            "Vehicle and Traffic Law §1192(4)", "https://cannabis.ny.gov/what-you-need-know-fact-sheet"),
    "NC": F("Impairment-based: no per se THC limit.", "N.C.G.S. 20-138.1",
            "https://ncleg.gov/EnactedLegislation/SessionLaws/HTML/2021-2022/SL2022-32.html"),
    "ND": F("Impairment-based: the test is whether the driver is incapable of driving safely; the 0.08% "
            "limit is for alcohol only.", "NDCC §39-08-01", "https://www.legis.nd.gov/cencode/t19c24-1.pdf"),
    "OH": F("Per se limits: 2 ng/mL of marihuana in whole blood or blood serum/plasma, or 10 ng/mL in "
            "urine, with separate limits for its metabolite.", "ORC 4511.19(A)(1)(j)(vii)",
            "https://codes.ohio.gov/ohio-revised-code/chapter-3796"),
    "OK": F("No nanogram threshold, but the statute also makes it an offence to drive with any amount of a "
            "Schedule I substance or its metabolites. Being a licensed patient is no defence.",
            "47 O.S. §11-902(A)(3), (B)", "https://oklahoma.gov/omma/",
            note="How the any-amount rule and the impairment rules fit together for patients is not settled "
                 "in the case law the audit found."),
    "OR": F("Impairment-based: no per se THC blood limit.", "ORS 813.010(1)(b)-(c)",
            "https://www.oregonlegislature.gov/bills_laws/ors/ors475C.html"),
    "PA": F("Zero tolerance: no nanogram limit, but driving with any amount of a Schedule I substance or its "
            "metabolite in the blood is an offence. Medical patients are not exempt.",
            "75 Pa.C.S. §3802(d)(1)(i)", "https://www.legis.state.pa.us/WU01/LI/LI/US/HTM/2016/0/0016..HTM"),
    "RI": F("Impairment-based: no numeric THC limit. Some penalty tiers turn on the presence of any scheduled "
            "controlled substance in the blood.", "R.I. Gen. Laws §31-27-2",
            "https://webserver.rilegislature.gov/Statutes/TITLE21/21-28.11/21-28.11-22.htm"),
    "SC": F("Impairment-based (\"materially and appreciably impaired\"); no per se THC limit.",
            "S.C. Code §56-5-2930(A)", "https://www.scstatehouse.gov/code/t44c053.php"),
    "SD": F("No per se THC limit for adults, and a medical card gives no driving immunity. Drivers under 21: "
            "zero tolerance.", "SDCL §32-23-1; §32-23-21", "http://sdlegislature.gov/api/Statutes/34-20G.html"),
    "TN": NOT_CONFIRMED("The report reads §55-10-401 only from a Justia copy and says its Code links are "
                        "reproductions, to be checked against the official text.", "Tenn. Code §55-10-401"),
    "TX": NOT_CONFIRMED("The report describes DWI as impairment-based, but marks its per se detail "
                        "unverified, resting on secondary summaries.", "Texas Penal Code ch. 49"),
    "UT": F("Zero tolerance: any measurable controlled substance or metabolite is an offence, without proof of "
            "impairment. The inactive metabolite is excepted, and medical cannabis taken in dosage form under "
            "the programme is an affirmative defence.", "Utah Code §41-6a-517",
            "https://le.utah.gov/xcode/Title41/Chapter6a/C41-6a-S517_2026050620260506.pdf"),
    "VT": F("Impairment-based: no per se THC limit.", "23 V.S.A. §1201",
            "http://legislature.vermont.gov/statutes/section/18/084/04230a"),
    "VA": NOT_CONFIRMED("The report finds driving impairment-based with no per se THC limit, but marks it "
                        "unverified until §18.2-266 is opened directly.", "Va. Code §18.2-266"),
    "WA": F("Per se limit: 5.00 ng/mL or more of THC in the blood within two hours of driving. Drivers under "
            "21: any THC above 0.00.", "RCW 46.61.502(1)(b); RCW 46.61.503",
            "https://app.leg.wa.gov/RCW/default.aspx?cite=46.61.506"),
    "WV": F("The general DUI law is impairment-based. Medical patients may not drive with more than 3 ng of "
            "active THC per mL of blood serum.", "W. Va. Code §17C-5-2; §16A-5-10(1)",
            "https://code.wvlegislature.gov/16A-3/"),
    "WI": F("Driving with 1 ng/mL or more of delta-9 THC in the blood is an offence; metabolites alone do not "
            "count. Impaired driving is a separate offence.", "Wis. Stat. §346.63(1)(am); §340.01(50m)(e)",
            "https://docs.legis.wisconsin.gov/document/acts/2019/68,54n"),
    "WY": NOT_CONFIRMED("The report reads §31-5-233 only from Justia and FindLaw copies of the statutes.",
                        "W.S. 31-5-233"),
}

for _code, _fact in DRIVING.items():
    QUICK[_code]["driving"] = _fact


# --------------------------------------------------------------------------------------
# Who qualifies for medical use (added 20 Nov 2026). Read from each report's medical
# programme section (§1.4 in most) and its audit rows. A list is published only where the
# report confirms it from an official source; a list read from a mirror or Justia copy,
# or from secondary sources, is held back. Where a list is long or the report does not
# give it whole, the text says "include" or "among them" rather than presenting a part
# as the whole. Counts are given only where the report confirms the count itself.
NONE = "None: the state has no medical marijuana programme, so no condition qualifies a patient."
MEDICAL = {
    "AK": F("A physician's certification for cancer, glaucoma, HIV or AIDS; a chronic or debilitating "
            "disease that produces cachexia, severe pain, severe nausea, seizures or persistent muscle "
            "spasms; or another condition the health department approves.", "AS 17.37.070",
            "https://health.alaska.gov/en/education/drugs-and-alcohol/marijuana/medical-marijuana/"),
    "AL": F("One of 16 categories of condition listed in the statute, as the Medical Cannabis Commission's "
            "patient page shows them. Conventional treatment must have failed first, unless it is not the "
            "standard of care for the condition.", "Ala. Code §20-2A-3(21); r. 538-X-1-.04",
            "https://amcc.alabama.gov/patients/"),
    "AR": F("Cancer, glaucoma, HIV or AIDS, hepatitis C, ALS, Tourette's syndrome, Crohn's disease, ulcerative "
            "colitis, PTSD, severe arthritis, fibromyalgia or Alzheimer's disease; a chronic or debilitating "
            "condition that produces cachexia, peripheral neuropathy, intractable pain lasting more than six "
            "months, severe nausea, seizures or severe persistent muscle spasms; or a condition the "
            "Department of Health approves.", "Ark. Const. amend. 98 §2(13)",
            "https://www.dfa.arkansas.gov/office/medical-marijuana-commission/"),
    "AZ": NOT_CONFIRMED("The report confirms the statutory list only from a mirror of the statute; the "
                        "official text on azleg.gov was not opened.", "A.R.S. §36-2801"),
    "CA": F("A physician's recommendation for cancer, anorexia, AIDS, chronic pain, spasticity, glaucoma, "
            "arthritis, migraine, \"or any other illness for which marijuana provides relief\". The state "
            "medical ID card is voluntary.", "Health & Safety Code §11362.5; §11362.71(f)",
            "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=HSC&sectionNum=11362.5"),
    "CO": F("The constitution's list (cancer, glaucoma, HIV or AIDS, or a chronic or debilitating condition "
            "producing cachexia, severe pain, severe nausea, seizures or persistent muscle spasms), plus PTSD, "
            "autism spectrum disorder, and any condition for which a physician could prescribe an opioid.",
            "Colo. Const. art. XVIII §14(1)(a); C.R.S. §25-1.5-106",
            "https://cdphe.colorado.gov/medical-marijuana-registry-providers",
            note="The health department's own list of conditions it has added is not yet confirmed."),
    "CT": F("One of 42 conditions for adults, or 11 for patients under 18, on the state's list; the Board of "
            "Physicians can recommend more.", "DCP qualifying conditions list",
            "https://portal.ct.gov/cannabis/knowledge-base/articles/mmp/qualifying-conditions"),
    "DC": F("Any condition for which an authorised practitioner decides treatment with medical cannabis would "
            "be beneficial. There is no closed list.", "D.C. Code §7-1671.01(17)",
            "https://code.dccouncil.gov/us/dc/council/code/titles/7/chapters/16B/index.full.html"),
    "DE": F("Since 2024, any diagnosed medical condition from which a health-care practitioner decides the "
            "patient is likely to benefit. Patients 65 and over may certify themselves.",
            "16 Del.C. §4902A(4); §4908A(a)(1)b; HB 285 (84 Del. Laws c. 264)", "https://omc.delaware.gov/"),
    "FL": F("Cancer, epilepsy, glaucoma, HIV or AIDS, PTSD, ALS, Crohn's disease, Parkinson's disease, "
            "multiple sclerosis, conditions of the same kind or comparable to these, a terminal condition, "
            "or chronic nonmalignant pain.", "Fla. Stat. §381.986(2)",
            "https://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0300-0399/0381/Sections/0381.986.html"),
    "GA": F("Low-THC oil only. The Department of Public Health lists 18 qualifying items, hospice care among "
            "them; they include cancer, ALS, multiple sclerosis, Parkinson's disease, sickle cell "
            "disease, Tourette's syndrome, Alzheimer's disease, autism and PTSD (patients 18 and over).",
            "DPH Low THC Oil Registry; SB 220",
            "https://dph.georgia.gov/low-thc-oil-registry/patients-and-caregivers"),
    "HI": F("Three routes since 2025: a listed debilitating condition; a primary treating provider's "
            "certification that the benefit outweighs the risk; or hospice care.", "Act 241, SLH 2025",
            "https://data.capitol.hawaii.gov/sessions/sessionlaws/Years/SLH2025/SLH2025_Act241.pdf"),
    "IA": F("Medical cannabidiol only: one of 13 conditions in the health department's rule, or a condition "
            "the Medical Cannabidiol Board has added.", "641 IAC 154.1",
            "https://hhs.iowa.gov/health-prevention/medical-cannabis",
            note="Whether two of the rule's conditions (ulcerative colitis and corticobasal degeneration) are "
                 "also in the current Code section is not confirmed."),
    "ID": F(NONE, "Idaho Code §37-2701 et seq.",
            "https://legislature.idaho.gov/statutesrules/idstat/Title37/T37CH27/SECT37-2701",
            note="HJR 4 was voted on 3 Nov 2026 and the result is not yet certified. Nothing here reflects any "
                 "outcome."),
    "IL": F("One of 58 debilitating conditions on the Department of Public Health's list.", "410 ILCS 130",
            "https://dph.illinois.gov/topics-services/prevention-wellness/medical-cannabis/debilitating-conditions",
            note="The count was checked against the list itself. Whether terminal illness also qualifies is "
                 "not shown on that page."),
    "IN": F(NONE, "Ind. Code art. 35-48", "https://public.courts.in.gov/Decisions/api/Document/Opinion?Id="
            "DmYIl2h3bOKWWdQQvJyPZ_rjZgo14Y_LmDtP2-HSBr7Uf3wsJD127SUP1Lq0Mzh20",
            note="Hemp and low-THC hemp extract are excluded from the definition of marijuana; that is not a "
                 "medical programme."),
    "KS": F(NONE, "K.S.A. 65-4101(aa)", "https://kslegislature.gov/li_2022/b2021_22/statute/065_000_0000_chapter/"
            "065_041_0000_article/065_041_0001_section/065_041_0001_k/",
            note="CBD and industrial hemp are excluded from the definition of marijuana; that is not a medical "
                 "programme."),
    "KY": F("Any cancer; chronic, severe, intractable or debilitating pain; epilepsy or another intractable "
            "seizure disorder; multiple sclerosis, muscle spasms or spasticity; chronic nausea or cyclical "
            "vomiting syndrome that has not responded to other treatment; PTSD; or a condition the Kentucky "
            "Center for Cannabis approves.", "KRS 218B.010(26)", "https://kymedcan.ky.gov",
            note="An executive order directing an emergency regulation on conditions is disputed and is not "
                 "reflected here."),
    "LA": F("A listed condition, or any other condition an authorised clinician considers debilitating and "
            "is qualified to treat. There is no patient card or registry.", "La. R.S. 40:1046(A)(2)",
            "https://ldh.la.gov/page/medical-marijuana"),
    "MA": F("Cancer, glaucoma, HIV or AIDS, hepatitis C, ALS, Crohn's disease, Parkinson's disease and "
            "multiple sclerosis, when debilitating.", "935 CMR 501.002",
            "https://masscannabiscontrol.com/know-the-laws/",
            note="Whether a provider may also certify other debilitating conditions is not yet confirmed from "
                 "the regulation's official text."),
    "MD": F("Cachexia, anorexia, wasting syndrome, severe or chronic pain, severe nausea, seizures, severe or "
            "persistent muscle spasms, glaucoma, PTSD, or another chronic medical condition which is severe "
            "and for which other treatments have been ineffective.", "Maryland Cannabis Administration",
            "https://cannabis.maryland.gov/Pages/patients.aspx"),
    "ME": F("No list. A medical provider certifies that, in their professional opinion, the patient is likely "
            "to benefit. Registering with the state is voluntary.", "18-691 CMR ch. 2 §5",
            "https://www.maine.gov/dafs/ocp/medical-use"),
    "MI": NOT_CONFIRMED("The report's list of Michigan's conditions comes from secondary sources, and the audit "
                        "leaves the medical programme section unverified in part.", "MCL 333.26423"),
    "MN": F("A condition for which the patient's own health care practitioner has recommended cannabis, or "
            "one of 19 named diagnoses.", "Minn. Stat. §342.01, subd. 63",
            "https://www.revisor.mn.gov/statutes/cite/342.01"),
    "MO": F("A physician's or nurse practitioner's certification. The constitution's list includes cancer, "
            "epilepsy, glaucoma, intractable migraines, chronic conditions causing severe persistent pain or "
            "muscle spasms, debilitating psychiatric disorders such as PTSD, and HIV or AIDS, and ends with a "
            "catch-all for other chronic or debilitating conditions a physician certifies.",
            "Mo. Const. art. XIV §1.2(22)", "https://health.mo.gov/business-professionals/cannabis-regulation"),
    "MS": NOT_CONFIRMED("The report reads the list (20 named items) from a Justia copy of the statute, not "
                        "the official text.", "Miss. Code §41-137-3"),
    "MT": F("A closed list: cancer, glaucoma, HIV or AIDS with serious symptoms; cachexia or wasting syndrome; "
            "severe chronic pain; intractable nausea or vomiting; epilepsy or an intractable seizure disorder; "
            "multiple sclerosis; Crohn's disease; painful peripheral neuropathy; a central nervous system "
            "disorder causing chronic, painful spasticity or muscle spasms; hospice care; or PTSD.",
            "MCA §16-12-102(10)", "https://leg.mt.gov/bills/mca/title_0160/chapter_0120/"),
    "NC": F(NONE, "N.C.G.S. 90-87(16), 90-94", "https://ncleg.gov/EnactedLegislation/SessionLaws/HTML/2021-2022/"
            "SL2022-32.html", note="Hemp extract has a narrow exemption (G.S. 90-94.1); that is not a medical "
                                   "programme. On Eastern Band of Cherokee trust land, tribal law governs."),
    "ND": F("The statute's list includes cancer, HIV or AIDS, decompensated cirrhosis from hepatitis C, ALS, "
            "PTSD, agitation of Alzheimer's disease, Crohn's disease, fibromyalgia, spinal stenosis or chronic "
            "back pain, glaucoma, epilepsy, anorexia or bulimia, anxiety disorder, Tourette's syndrome, "
            "Ehlers-Danlos syndrome, endometriosis, interstitial cystitis, neuropathy, migraine, rheumatoid "
            "arthritis, autism, brain injury and terminal illness, plus chronic conditions with listed symptoms.",
            "N.D.C.C. §19-24.1-01", "https://www.legis.nd.gov/cencode/t19c24-1.pdf"),
    "NE": F("No list of conditions. A practitioner's written recommendation that the benefits outweigh the "
            "harms for a medical condition, its symptoms or the side effects of its treatment.",
            "Neb. Rev. Stat. §71-24,104", "https://nebraskalegislature.gov/laws/statutes.php?statute=71-24,104"),
    "NH": F("Adults 21 and over: any debilitating or terminal condition or symptom for which the provider "
            "judges the benefits likely outweigh the risks (since 1 Oct 2024). Others: a condition on the "
            "statute's lists, which include generalised anxiety disorder.", "RSA 126-X:1, IX",
            "https://gc.nh.gov/rsa/html/X/126-X/126-X-mrg.htm"),
    "NJ": NOT_CONFIRMED("The report's list of New Jersey's conditions rests on a secondary source, and the "
                        "count it gives (17) does not match the 18 conditions it lists."),
    "NM": F("One of 30 conditions on the Department of Health's list, among them Alzheimer's disease, ALS, "
            "anxiety disorder, autism spectrum disorder, cancer, Crohn's disease, epilepsy, glaucoma and "
            "HIV. Write-in diagnoses are not accepted.", "NM DOH Medical Cannabis Program",
            "https://prod.nmhealth.org/publication/view/guide/9262/"),
    "NV": F("A chronic or debilitating condition listed in the statute, among them anxiety disorder, autism, "
            "autoimmune disease, anorexia nervosa, cancer, opioid dependence, glaucoma, and conditions "
            "producing cachexia or muscle spasms; or one the Division classifies or approves on petition.",
            "NRS 678C.030", "https://www.leg.state.nv.us/Division/Legal/Lawlibrary/NRS/NRS-678C.html",
            note="Whether PTSD qualifies on its own is not confirmed."),
    "NY": F("Any condition the patient's certifying health care provider deems clinically appropriate; the "
            "statute's list ends with any other condition the practitioner certifies.", "Cannabis Law §3(18)",
            "https://cannabis.ny.gov"),
    "OH": F("One of 26 conditions: 21 in the statute, plus cachexia, Huntington's disease, spasticity, "
            "terminal illness and irritable bowel syndrome, which the State Medical Board added.",
            "ORC 3796.01(A)(6)", "https://codes.ohio.gov/ohio-revised-code/chapter-3796"),
    "OK": F("No list: the statute says \"There are no qualifying conditions\". A licensed physician recommends "
            "medical marijuana under the reasonable and prudent physician standard.", "63 O.S. §420(M)",
            "https://oklahoma.gov/omma/"),
    "OR": NOT_CONFIRMED("The report names the statute (ORS 475C.777) but does not reproduce its list, and "
                        "the 2026 expansion (HB 4142) is worded from a law-firm summary."),
    "PA": F("One of 24 serious medical conditions on the Department of Health's list, plus 2 more for "
            "research only.", "Medical Marijuana Act §103",
            "https://www.pa.gov/agencies/health/programs/medical-marijuana/medical-marijuana-patients"),
    "RI": NOT_CONFIRMED("The report quotes only the closing clause of the statutory definition "
                        "(§21-28.6-3(3)), not its list of conditions."),
    "SC": F(NONE, "S.C. Code §44-53-110(27), §44-53-370", "https://www.scstatehouse.gov/code/t44c053.php",
            note="A narrow CBD exception (Julian's Law) exists; it is not a medical programme."),
    "SD": F("A chronic or debilitating condition producing cachexia or wasting, severe debilitating pain, severe "
            "nausea (not from pregnancy), seizures or severe persistent muscle spasms; AIDS or HIV; ALS; "
            "multiple sclerosis; cancer with severe or chronic pain, nausea or vomiting, or wasting; Crohn's "
            "disease; epilepsy and seizures; or PTSD.", "SDCL 34-20G-1(8)",
            "https://sdlegislature.gov/Statutes/34-20G-1"),
    "TN": F(NONE, "Tenn. Code §39-17-402(16)", "",
            note="A narrow low-THC oil possession exclusion exists; it is not a medical programme. The audited "
                 "report cites the Tennessee Code, but no official link for it was captured."),
    "TX": NOT_CONFIRMED("The report reads the list from a Justia copy of the statute (as amended by HB 46), "
                        "not the official text.", "Tex. Occ. Code §169.003"),
    "UT": F("The statute's list includes HIV or AIDS, Alzheimer's disease, ALS, cancer, cachexia, persistent "
            "nausea (with exclusions), Crohn's disease or ulcerative colitis, epilepsy, multiple sclerosis, PTSD "
            "(with a qualifying diagnosis), autism, terminal illness, hospice care, rare conditions affecting "
            "fewer than 200,000 people in the US, pain lasting more than 2 weeks, and acute pain.",
            "Utah Code §26B-4-203",
            "https://le.utah.gov/xcode/Title26B/Chapter4/C26B-4-S203_2026050620260506.pdf"),
    "VA": F("No list: any diagnosed condition that the practitioner judges may benefit from cannabis.",
            "Va. Code §4.1-1601(A)", "https://law.lis.virginia.gov/vacode/4.1-1601/"),
    "VT": F("Cancer, multiple sclerosis, HIV or AIDS, glaucoma, Crohn's disease, Parkinson's disease, PTSD or "
            "ulcerative colitis, where the disease or its treatment causes severe, persistent and intractable "
            "symptoms; or a chronic, debilitating disease or treatment that produces cachexia or wasting, "
            "chronic pain, severe nausea or seizures.", "7 V.S.A. §951(8)",
            "https://legislature.vermont.gov/statutes/fullchapter/07/035"),
    "WA": F("The statute's list includes cancer, HIV, multiple sclerosis, epilepsy or other seizure disorders, "
            "spasticity disorders, intractable pain, glaucoma, Crohn's disease, hepatitis C, diseases causing "
            "nausea, vomiting, wasting or spasms, PTSD and traumatic brain injury, most limited to symptoms "
            "unrelieved by standard treatment. The patient must be a Washington resident at diagnosis.",
            "RCW 69.51A.010", "https://app.leg.wa.gov/RCW/default.aspx?cite=69.51A.010"),
    "WI": F(NONE, "Wis. Stat. §961.14(4)(t)", "https://docs.legis.wisconsin.gov/document/acts/2019/68,54n",
            note="A narrow certified-CBD exception exists; it is not a medical programme."),
    "WV": F("One of 15 serious medical conditions in the statute, terminal illness among them. Anxiety, "
            "depression, insomnia, ulcerative colitis and opioid use disorder are not on the list.",
            "W. Va. Code §16A-2-1(a)(30)", "https://code.wvlegislature.gov/16A-2-1/"),
    "WY": F(NONE, "W.S. 35-7-1031(c)", "",
            note="The audited report cites the Wyoming statutes, but no official link for them was captured."),
}

for _code, _fact in MEDICAL.items():
    QUICK[_code]["medical"] = _fact


# --------------------------------------------------------------------------------------
# Edibles (added 20 Nov 2026): THC limits per serving and per package, and the product
# rules that go with them. A limit is published only where the report ties it to an
# official source (statute, rule or regulator page); Nevada's NRS 678D.420 and Delaware's
# 4 Del.C. §1331 were also read online. Hemp and hemp-derived products follow other rules
# and are not covered here. A report that found NO limit is held back, not read as "none".
NO_MARKET = "None: there is no legal marijuana market, so no marijuana edibles."
HEMP = "Hemp-derived products follow separate rules, not covered here."
NO_LINK = HEMP + " The audited report cites the state's statutes, but no official link for them was captured."
EDIBLES = {
    "AK": F("No more than 10 mg of THC per serving and 100 mg per packaged unit.", "3 AAC 306",
            "https://www.commerce.alaska.gov/web/amco/",
            note="A total-THC formula is only a 2026 proposal (AO-360), not current law."),
    "AL": F("No food edibles: products baked, mixed or infused into food, such as cookies or candies, are "
            "banned. Oral forms are tablets, capsules, tinctures and non-sugar-coated gelatin cubes or "
            "lozenges.", "Ala. Code §20-2A-3(14)", "https://amcc.alabama.gov/patients/"),
    "AR": NOT_CONFIRMED("A 100 mg per-package edible limit appears only in a secondary source; the report "
                        "found it in no official text.", "Ark. Const. amend. 98"),
    "AZ": F("No more than 10 mg of THC per serving and 100 mg per package, delineated or scored into "
            "servings.", "A.R.S. §36-2854", "https://www.azleg.gov/ars/36/02854.htm"),
    "CA": F("No more than 10 mg of THC per serving, in standardised servings.", "MAUCRSA, as the AB 2532 "
            "digest restates it",
            "https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202520260AB2532",
            note="The 100 mg per package limit is in the regulations (4 CCR), which the report read only "
                 "from an unofficial copy."),
    "CO": NOT_CONFIRMED("The report reads the edible limits (Rule 4-115) only from Cornell's reproduction of "
                        "the rules, not the official text.", "1 CCR 212-3"),
    "CT": F("No more than 5 mg of THC per serving and 100 mg per package.", "DCP and Attorney General release",
            "https://portal.ct.gov/ag/press-releases/2024-press-releases/attorney-general-dcp-commissioner-"
            "cafferelli-announce-psa-regarding-illegal-cannabis-edibles"),
    "DC": NOT_CONFIRMED("The report found no per-serving or per-package edible limit in the D.C. Code sections "
                        "it opened, but did not establish that none exists."),
    "DE": F("No more than 10 mg of total THC per serving and 100 mg in a multi-serving package.",
            "4 Del.C. §1331", "https://delcode.delaware.gov/title4/c013/sc03/index.html", note=CHK),
    "FL": F("No more than 10 mg of THC per serving and 200 mg per edible. Edibles may not be attractive to "
            "children, shaped like a person, cartoon or animal, or resemble commercial candy.",
            "Fla. Stat. §381.986(8)(e)8.",
            "https://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&URL=0300-0399/0381/Sections/0381.986.html"),
    "GA": F("Medical cannabis products (low-THC only): up to 1,200 mg of THC per package.",
            "SB 220; DPH Low THC Oil Registry",
            "https://dph.georgia.gov/low-thc-oil-registry/patients-and-caregivers",
            note="Whether gummies count as an allowed ingestible or a banned candy or food product is "
                 "unresolved."),
    "HI": NOT_CONFIRMED("The report lists the product forms Hawaii's dispensaries may sell but gives no "
                        "confirmed per-serving or per-package limit for edibles.", "HRS §329D-10"),
    "IA": F("No edibles: manufacturers may not make edible medical cannabidiol products. Oral, topical, "
            "nebulised or vaporised, and rectal or vaginal forms are allowed; nothing smokable.",
            "Iowa Code §124E.7(12)(c); §124E.17", IA_URL, note=CHK),
    "IL": F("No more than 10 mg of THC per serving and 100 mg per package; the Department of Agriculture may "
            "change the amounts by rule.", "410 ILCS 705/55-21(k)",
            "https://ilga.gov/legislation/ilcs/fulltext?DocName=041007050K55-21"),
    "KY": F("Edibles and other oral products: no more than 10 mg of delta-9 THC per serving.",
            "915 KAR 1:070", "https://apps.legislature.ky.gov/law/kar/titles/915/001/070/",
            note="Whether there is also a per-package limit (915 KAR 1:100) is not confirmed."),
    "LA": NOT_CONFIRMED("The report finds edible forms (such as gelatin chewables) allowed by rule but no "
                        "confirmed per-serving or per-package limit.", "La. R.S. 40:1046"),
    "MA": F("5 mg of THC per serving and 100 mg per package (5.5 mg and 110 mg with the allowed 10% "
            "variance), and no more than 20 servings a package.", "935 CMR 500.150(4)",
            "https://masscannabiscontrol.com/document/935-cmr-500-000-adult-use-of-marijuana-effective-06-18-26-pdf-2/"),
    "MD": F("Adult use: no more than 10 mg of THC per serving and 100 mg per package. Higher-potency products "
            "are for patients only.", "COMAR 14.17.13.05", "https://cannabis.maryland.gov/Pages/law.aspx"),
    "ME": F("No more than 10 mg of THC per serving and 200 mg per package.", "28-B M.R.S. §703(1)(F)",
            "https://www.mainelegislature.org/LEGIS/STATUTES/28-B/title28-Bsec703.pdf"),
    "MI": NOT_CONFIRMED("The report takes Michigan's edible limits from a secondary reproduction of a CRA "
                        "bulletin, and its sources conflict on the medical limits."),
    "MN": NOT_CONFIRMED("The report's per-serving and per-package figures are for lower-potency hemp edibles; "
                        "it does not give the limits for adult-use cannabis edibles.", "Minn. Stat. ch. 342"),
    "MO": NOT_CONFIRMED("The report found no general per-serving or per-package edible limit in Article XIV or "
                        "19 CSR 100-1.120 as read, and rejects the 10 mg / 100 mg figures in secondary sources.",
                        "19 CSR 100-1.120"),
    "MS": F("No more than 10 mg of THC per serving (within ±10%).", "MSDH Medical Cannabis Program rules",
            "https://www.mmcp.ms.gov/sites/default/files/Documents/RevisedAdminRegulationsMMCPBOHADOPTED10.11.2023.pdf"),
    "MT": NOT_CONFIRMED("The report's figures (5 mg per serving from 1 July 2026 under HB 636; 100 mg per "
                        "package) are among the sections it lists as not yet opened in official text.",
                        "MCA §16-12-224"),
    "ND": F("Only low-dose lozenges, soft or hard and square in shape: no more than 5 mg of THC per serving "
            "and 50 mg per package, with the Department's prior approval. Other THC foods and drinks are not "
            "allowed.", "N.D.C.C. §19-24.1-24.1 (HB 1203, 2025)", "https://www.legis.nd.gov/cencode/t19c24-1.pdf"),
    "NE": NOT_CONFIRMED("No dispensary had been licensed as of 30 Oct 2026, and the report gives no confirmed "
                        "product rules for edibles.", "Neb. Rev. Stat. §71-24,104"),
    "NH": NOT_CONFIRMED("The report found no edible limit in New Hampshire law; the figures in search results "
                        "come from failed adult-use bills."),
    "NJ": F("No more than 10 mg of THC per serving and 100 mg per package.", "N.J.A.C. 17:30",
            "http://www.state.nj.us/cannabis/documents/businesses/Business%20Resources/Labeling%20of%20Total%20Active%20THC%20for%20Ingestibles%20Guidance%20.pdf"),
    "NM": F("Adult use: no more than 10 mg of total THC per serving and 100 mg per container. Medical edibles "
            "may have up to 50 mg per serving.", "16.8.3.12 NMAC",
            "https://www.srca.nm.gov/nmac/nmregister/xxxiii/16.8.3_xxxiii01.pdf"),
    "NV": F("No more than 10 mg of THC per serving and 100 mg per package.", "NRS 678D.420(1), (2)(e)",
            "https://www.leg.state.nv.us/NRS/NRS-678D.html", note=CHK),
    "NY": F("No more than 10 mg of THC per serving.", "9 NYCRR Part 128",
            "https://cannabis.ny.gov/part-128-guidance",
            note="A 100 mg per package limit is reported only by secondary sources so far."),
    "OH": NOT_CONFIRMED("The report gives limits for medical product forms (oral drops, patches and others) "
                        "but not for adult-use edibles."),
    "OK": F("No per-serving or per-package THC limit. From 1 Nov 2026, packages must state the servings and the "
            "THC per serving, and edibles may not be attractive to children, shaped like a person, animal or "
            "cartoon, or resemble commercial candy.", "63 O.S. §423(C)(7) (HB 4454)",
            "https://oklahoma.gov/omma/about/news/2026/hb-4454-clarification-processor-and-dispensary-requirements.html"),
    "OR": F("Adult use: no more than 10 mg of THC per serving and 100 mg per package (since 1 Apr 2022). "
            "Medical-grade edibles: up to 100 mg per package, with no serving-size rule.",
            "OAR 845-026-0210, -0220",
            "http://cms.oregon.gov/olcc/marijuana/Documents/Bulletins/IB2022-01-Potency-Limits-Edibles.pdf"),
    "PA": F("No commercial edibles: making medical marijuana into an edible is unlawful, except a patient or "
            "caregiver mixing it into food to help take it.", "Medical Marijuana Act §304",
            "https://www.legis.state.pa.us/WU01/LI/LI/US/HTM/2016/0/0016..HTM"),
    "RI": F("No more than 10 mg of THC per serving and 100 mg per package; some designated medical products "
            "may exceed these.", "560-RICR-10-10-2", "https://ccc.ri.gov/media/2311/download?language=en"),
    "SD": F("No more than 50 mg of THC per serving, under the 2023 rules.", "ARSD 44:90:07:04",
            "https://rules.sd.gov/Uploads/782_AdoptedRules.pdf",
            note="A labelling rule (44:90:10:12) still refers to 10 mg servings; the report flags the "
                 "conflict."),
    "TX": F("Low-THC products only, which may include edibles: no more than 10 mg of THC per dose and 1 g per "
            "package.", "HB 46 (2025)", "https://capitol.texas.gov/tlodocs/89R/analysis/html/HB00046E.htm"),
    "UT": NOT_CONFIRMED("The report gives no confirmed per-serving or per-package limit for Utah's medical "
                        "edible products."),
    "VA": F("No adult-use sales are licensed. Medical products: no more than 10 mg of THC per dose, except as "
            "§4.1-1603.2 allows.", "Va. Code §4.1-1602", "https://law.lis.virginia.gov/vacode/4.1-1602/"),
    "VT": F("No more than 5 mg of THC per serving and 100 mg per package, in opaque, child-resistant "
            "packaging with the standard symbol.", "7 V.S.A. §881(a)(3)",
            "https://legislature.vermont.gov/statutes/section/07/033/00881"),
    "WA": F("No more than 10 mg of active THC per serving and 100 mg per package, at most 10 servings. Some "
            "patient-only products (capsules, tinctures and similar, not edibles) may have up to 50 mg per "
            "serving.", "WAC 314-55-095", "https://lcb.wa.gov/education2cb/reading_a_product_label"),
    "WV": NOT_CONFIRMED("The report found no statutory per-serving or per-package limit; any limit would be in "
                        "the bureau's rules or product approvals, which it did not confirm.", "W. Va. Code ch. 16A"),
    "ID": F(NO_MARKET, 'Idaho Code §37-2701 et seq.', 'https://legislature.idaho.gov/statutesrules/idstat/Title37/T37CH27/SECT37-2701', note=HEMP),
    "IN": F(NO_MARKET, 'Ind. Code art. 35-48 (marijuana now defined at IC 35-48-1.1-29)', 'https://public.courts.in.gov/Decisions/api/Document/Opinion?Id=DmYIl2h3bOKWWdQQvJyPZ_rjZgo14Y_LmDtP2-HSBr7Uf3wsJD127SUP1Lq0Mzh20', note=HEMP),
    "KS": F(NO_MARKET, 'K.S.A. 65-4101(aa) and 21-5706', 'https://kslegislature.gov/li_2022/b2021_22/statute/065_000_0000_chapter/065_041_0000_article/065_041_0001_section/065_041_0001_k/', note=HEMP),
    "NC": F(NO_MARKET, 'N.C.G.S. 90-87(16), 90-94 (Schedule VI), 90-95', 'https://ncleg.gov/EnactedLegislation/SessionLaws/HTML/2021-2022/SL2022-32.html', note=HEMP),
    "SC": F(NO_MARKET, 'S.C. Code §44-53-110(27), §44-53-370', 'https://www.scstatehouse.gov/code/t44c053.php', note=HEMP),
    "TN": F(NO_MARKET, 'Tenn. Code §39-17-402(16) and Schedule VI', '', note=NO_LINK),
    "WI": F(NO_MARKET, 'Wis. Stat. ch. 961 (§961.41', 'https://docs.legis.wisconsin.gov/document/acts/2019/68,54n', note=HEMP),
    "WY": F(NO_MARKET, 'Wyoming Controlled Substances Act, W.S. 35-7-1001 et seq. (35-7-1031(c))', '', note=NO_LINK),
}

for _code, _fact in EDIBLES.items():
    QUICK[_code]["edibles"] = _fact
