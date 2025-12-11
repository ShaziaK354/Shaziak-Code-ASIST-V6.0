"""
SAMM Chapter 4 Entity Implementation
=====================================

Chapter 4: Foreign Military Sales (FMS) Program General Information

This module contains:
1. Chapter 4 Ground Truth Entities
2. Chapter 4 Specific Acronym Pairs
3. Chapter 4 Entity Patterns
4. Chapter 4 Entity Relationships
5. Chapter 4 Test Cases
"""

# =============================================================================
# CHAPTER 4 SPECIFIC ACRONYM PAIRS (NEW - Not in Chapter 1)
# =============================================================================
CHAPTER_4_ACRONYM_PAIRS = {
    # DSCA Office Acronyms
    "spp": "strategy, plans, and policy",
    "iops": "international operations",
    "iops/rex": "international operations regional execution directorate",
    "iops/wpn": "international operations weapons directorate", 
    "iops/wpns": "international operations weapons directorate",
    "fo/ogc": "front office office of general counsel",
    "adm/pie": "office of administration performance improvement and effectiveness directorate",
    "adm/pie/ame": "assessment monitoring and evaluation division",
    
    # State Department Offices
    "pm/rsat": "bureau of political-military affairs office of regional security and arms transfers",
    "pm": "bureau of political-military affairs",
    "ddtc": "directorate of defense trade controls",
    "state(pm)": "department of state bureau of political-military affairs",
    "state(ddtc)": "department of state directorate of defense trade controls",
    
    # Programs & Processes
    "tpa": "total package approach",
    "eum": "end use monitoring",
    "eeum": "enhanced end use monitoring",
    "p&a": "price and availability",
    "par": "pre-lor assessment request",
    "cn": "congressional notification",
    "rdfp": "regional defense fellowship program",
    "fms-only": "foreign military sales only",
    
    # Legal/Regulatory
    "ndp": "national disclosure policy",
    "ndp-1": "national disclosure policy 1",
    "jtr": "joint travel regulations",
    "eo 13526": "executive order 13526",
    "dodd 4270.5": "department of defense directive 4270.5",
    "dodd 5230.20": "department of defense directive 5230.20",
    "dodi 2010.06": "department of defense instruction 2010.06",
    "dodi 5530.03": "department of defense instruction 5530.03",
    "dodm 5200.01": "department of defense manual 5200.01",
    
    # Defense Equipment/Items
    "sme": "significant military equipment",
    "mde": "major defense equipment",
    "gfe": "government furnished equipment",
    "gfm": "government furnished materiel",
    "nvd": "night vision device",
    "nvds": "night vision devices",
    "manpads": "man-portable air defense system",
    "comsec": "communications security",
    "infosec": "information security",
    "tdp": "technical data package",
    
    # Intelligence/Targeting
    "geoint": "geospatial intelligence",
    "c4isr": "command control communications computer intelligence surveillance and reconnaissance",
    "atd": "advanced target development",
    "tcm": "target coordinate mensuration",
    "ppm": "precision point mensuration",
    "cde": "collateral damage estimation",
    "cer": "collateral effects radii",
    "pdt": "population density tables",
    "diee": "digital imagery exploitation engine",
    "etd": "enhanced targeting data",
    "pklut": "probability of kill look up tool",
    "fom": "figure of merit",
    
    # Technology/Systems
    "aesa": "active electronically scanned array",
    "ladar": "laser detection and ranging",
    "lidar": "light detection and ranging",
    "gps": "global positioning system",
    "pps": "pulse per second",
    "iff": "identification friend or foe",
    "a/s": "air to surface",
    "s/s": "surface to surface",
    
    # Organizations (new)
    "aflcmc": "air force life cycle management center",
    "jtcg/me": "joint technical coordinating group for munitions effectiveness",
    "jts": "joint targeting school",
    "asd(so/lic)": "assistant secretary of defense for special operations and low-intensity conflict",
    "so/lic": "special operations low-intensity conflict",
    "asd(hd&gs/cwmd)": "assistant secretary of defense for homeland defense and global security countering weapons of mass destruction",
    "hd&gs/cwmd": "homeland defense and global security countering weapons of mass destruction",
    "usn": "united states navy",
    "gsa": "general services administration",
    "iaea": "international atomic energy agency",
    "un": "united nations",
    
    # Other Chapter 4 Terms
    "tla": "travel and living allowance",
    "ims": "international military student",
    "ncr": "nonrecurring cost recoupment",
    "sc-tms": "security cooperation training management system",
    "masl": "military articles and services list",
    "cta": "country team assessment",
    "qw": "quick weaponeering",
    "niprnet": "non-classified internet protocol router network",
}

# =============================================================================
# CHAPTER 4 GROUND TRUTH ENTITIES
# =============================================================================
CHAPTER_4_GROUND_TRUTH = {
    # Organizations (C4.1 - C4.5)
    "organizations": {
        # DSCA Offices
        "DSCA", "Defense Security Cooperation Agency",
        "DSCA SPP", "DSCA (SPP)", "Office of Strategy, Plans, and Policy",
        "DSCA IOPS", "DSCA (IOPS)", "Office of International Operations",
        "DSCA IOPS/REX", "IOPS/REX", "Regional Execution Directorate",
        "DSCA IOPS/WPN", "IOPS/WPN", "IOPS/WPNS", "Weapons Directorate",
        "DSCA FO/OGC", "FO/OGC", "Office of the General Counsel",
        "DSCA ADM/PIE", "ADM/PIE",
        
        # State Department
        "DoS", "State", "Department of State",
        "State PM", "State(PM)", "Bureau of Political-Military Affairs",
        "PM/RSAT", "State(PM/RSAT)", "Office of Regional Security and Arms Transfers",
        "DDTC", "State(DDTC)", "Directorate of Defense Trade Controls",
        
        # DoD Components
        "DoD", "Department of Defense",
        "OUSD(P)", "USD(P)", "Under Secretary of Defense for Policy",
        "OUSD(A&S)", "USD(A&S)", "Under Secretary of Defense for Acquisition and Sustainment",
        "DTSA", "Defense Technology Security Administration",
        "NGA", "National Geospatial-Intelligence Agency",
        "DIA", "Defense Intelligence Agency",
        
        # Military Departments
        "MILDEP", "MILDEPS", "Military Department",
        "USN", "U.S. Navy", "United States Navy",
        "USACE", "U.S. Army Corps of Engineers",
        "AFLCMC", "Air Force Life Cycle Management Center",
        
        # Other Organizations
        "DOC", "Department of Commerce",
        "GSA", "General Services Administration",
        "SCO", "SCOS", "Security Cooperation Organization",
        "IA", "IAS", "Implementing Agency",
        "CCMD", "CCMDS", "Combatant Command",
        "CCDR", "Combatant Commander",
        "NATO", "North Atlantic Treaty Organization",
        "UN", "United Nations",
        "IAEA", "International Atomic Energy Agency",
        "JTCG/ME", "Joint Technical Coordinating Group for Munitions Effectiveness",
        "JTS", "Joint Targeting School",
        "ASD(SO/LIC)", "SO/LIC",
        "ASD(HD&GS/CWMD)",
    },
    
    # Programs (C4.1 - C4.5)
    "programs": {
        "FMS", "Foreign Military Sales",
        "DCS", "Direct Commercial Sales",
        "BPC", "Building Partner Capacity",
        "EDA", "Excess Defense Articles",
        "FMF", "Foreign Military Financing",
        "MAP", "Military Assistance Program",
        "SA", "Security Assistance",
        "SC", "Security Cooperation",
        "IMET", "International Military Education and Training",
        "TPA", "Total Package Approach",
        "EUM", "End Use Monitoring",
        "EEUM", "Enhanced End Use Monitoring",
        "RDFP", "Regional Defense Fellowship Program",
        "FMS-Only",
    },
    
    # Authorities/Legal (C4.1 - C4.5)
    "authorities": {
        "AECA", "Arms Export Control Act",
        "FAA", "Foreign Assistance Act",
        "USML", "United States Munitions List", "U.S. Munitions List",
        "FAR", "Federal Acquisition Regulation",
        "DFARS", "Defense Federal Acquisition Regulation Supplement",
        "NDP", "National Disclosure Policy",
        "NDP-1",
        "JTR", "Joint Travel Regulations",
        "EO 13526", "Executive Order 13526",
        "PD", "Presidential Determination",
        "10 U.S.C.", "Title 10",
        "22 U.S.C.", "Title 22",
        "22 CFR part 121",
    },
    
    # Documents (C4.1 - C4.5)
    "documents": {
        "LOA", "Letter of Offer and Acceptance",
        "LOR", "Letter of Request",
        "P&A", "Price and Availability",
        "PAR", "Pre-LOR Assessment Request",
        "TDP", "Technical Data Package",
        "CN", "Congressional Notification",
        "DoDI 2010.06", "DoDI 5530.03",
        "DoDD 4270.5", "DoDD 5230.20",
        "DoDM 5200.01",
        "MASL", "Military Articles and Services List",
    },
    
    # Concepts (C4.1 - C4.5)
    "concepts": {
        # Eligibility Concepts
        "eligibility", "eligible", "eligibility determination",
        "Presidential Determination", "eligibility criteria",
        "retransfer", "retransfer restrictions",
        "third party transfer", "end use",
        
        # Sales Concepts
        "FMS-Only", "DCS preference", "concurrent negotiations",
        "international competition", "sole source",
        "total package approach", "TPA",
        
        # Equipment Categories
        "defense articles", "defense services",
        "SME", "Significant Military Equipment",
        "MDE", "Major Defense Equipment",
        "GFE", "Government Furnished Equipment",
        "GFM", "Government Furnished Materiel",
        
        # Targeting/Intelligence
        "GEOINT", "Geospatial Intelligence",
        "C4ISR", "ATD", "Advanced Target Development",
        "TCM", "Target Coordinate Mensuration",
        "CDE", "Collateral Damage Estimation",
        "weaponeering",
        
        # Security
        "COMSEC", "Communications Security",
        "INFOSEC", "Information Security",
        "classification", "CONFIDENTIAL",
        
        # Specific Items
        "NVD", "Night Vision Device",
        "MANPADS", "Stinger",
        "cluster munitions", "white phosphorus",
        "depleted uranium", "napalm",
        "coproduction",
    },
    
    # Sections (Chapter 4 specific)
    "sections": {
        "C4.1", "C4.1.1", "C4.1.2", "C4.1.3",
        "C4.2", "C4.2.1", "C4.2.2", "C4.2.3", "C4.2.4",
        "C4.3", "C4.3.1", "C4.3.2", "C4.3.3", "C4.3.4", "C4.3.5", "C4.3.6", "C4.3.7",
        "C4.4", "C4.4.1", "C4.4.2", "C4.4.3", "C4.4.4", "C4.4.5", "C4.4.6", "C4.4.7",
        "C4.4.8", "C4.4.9", "C4.4.10", "C4.4.11", "C4.4.12", "C4.4.13", "C4.4.14",
        "C4.4.15", "C4.4.16", "C4.4.17", "C4.4.18", "C4.4.19",
        "C4.5", "C4.5.1", "C4.5.2", "C4.5.3", "C4.5.4", "C4.5.5", "C4.5.6", "C4.5.7",
    }
}

# =============================================================================
# CHAPTER 4 ENTITY PATTERNS (for IntegratedEntityAgent.samm_entity_patterns)
# =============================================================================
CHAPTER_4_ENTITY_PATTERNS = {
    "organizations": [
        # DSCA Offices
        "DSCA", "Defense Security Cooperation Agency",
        "DSCA SPP", "DSCA (SPP)", "Office of Strategy, Plans, and Policy",
        "DSCA IOPS", "DSCA (IOPS)", "Office of International Operations",
        "IOPS/REX", "Regional Execution Directorate",
        "IOPS/WPN", "IOPS/WPNS", "Weapons Directorate",
        "FO/OGC", "Office of the General Counsel",
        "ADM/PIE",
        # State Offices
        "State PM", "State(PM)", "PM", "Bureau of Political-Military Affairs",
        "PM/RSAT", "Office of Regional Security and Arms Transfers",
        "DDTC", "Directorate of Defense Trade Controls",
        # Defense Agencies
        "DTSA", "Defense Technology Security Administration",
        "NGA", "National Geospatial-Intelligence Agency",
        "DIA", "Defense Intelligence Agency",
        "DOC", "Department of Commerce",
        # Other
        "AFLCMC", "Air Force Life Cycle Management Center",
        "JTCG/ME", "Joint Technical Coordinating Group for Munitions Effectiveness",
        "JTS", "Joint Targeting School",
        "USN", "U.S. Navy",
        "GSA", "General Services Administration",
        "NATO", "IAEA", "UN",
        "ASD(SO/LIC)", "SO/LIC",
        "ASD(HD&GS/CWMD)",
    ],
    "programs": [
        "FMS", "Foreign Military Sales",
        "DCS", "Direct Commercial Sales",
        "FMS-Only", "Total Package Approach", "TPA",
        "EUM", "End Use Monitoring",
        "EEUM", "Enhanced End Use Monitoring",
        "BPC", "Building Partner Capacity",
        "RDFP", "Regional Defense Fellowship Program",
        "coproduction", "co-production",
    ],
    "authorities": [
        "AECA", "Arms Export Control Act",
        "FAA", "Foreign Assistance Act",
        "USML", "United States Munitions List", "U.S. Munitions List",
        "FAR", "Federal Acquisition Regulation",
        "DFARS", "Defense Federal Acquisition Regulation Supplement",
        "NDP", "National Disclosure Policy", "NDP-1",
        "JTR", "Joint Travel Regulations",
        "EO 13526", "Executive Order 13526",
        "Presidential Determination", "PD",
    ],
    "concepts": [
        # Eligibility
        "eligibility", "eligible", "eligibility determination",
        "retransfer", "third party transfer", "end use",
        # Equipment
        "SME", "Significant Military Equipment",
        "MDE", "Major Defense Equipment",
        "GFE", "Government Furnished Equipment",
        "GFM", "Government Furnished Materiel",
        "defense articles", "defense services",
        # Targeting
        "GEOINT", "Geospatial Intelligence",
        "C4ISR",
        "ATD", "Advanced Target Development",
        "TCM", "Target Coordinate Mensuration",
        "CDE", "Collateral Damage Estimation",
        "weaponeering",
        # Security
        "COMSEC", "Communications Security",
        "INFOSEC", "Information Security",
        # Items
        "NVD", "Night Vision Device", "NVDs",
        "MANPADS", "Stinger",
        "cluster munitions",
        "white phosphorus",
    ],
    "documents": [
        "LOA", "Letter of Offer and Acceptance",
        "LOR", "Letter of Request",
        "P&A", "Price and Availability",
        "PAR", "Pre-LOR Assessment Request",
        "TDP", "Technical Data Package",
        "CN", "Congressional Notification",
        "MASL", "Military Articles and Services List",
    ]
}

# =============================================================================
# CHAPTER 4 ENTITY RELATIONSHIPS
# =============================================================================
CHAPTER_4_ENTITY_RELATIONSHIPS = {
    # Eligibility relationships (C4.1)
    "Presidential Determination": ["determines FMS eligibility", "authorizes sales"],
    "Secretary of State": ["determines sales", "approves retransfers", "supervises FMS"],
    "DSCA SPP": ["handles eligibility questions", "issues DCS preferences"],
    "DSCA IOPS": ["handles eligibility changes", "coordinates FMS-Only designations", "approves MANPADS discussions"],
    
    # Sales process relationships (C4.2, C4.3)
    "FMS": ["transfers defense articles", "transfers defense services", "government-to-government sales"],
    "DCS": ["Direct Commercial Sales", "alternative to FMS", "commercial contracts"],
    "FMS-Only": ["designated by State", "requires FMS channel", "sensitive items"],
    "TPA": ["Total Package Approach", "ensures sustainability", "includes training and support"],
    
    # Equipment relationships (C4.4)
    "SME": ["Significant Military Equipment", "on USML", "asterisk designation"],
    "MDE": ["Major Defense Equipment", "over $50M R&D or $200M production", "SME subset"],
    "USML": ["designates defense articles", "lists SME", "22 CFR part 121"],
    "NVD": ["requires case-by-case review", "DTSA policy", "EUM requirements"],
    "MANPADS": ["requires DSCA approval", "Stinger systems", "special controls"],
    
    # Targeting relationships (C4.4.18)
    "ATD": ["Advanced Target Development", "includes TCM, weaponeering, CDE"],
    "TCM": ["Target Coordinate Mensuration", "generates precise coordinates"],
    "CDE": ["Collateral Damage Estimation", "assesses civilian risk"],
    "GEOINT": ["from NGA", "supports targeting", "mission data"],
    "DIEE": ["default targeting solution", "managed by AFLCMC"],
    
    # Restricted items relationships (C4.5)
    "cluster munitions": ["restricted", "99% functioning rate required"],
    "MANPADS": ["requires DSCA approval", "special controls"],
    "white phosphorus": ["requires DSCA coordination", "special conditions"],
}

# =============================================================================
# CHAPTER 4 TEST CASES (Realistic expectations - includes valid expansions)
# =============================================================================
TEST_CASES_CHAPTER_4 = {
    # Pattern 1: FMS Eligibility Queries
    "pattern_c4_1_eligibility": {
        "description": "FMS eligibility and Presidential Determination queries",
        "tests": [
            {"id": 101, "query": "What determines FMS eligibility?", 
             "expected": ["fms", "eligibility", "foreign military sales"]},
            {"id": 102, "query": "How does a country become eligible for FMS?",
             "expected": ["fms", "eligibility", "foreign military sales"]},
            {"id": 103, "query": "What is a Presidential Determination?",
             "expected": ["presidential determination"]},
            {"id": 104, "query": "What can cause a country to lose FMS eligibility?",
             "expected": ["fms", "eligibility", "foreign military sales"]},
            {"id": 105, "query": "Who handles FMS eligibility questions at DSCA SPP?",
             "expected": ["fms", "eligibility", "dsca", "spp", "dsca spp", 
                         "foreign military sales", "defense security cooperation agency", 
                         "strategy plans and policy"]},
        ]
    },
    
    # Pattern 2: FMS vs DCS Queries
    "pattern_c4_2_fms_dcs": {
        "description": "FMS vs Direct Commercial Sales queries",
        "tests": [
            {"id": 106, "query": "What is the difference between FMS and DCS?",
             "expected": ["fms", "dcs", "foreign military sales", "direct commercial sales"]},
            {"id": 107, "query": "What is FMS-Only?",
             "expected": ["fms-only", "fms", "foreign military sales", "foreign military sales only"]},
            {"id": 108, "query": "What items are FMS-Only?",
             "expected": ["fms-only", "fms", "foreign military sales", "foreign military sales only"]},
            {"id": 109, "query": "What is DCS preference?",
             "expected": ["dcs", "dcs preference", "direct commercial sales"]},
            {"id": 110, "query": "Can a purchaser request both FMS and DCS concurrently?",
             "expected": ["fms", "dcs", "foreign military sales", "direct commercial sales"]},
        ]
    },
    
    # Pattern 3: Total Package Approach Queries
    "pattern_c4_3_tpa": {
        "description": "Total Package Approach queries",
        "tests": [
            {"id": 111, "query": "What is the Total Package Approach?",
             "expected": ["total package approach", "tpa"]},
            {"id": 112, "query": "What does TPA include?",
             "expected": ["tpa", "total package approach"]},
            {"id": 113, "query": "Why is TPA important for FMS?",
             "expected": ["tpa", "fms", "total package approach", "foreign military sales"]},
        ]
    },
    
    # Pattern 4: Defense Articles/Equipment Queries
    "pattern_c4_4_equipment": {
        "description": "Defense articles and equipment category queries",
        "tests": [
            {"id": 114, "query": "What is SME Significant Military Equipment?",
             "expected": ["sme", "significant military equipment"]},
            {"id": 115, "query": "What is MDE Major Defense Equipment?",
             "expected": ["mde", "major defense equipment"]},
            {"id": 116, "query": "What is the USML?",
             "expected": ["usml", "united states munitions list"]},
            {"id": 117, "query": "What are defense articles?",
             "expected": ["defense articles"]},
            {"id": 118, "query": "What is GFE Government Furnished Equipment?",
             "expected": ["gfe", "government furnished equipment"]},
        ]
    },
    
    # Pattern 5: Targeting/C4ISR Queries
    "pattern_c4_5_targeting": {
        "description": "Targeting and C4ISR queries (C4.4.16-18)",
        "tests": [
            {"id": 119, "query": "What is GEOINT Geospatial Intelligence?",
             "expected": ["geoint", "geospatial intelligence"]},
            {"id": 120, "query": "What is C4ISR?",
             "expected": ["c4isr", "command control communications computer intelligence surveillance reconnaissance"]},
            {"id": 121, "query": "What is ATD Advanced Target Development?",
             "expected": ["atd", "advanced target development"]},
            {"id": 122, "query": "What is TCM Target Coordinate Mensuration?",
             "expected": ["tcm", "target coordinate mensuration"]},
            {"id": 123, "query": "What is CDE Collateral Damage Estimation?",
             "expected": ["cde", "collateral damage estimation"]},
            {"id": 124, "query": "What targeting and weaponeering is required?",
             "expected": ["targeting", "weaponeering"]},
        ]
    },
    
    # Pattern 6: End Use Monitoring Queries
    "pattern_c4_6_eum": {
        "description": "End Use Monitoring queries",
        "tests": [
            {"id": 125, "query": "What is EUM End Use Monitoring?",
             "expected": ["eum", "end use monitoring"]},
            {"id": 126, "query": "What is EEUM Enhanced End Use Monitoring?",
             "expected": ["eeum", "enhanced end use monitoring", "eum", "end use monitoring"]},
            {"id": 127, "query": "What are retransfer restrictions?",
             "expected": ["retransfer", "retransfer restrictions"]},
        ]
    },
    
    # Pattern 7: Special Items Queries
    "pattern_c4_7_special_items": {
        "description": "Special items requiring approval (NVD, MANPADS, etc.)",
        "tests": [
            {"id": 128, "query": "What are NVD Night Vision Devices?",
             "expected": ["nvd", "night vision device", "nvds", "night vision devices"]},
            {"id": 129, "query": "How are NVDs controlled by DTSA?",
             "expected": ["nvds", "dtsa", "night vision devices", "defense technology security administration"]},
            {"id": 130, "query": "What is MANPADS policy?",
             "expected": ["manpads", "man-portable air defense system"]},
            {"id": 131, "query": "How are Stinger MANPADS controlled?",
             "expected": ["stinger", "manpads", "man-portable air defense system"]},
            {"id": 132, "query": "What cluster munitions are restricted under FMS?",
             "expected": ["fms", "cluster munitions", "foreign military sales"]},
        ]
    },
    
    # Pattern 8: DSCA Office Queries
    "pattern_c4_8_dsca_offices": {
        "description": "DSCA office roles in FMS",
        "tests": [
            {"id": 133, "query": "What does DSCA SPP do?",
             "expected": ["dsca", "spp", "dsca spp", "defense security cooperation agency", "strategy plans and policy"]},
            {"id": 134, "query": "What is DSCA IOPS?",
             "expected": ["dsca", "iops", "dsca iops", "defense security cooperation agency", "international operations"]},
            {"id": 135, "query": "What does IOPS/WPN handle?",
             "expected": ["iops/wpn", "iops", "weapons directorate", "international operations"]},
            {"id": 136, "query": "Who at DSCA IOPS coordinates FMS-Only?",
             "expected": ["fms-only", "dsca", "iops", "dsca iops", "fms", 
                         "foreign military sales", "defense security cooperation agency", 
                         "international operations", "foreign military sales only"]},
        ]
    },
    
    # Pattern 9: International Competition Queries
    "pattern_c4_9_competition": {
        "description": "International weapons competition queries",
        "tests": [
            {"id": 137, "query": "What is an international competition?",
             "expected": ["international competition", "competition"]},
            {"id": 138, "query": "Who leads international competition - DSCA or MILDEP?",
             "expected": ["dsca", "mildep", "international competition", "competition", 
                         "defense security cooperation agency"]},
            {"id": 139, "query": "How does DoD handle competition?",
             "expected": ["dod", "competition", "department of defense"]},
        ]
    },
    
    # Pattern 10: Legal/Regulatory Queries
    "pattern_c4_10_legal": {
        "description": "FMS legal authority queries",
        "tests": [
            {"id": 140, "query": "What AECA laws govern FMS?",
             "expected": ["fms", "aeca", "foreign military sales", "arms export control act"]},
            {"id": 141, "query": "What is the NDP National Disclosure Policy?",
             "expected": ["ndp", "national disclosure policy"]},
            {"id": 142, "query": "What are DFARS requirements for FMS?",
             "expected": ["dfars", "fms", "foreign military sales"]},
            {"id": 143, "query": "How is FMS information classification handled?",
             "expected": ["fms", "classification", "foreign military sales"]},
        ]
    },
    
    # Pattern 11: Coproduction Queries
    "pattern_c4_11_coproduction": {
        "description": "Coproduction agreement queries",
        "tests": [
            {"id": 144, "query": "What is coproduction?",
             "expected": ["coproduction"]},
            {"id": 145, "query": "How are coproduction agreements authorized by DSCA?",
             "expected": ["coproduction", "dsca", "defense security cooperation agency"]},
            {"id": 146, "query": "What is DoDI 5530.03 coproduction?",
             "expected": ["dodi 5530.03", "coproduction"]},
        ]
    },
    
    # Pattern 12: Documents/Forms Queries  
    "pattern_c4_12_documents": {
        "description": "FMS document queries",
        "tests": [
            {"id": 147, "query": "What is P&A Price and Availability?",
             "expected": ["p&a", "price and availability"]},
            {"id": 148, "query": "What is a PAR Pre-LOR Assessment Request?",
             "expected": ["par", "pre-lor assessment request", "lor", "letter of request"]},
            {"id": 149, "query": "What is CN Congressional Notification?",
             "expected": ["cn", "congressional notification"]},
            {"id": 150, "query": "What is the MASL Military Articles and Services List?",
             "expected": ["masl", "military articles and services list"]},
        ]
    },
}

# =============================================================================
# HELPER FUNCTION: Get all Chapter 4 test cases as flat list
# =============================================================================
def get_all_chapter4_tests():
    """Return all Chapter 4 tests as a flat list"""
    all_tests = []
    for pattern_name, pattern_data in TEST_CASES_CHAPTER_4.items():
        for test in pattern_data["tests"]:
            test["pattern"] = pattern_name
            all_tests.append(test)
    return all_tests

def get_chapter4_ground_truth_entities():
    """Get flattened set of all Chapter 4 ground truth entities INCLUDING all valid expansions"""
    all_entities = set()
    
    # Add all entities from ground truth categories
    for category, entities in CHAPTER_4_GROUND_TRUTH.items():
        all_entities.update(entities)
    
    # Add ALL valid acronym expansions (these are NOT hallucinations!)
    VALID_EXPANSIONS = {
        # DSCA Office expansions
        "Strategy Plans And Policy", "strategy plans and policy",
        "International Operations", "international operations", 
        "Weapons Directorate", "weapons directorate",
        "Regional Execution Directorate", "regional execution directorate",
        # Core program expansions
        "Defense Security Cooperation Agency", "defense security cooperation agency",
        "Foreign Military Sales", "foreign military sales",
        "Direct Commercial Sales", "direct commercial sales",
        "Foreign Military Sales Only", "foreign military sales only",
        "Department of Defense", "department of defense",
        # Equipment expansions
        "Significant Military Equipment", "significant military equipment",
        "Major Defense Equipment", "major defense equipment",
        "Government Furnished Equipment", "government furnished equipment",
        "Government Furnished Materiel", "government furnished materiel",
        "Night Vision Device", "night vision device",
        "Night Vision Devices", "night vision devices",
        "Man-Portable Air Defense System", "man-portable air defense system",
        # Targeting expansions  
        "Geospatial Intelligence", "geospatial intelligence",
        "Advanced Target Development", "advanced target development",
        "Target Coordinate Mensuration", "target coordinate mensuration",
        "Collateral Damage Estimation", "collateral damage estimation",
        "Command Control Communications Computer Intelligence Surveillance Reconnaissance",
        "command control communications computer intelligence surveillance reconnaissance",
        # Monitoring expansions
        "End Use Monitoring", "end use monitoring",
        "Enhanced End Use Monitoring", "enhanced end use monitoring",
        "Total Package Approach", "total package approach",
        # Legal expansions
        "Arms Export Control Act", "arms export control act",
        "National Disclosure Policy", "national disclosure policy",
        "United States Munitions List", "united states munitions list",
        "Defense Technology Security Administration", "defense technology security administration",
        # Documents expansions
        "Price and Availability", "price and availability",
        "Pre-LOR Assessment Request", "pre-lor assessment request",
        "Congressional Notification", "congressional notification",
        "Military Articles and Services List", "military articles and services list",
        "Letter of Request", "letter of request", "Letter Of Request",
        "Letter of Offer and Acceptance", "letter of offer and acceptance",
        # Other valid terms
        "competition", "targeting",
        "SPP", "spp", "IOPS", "iops", "NVDs", "nvds",
        "DSCA SPP", "dsca spp", "DSCA IOPS", "dsca iops",
    }
    
    all_entities.update(VALID_EXPANSIONS)
    
    return all_entities

# =============================================================================
# PRINT SUMMARY
# =============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("CHAPTER 4 ENTITY IMPLEMENTATION SUMMARY")
    print("=" * 80)
    
    print(f"\n📊 NEW ACRONYM PAIRS: {len(CHAPTER_4_ACRONYM_PAIRS)}")
    print(f"📊 GROUND TRUTH CATEGORIES:")
    for cat, entities in CHAPTER_4_GROUND_TRUTH.items():
        print(f"   - {cat}: {len(entities)} entities")
    
    print(f"\n📊 ENTITY PATTERNS:")
    for cat, patterns in CHAPTER_4_ENTITY_PATTERNS.items():
        print(f"   - {cat}: {len(patterns)} patterns")
    
    print(f"\n📊 TEST CASES:")
    total_tests = 0
    for pattern_name, pattern_data in TEST_CASES_CHAPTER_4.items():
        count = len(pattern_data["tests"])
        total_tests += count
        print(f"   - {pattern_name}: {count} tests")
    print(f"   TOTAL: {total_tests} tests")
    
    print(f"\n📊 ENTITY RELATIONSHIPS: {len(CHAPTER_4_ENTITY_RELATIONSHIPS)} relationship groups")
