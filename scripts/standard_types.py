#!/usr/bin/env python3
"""The 16 standard licence types, and the mapping from each regulator's own
vocabulary onto them. One source of truth, imported by add_standard_type.py
and by verify.py so the check and the write can never drift apart.

CLAUDE.md: "Show the state's own licence name on state pages; use the standard
type for search." So `licence_type` keeps the regulator's own official name and
`category` keeps the build's own grouping; `standard_type` is the one value a
single search can span all 51 jurisdictions with. Nothing here rewrites either
of the first two.

Two columns come out of this, for the reason HANDOFF gives when it allows
multiple activity tags:

  standard_type       exactly one of the 16 - the LEAD activity, so a facet
                      has one value per licence and counts cannot double.
  standard_types_all  every one of the 16 the licence authorises, ';'-joined
                      in CANONICAL (HANDOFF) order, so the same combination
                      always reads the same way whatever order the regulator
                      happened to list it in. Always populated; equal to
                      standard_type for the 50,397 single-activity rows.

The lead is picked by the fixed precedence in LEAD_ORDER, most downstream
(most consumer-facing) first, NOT by the order the source wrote. Source order
cannot be the rule because the same NJ combination arrives as "Cultivation;
Manufacturing; Retail Store", as "Retail Store; Cultivation" and as
"Dispensing, Cultivating" - keying on it would scatter one real combination
across three different leads. Downstream-first means a person searching for
somewhere that can sell to them finds every licence that may.

This is a derived column. The three builders do not write it, so it must be
re-applied after any rebuild - verify.py fails loudly if it is missing, which
is the guard against a rebuild silently dropping it.
"""

# HANDOFF.md, "Standard types (16)" - in HANDOFF's own order, which is also the
# canonical order standard_types_all is written in.
STANDARD_TYPES = [
    "Cultivation", "Nursery", "Manufacturing", "Retail", "Delivery",
    "Transport & Distribution", "Testing Lab", "Microbusiness",
    "Consumption Lounge", "Research", "Caregiver", "Event Organizer",
    "Operator", "Hemp Grower", "Hemp Processor", "Hemp Retail",
]

# Most downstream first. Only the types that actually appear in a compound
# need an opinion; the rest are listed so the order is total and a future
# compound cannot fall off the end.
LEAD_ORDER = [
    "Retail", "Consumption Lounge", "Delivery", "Transport & Distribution",
    "Hemp Retail", "Manufacturing", "Hemp Processor", "Cultivation",
    "Hemp Grower", "Nursery", "Microbusiness", "Operator", "Event Organizer",
    "Testing Lab", "Research", "Caregiver",
]

# Every `category` value in the three tables -> the standard types it carries.
# Keyed on category because all 177 distinct licence_type values (179
# category x licence_type pairs) were checked against it and none contradicts
# its own category; where a category name does
# not itself say what the licence authorises (Integrated, Compassion Center
# (Hybrid), Industrial Hemp Dual) the activities come from the state's own
# audited report, cited in HANDOFF.md.
CATEGORY_TO_TYPES = {
    # --- category name already is a standard type -------------------------
    "Cultivation": ["Cultivation"],
    "Nursery": ["Nursery"],
    "Manufacturing": ["Manufacturing"],
    "Delivery": ["Delivery"],
    "Transport & Distribution": ["Transport & Distribution"],
    "Testing Lab": ["Testing Lab"],
    "Microbusiness": ["Microbusiness"],
    "Consumption Lounge": ["Consumption Lounge"],
    "Research": ["Research"],
    "Event Organizer": ["Event Organizer"],
    "Operator": ["Operator"],
    "Hemp Grower": ["Hemp Grower"],
    "Hemp Processor": ["Hemp Processor"],
    "Hemp Retail": ["Hemp Retail"],

    # --- renamed to HANDOFF's standard spelling ---------------------------
    # HANDOFF's name is "Retail", not "Retail Store".
    "Retail Store": ["Retail"],
    # HANDOFF's name is "Caregiver"; ME's own word stays in licence_type
    # ("Registered Caregiver") and the medical programme in `program`.
    "Medical Caregiver": ["Caregiver"],
    # Near-duplicate of "Hemp Retail" (178 rows against 12,396). RI's
    # CBD/Hemp-Derived Consumable Retailer and CT's Moderate-THC Hemp Product
    # Vendor are both hemp retail; the two spellings are one type.
    "Hemp Retailer": ["Hemp Retail"],

    # --- medical/adult-use is a separate filter, never a separate type ----
    # HANDOFF: "Medical vs adult-use is a separate filter." A dispensary is
    # retail; `program` already carries Medical / Adult Use / both.
    "Medical Dispensary": ["Retail"],
    # CT: program is "Adult Use; Medical" on every row. A hybrid retailer
    # sells to both patients and adult-use customers - CT's hybrid retailers
    # are where the first adult-use sales happened (CT report, Part 0) - and
    # does nothing else. "Hybrid" is the programme pair, not an extra activity.
    "Hybrid Retailer": ["Retail"],

    # --- a smaller licence of the same activity ---------------------------
    # CT §21a-420: (16) cultivator needs "not less than fifteen thousand
    # square feet of grow space"; (39) micro-cultivator "not less than two
    # thousand ... not more than ten thousand". Same activity, smaller cap -
    # so Cultivation, NOT Microbusiness. A microbusiness (CA, NY, MA) covers
    # several activities under one licence; a CT micro-cultivator only grows.
    # Folding them together would merge two genuinely different things.
    "Micro-Cultivation": ["Cultivation"],

    # --- hemp-side manufacture is Hemp Processor ---------------------------
    # CT "Manufacturer Of Hemp Consumables", program Hemp. The same activity
    # as TX's "Consumable Hemp Product" licence, which this table already
    # categorises Hemp Processor - so the in-table precedent decides it.
    "Hemp Manufacturer": ["Hemp Processor"],
    # CT "Manufacturer Of Thc-Infused Beverages", program Hemp: hemp
    # manufacture specialised to one product. The product is in licence_type.
    "THC Beverage Manufacturer": ["Hemp Processor"],
    # RI § 1.6 grower/handler, with extraction at § 1.12. A handler
    # processes. OR's "Hemp Handler Certificate" is already Hemp Processor in
    # this table, so RI's handler reads the same way.
    "Hemp Handler": ["Hemp Processor"],

    # --- distribution is distribution, in either programme -----------------
    # CT "Cannabis Product Packager". HANDOFF lists Packaging as one of the
    # Manufacturing activity tags, so a packager is a manufacturer.
    "Packager": ["Manufacturing"],
    # VT "Wholesaler" - a cannabis wholesaler moves product to licensees.
    "Wholesaler": ["Transport & Distribution"],
    # MA/CT standalone transporters.
    "Transporter": ["Transport & Distribution"],
    # RI "CBD/Hemp-Derived Consumable Distributor" and CT "Wholesaler Of
    # Thc-Infused Beverages", both program Hemp. They sell to retailers, not
    # to the public, so they are not Hemp Retail; there is no hemp-specific
    # distribution type among the 16 and distribution is what they do.
    # `program` = Hemp keeps them separable from cannabis distributors.
    # (RI's own rule pairs § 1.7 distributor/retailer in one fee class; the
    # standard type tracks the activity, not the fee schedule.)
    "Hemp Distributor": ["Transport & Distribution"],
    "THC Beverage Wholesaler": ["Transport & Distribution"],

    # --- genuinely multi-activity: a tag list, lead by LEAD_ORDER ----------
    # NJ: the CRC's own compound class wording, in all the orders it uses.
    "Cultivation; Manufacturing; Retail Store": ["Cultivation", "Manufacturing", "Retail"],
    "Cultivation; Manufacturing": ["Cultivation", "Manufacturing"],
    "Manufacturing; Cultivation": ["Cultivation", "Manufacturing"],
    "Cultivation; Retail Store": ["Cultivation", "Retail"],
    "Retail Store; Cultivation": ["Cultivation", "Retail"],
    "Manufacturing; Retail Store": ["Manufacturing", "Retail"],
    "Retail Store; Consumption Lounge": ["Retail", "Consumption Lounge"],
    # RI "Industrial Hemp Dual" - grower and handler in one licence.
    "Hemp Grower/Handler": ["Hemp Grower", "Hemp Processor"],
    # RI compassion centre. RI report, Part 11 (§ 21-28.6-12; 560-10-10-1
    # § 1.8): "medical retail + cultivation/manufacture for patients;
    # vertically integrated". "(Hybrid)" is § 1.9 adult-use sales added on
    # top - the programme pair, already in `program`.
    "Compassion Center (Hybrid)": ["Cultivation", "Manufacturing", "Retail"],
    # VT integrated licensee. VT report: § 971(b)(1) "operate vertically
    # integrated under one license", § 973(a) cultivate/package/label/
    # test/transport and produce products, and the CCB Municipal FAQ speaks
    # of "the retail portion of an integrated license". NB the licence was
    # repealed 1 July 2026 by Act 176 § 909 - the 2 rows are legacy.
    "Integrated": ["Cultivation", "Manufacturing", "Retail"],
}


def types_for(category, licence_type=""):
    """Return (lead, all_types) for a row, or (None, None) if unmapped.

    Unmapped is returned rather than guessed: a new category must be a
    decision recorded in HANDOFF.md, not a silent blank or a near-miss.
    """
    types = CATEGORY_TO_TYPES.get(category)
    if not types:
        return None, None
    ordered = [t for t in STANDARD_TYPES if t in types]
    lead = next(t for t in LEAD_ORDER if t in types)
    return lead, "; ".join(ordered)
