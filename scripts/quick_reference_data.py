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

FIELDS = ["possession", "home_grow", "state_tax", "regulator"]


def F(text, cite, url, confirmed=True, note=""):
    return {"text": text, "cite": cite, "url": url, "confirmed": confirmed, "note": note}


def NOT_CONFIRMED(why, cite="", url=""):
    return F(None, cite, url, confirmed=False, note=why)


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
                        "16 Del.C. §4701", "https://omc.delaware.gov/adult-use/",
                        note="Registered medical patients may possess up to 6 oz of usable marijuana (16 Del.C. §4903A)."),
        "home_grow": F("Not allowed, for adults or for medical patients and caregivers.",
                       "16 Del.C. §4764A(c)", "https://omc.delaware.gov/adult-use/"),
        "state_tax": F("15% of the retail price on adult-use sales; medical sales are exempt. "
                       "From 21 Oct 2026 infused beverages pay a per-container tax instead.",
                       "4 Del.C. §1382", "https://revenue.delaware.gov/marijuana-establishments-and-retail-tax-faqs/"),
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
                        "total THC per 90 days (more by waiver). Marijuana is not legal in any amount.",
                        "Iowa Code §124E.9(14)-(15); §124.401(5)",
                        "https://www.legis.iowa.gov/docs/code/2024/124E.pdf"),
        "home_grow": F("Not allowed, including for patients.", "Iowa Code ch. 124E",
                       "https://www.legis.iowa.gov/docs/code/2024/124E.pdf"),
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
                        "(1 MMCEU is 3.5 g of flower). Visiting cardholders: 14. For anyone else, "
                        "30 g or less on a first conviction is a fine only; it is not legal.",
                        "Mississippi Medical Cannabis Act (SB 2095, 2022); Miss. Code §41-29-139(c)", "https://www.mmcp.ms.gov/"),
        "home_grow": F("Not allowed, including for patients.", "Miss. Code §41-137-1 et seq.",
                       "https://www.mmcp.ms.gov/"),
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
        "state_tax": F("15% wholesale excise on the first wholesale sale (medical and adult use), "
                       "and a 10% retail excise on adult-use sales, on top of sales tax (at least "
                       "6.85%). Medical sales are exempt from the 10%.", "NRS 372A.290",
                       "https://www.leg.state.nv.us/NRS/NRS-372A.html"),
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
                        "NMSA §26-2C-25(A)", "https://www.rld.nm.gov/cannabis/cannabis-in-new-mexico/adult-use/"),
        "home_grow": F("6 mature and 6 immature plants per adult; no more than 12 mature plants "
                       "per household.", "NMSA §26-2C-25(A)(9)",
                       "https://www.rld.nm.gov/cannabis/cannabis-in-new-mexico/adult-use/personal-use-of-cannabis/"),
        "state_tax": F("Cannabis excise: 14% from 1 July 2026 (13% the year before), rising one "
                       "point each 1 July to 18% in 2030. Medical sales to patients are exempt.",
                       "NMSA §7-42-3(B)-(C)", "https://www.rld.nm.gov/cannabis/compliance/tax-reporting/"),
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
        "home_grow": F("Not allowed: growing is \"production\", charged as manufacture.",
                       "Tenn. Code §§39-17-402(24), 39-17-417", "",
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
        "possession": F("Not legal. Up to 3 oz of plant form is a misdemeanor; more is a felony.",
                        "W.S. 35-7-1031(c)(i)", "",
                        note="The audited report cites the Wyoming statutes, but no official link for "
                             "them was captured."),
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
