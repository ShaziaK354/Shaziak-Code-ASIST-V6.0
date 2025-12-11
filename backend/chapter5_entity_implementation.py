"""
SAMM Chapter 5 Entity Implementation - CORRECTED v2
====================================================

FIXES:
1. Expected entities only include what's IN THE QUERY
2. Acronym expansions are NOT hallucinations
3. Removed entities that aren't in the query

Chapter 5: Foreign Military Sales (FMS) Case Development
"""

# =============================================================================
# CHAPTER 5 SPECIFIC ACRONYM PAIRS (NEW - Not in Chapter 1 or 4)
# =============================================================================
CHAPTER_5_ACRONYM_PAIRS = {
    # LOR Related
    "lor": "letter of request",
    "loa": "letter of offer and acceptance",
    "p&a": "price and availability",
    "load": "letter of offer and acceptance data",
    "oed": "offer expiration date",
    "rfp": "request for proposal",
    "rfi": "request for information",
    "mfr": "memorandum for record",
    
    # Case Categories
    "clssa": "cooperative logistics supply support arrangement",
    "fmso": "foreign military sales order",
    "fmso i": "foreign military sales order i",
    "fmso ii": "foreign military sales order ii",
    "nte": "not to exceed",
    "ffp": "firm fixed price",
    "eoq": "economic order quantity",
    "npor": "non-program of record",
    "por": "program of record",
    
    # Country Team Assessment
    "cta": "country team assessment",
    "com": "chief of mission",
    "mtcr": "missile technology control regime",
    "uav": "unmanned aerial vehicle",
    "ucav": "unmanned combat aerial vehicle",
    "isr": "intelligence surveillance and reconnaissance",
    "ad": "air defense",
    
    # Case Processing
    "milap": "military department approval",
    "milsgn": "military signature",
    "cpohold": "case processing office hold",
    "cdef": "case development extenuating factor",
    "pmr": "program management review",
    "cas": "contract administration services",
    
    # Organizations (new for Ch5)
    "iops/gex": "international operations global execution directorate",
    "iops/gex/cwd": "case writing and development division",
    "obo/fpre": "office of business operations financial policy and regional execution",
    "obo/fpre/frc": "financial reporting and compliance division",
    "ussocom": "united states special operations command",
    "sof at&l-io": "special operations force acquisition technology and logistics international operations",
    "cpd": "country portfolio director",
    
    # Documents/Forms
    "mtds": "manpower travel data sheet",
    "mou": "memorandum of understanding",
    "sow": "statement of work",
    "pws": "performance work statement",
    "ils": "integrated logistics support",
    "masl": "military articles and services list",
    
    # Special Programs
    "so-p": "special operations peculiar",
    "ot&e": "operational testing and evaluation",
    "nvd": "night vision device",
    "nvds": "night vision devices",
    "manpads": "man-portable air defense system",
    
    # Systems
    "dsams": "defense security assistance management system",
    "cts": "case tracking system",
    "scip": "security cooperation information portal",
}

# =============================================================================
# CHAPTER 5 GROUND TRUTH ENTITIES
# =============================================================================
CHAPTER_5_GROUND_TRUTH = {
    "organizations": [
        "DSCA", "Defense Security Cooperation Agency",
        "IOPS", "Office of International Operations",
        "IOPS/WPN", "IOPS/WPNS", "Weapons Directorate",
        "IOPS/REX", "Regional Execution Directorate",
        "IOPS/GEX", "Global Execution Directorate",
        "IOPS/GEX/CWD", "Case Writing and Development Division",
        "SPP", "Office of Strategy, Plans, and Policy",
        "SPP/EPA", "Execution Policy and Analysis Directorate",
        "ADM/PIE", "Performance, Improvement, and Effectiveness Directorate",
        "ADM/PIE/AME", "Assessment, Monitoring and Evaluation Division",
        "OBO", "Office of Business Operations",
        "OBO/FPRE", "Financial Policy & Regional Execution Directorate",
        "OBO/FPRE/FRC", "Financial Reporting and Compliance Division",
        "FO/OGC", "Office of the General Counsel",
        "CPD", "Country Portfolio Director",
        "PM/SA", "Office of Security Assistance",
        "PM/RSAT", "Office of Regional Security and Arms Transfers",
        "IA", "Implementing Agency",
        "MILDEP", "Military Department",
        "CCMD", "Combatant Command",
        "USSOCOM", "U.S. Special Operations Command",
        "SOF AT&L-IO",
    ],
    "documents": [
        "LOR", "Letter of Request",
        "LOA", "Letter of Offer and Acceptance",
        "P&A", "Price and Availability",
        "LOAD", "LOA Data",
        "CTA", "Country Team Assessment",
        "CN", "Congressional Notification",
        "MFR", "Memorandum for Record",
        "RFP", "Request for Proposal",
        "RFI", "Request for Information",
        "MASL", "Military Articles and Services List",
        "MTDS", "Manpower Travel Data Sheet",
        "MOU", "Memorandum of Understanding",
        "SOW", "Statement of Work",
        "LOR Actionable", "LOR Complete", "LOR Insufficient",
        "LOR Receipt", "LOR Assessment", "LOR checklist", "LOR Advisory",
        "LOA Amendment", "LOA Modification",
        "Standard Terms and Conditions",
    ],
    "case_types": [
        "Defined Order", "Blanket Order",
        "FMS case", "case development",
        "CLSSA", "Cooperative Logistics Supply Support Arrangement",
        "FMSO", "Foreign Military Sales Order",
        "FMSO I", "FMSO II",
        "Category A", "Category B", "Category C", "Category D",
    ],
    "response_types": [
        "hybrid", "hybrid response",
        "negotiated", "negotiated response",
        "NTE", "Not-to-Exceed",
        "FFP", "Firm Fixed Price",
        "EOQ", "Economic Order Quantity",
    ],
    "processing": [
        "MILAP", "Military Department Approval",
        "MILSGN", "Military Signature",
        "CPOHOLD", "Case Processing Office Hold",
        "CPOHOLDREM", "CPOHOLD Removal",
        "CDEF", "Case Development Extenuating Factor",
        "OED", "Offer Expiration Date",
        "restatement", "counteroffer",
        "case development standard",
    ],
    "special_items": [
        "SO-P", "Special Operations-Peculiar", "Special Operations Peculiar",
        "MTCR", "Missile Technology Control Regime",
        "MTCR Category I",
        "ISR", "Intelligence, Surveillance and Reconnaissance",
        "ISR UAV", "ISR UCAV",
        "UAV", "Unmanned Aerial Vehicle",
        "MANPADS", "Man-Portable Air Defense System",
        "NVD", "Night Vision Device",
        "NVDs", "Night Vision Devices",
        "FoM", "Figure of Merit",
        "working dogs", "working dog",
        "white phosphorus",
    ],
    "approvals": [
        "Yockey Waiver",
        "OT&E", "Operational Testing and Evaluation",
        "ENDP", "Exception to National Disclosure Policy",
        "NPOR", "Non-Program of Record",
        "POR", "Program of Record",
    ],
    "systems": [
        "DSAMS", "Defense Security Assistance Management System",
        "CTS", "Case Tracking System",
        "SCIP", "Security Cooperation Information Portal",
        "DTS", "Defense Transportation System",
    ],
    "references": [
        "Table C5.T1", "Table C5.T1A", "Table C5.T1B",
        "Table C5.T3A", "Table C5.T3B",
        "Table C5.T4", "Table C5.T5", "Table C5.T6",
        "Figure C5.F1", "C5.1", "C5.2", "C5.3", "C5.4",
    ],
}

# =============================================================================
# VALID EXPANSIONS - These are NOT hallucinations!
# When an acronym is extracted, its expansion is also valid
# =============================================================================
VALID_EXPANSIONS = {
    # Core acronym → expansion pairs
    "LOR": "Letter of Request",
    "LOA": "Letter of Offer and Acceptance", 
    "P&A": "Price and Availability",
    "CTA": "Country Team Assessment",
    "CPOHOLD": "Case Processing Office Hold",
    "CDEF": "Case Development Extenuating Factor",
    "CLSSA": "Cooperative Logistics Supply Support Arrangement",
    "FMSO": "Foreign Military Sales Order",
    "FMSO I": "Foreign Military Sales Order I",
    "FMSO II": "Foreign Military Sales Order II",
    "NTE": "Not-to-Exceed",
    "FFP": "Firm Fixed Price",
    "DSAMS": "Defense Security Assistance Management System",
    "CTS": "Case Tracking System",
    "SCIP": "Security Cooperation Information Portal",
    "MASL": "Military Articles and Services List",
    "CPD": "Country Portfolio Director",
    "IOPS": "International Operations",
    "IOPS/WPN": "Weapons Directorate",
    "IOPS/GEX": "International Operations Global Execution Directorate",
    "IOPS/GEX/CWD": "Case Writing and Development Division",
    "OBO": "Office of Business Operations",
    "OBO/FPRE": "Financial Policy and Regional Execution Directorate",
    "OBO/FPRE/FRC": "Financial Reporting and Compliance Division",
    "SO-P": "Special Operations Peculiar",
    "MTCR": "Missile Technology Control Regime",
    "ISR": "Intelligence Surveillance Reconnaissance",
    "NVD": "Night Vision Device",
    "NVDs": "Night Vision Devices",
    "MANPADS": "Man-Portable Air Defense System",
    "IA": "Implementing Agency",
    "CCMD": "Combatant Command",
    "FMS": "Foreign Military Sales",
    "DSCA": "Defense Security Cooperation Agency",
}

# =============================================================================
# CORRECTED TEST CASES - Expected only includes entities IN THE QUERY
# =============================================================================
TEST_CASES_CHAPTER_5 = {
    # Pattern 1: LOR Submission Queries
    "pattern_c5_1_lor": {
        "description": "Letter of Request submission and format queries",
        "tests": [
            {"id": 201, "query": "What is a Letter of Request LOR?",
             "expected": ["lor", "letter of request"]},
            {"id": 202, "query": "What format should an LOR have?",
             "expected": ["lor", "letter of request"]},  # "format" is generic, not entity
            {"id": 203, "query": "What is the LOR checklist?",
             "expected": ["lor", "lor checklist", "letter of request"]},
            {"id": 204, "query": "How do I submit an LOR to DSCA IOPS?",
             "expected": ["lor", "dsca", "iops", "dsca iops", "letter of request", 
                         "defense security cooperation agency", "international operations"]},
            {"id": 205, "query": "What makes an LOR actionable?",
             "expected": ["lor", "lor actionable", "letter of request"]},  # "actionable" alone is not entity
        ]
    },
    
    # Pattern 2: LOR Processing Queries
    "pattern_c5_2_lor_processing": {
        "description": "LOR assessment and processing queries",
        "tests": [
            {"id": 206, "query": "What is LOR Actionable status?",
             "expected": ["lor actionable", "lor", "letter of request"]},
            {"id": 207, "query": "What is LOR Complete?",
             "expected": ["lor complete", "lor", "letter of request"]},
            {"id": 208, "query": "What is LOR Insufficient?",
             "expected": ["lor insufficient", "lor", "letter of request"]},
            {"id": 209, "query": "What are LOR actionable criteria in Table C5.T3A?",
             "expected": ["lor", "lor actionable", "actionable criteria", "table c5.t3a", "letter of request"]},
             # "actionable criteria" IS in query, so valid
            {"id": 210, "query": "How does the IA assess an LOR?",
             "expected": ["ia", "lor", "implementing agency", "letter of request"]},
        ]
    },
    
    # Pattern 3: Case Types Queries
    "pattern_c5_3_case_types": {
        "description": "FMS case types and categories queries",
        "tests": [
            {"id": 211, "query": "What is a Defined Order case?",
             "expected": ["defined order", "defined order case"]},  # Both valid
            {"id": 212, "query": "What is a Blanket Order case?",
             "expected": ["blanket order", "blanket order case"]},  # Both valid
            {"id": 213, "query": "What is a CLSSA Cooperative Logistics Supply Support Arrangement?",
             "expected": ["clssa", "cooperative logistics supply support arrangement"]},
            {"id": 214, "query": "What is the difference between FMSO I and FMSO II?",
             "expected": ["fmso", "fmso i", "fmso ii", "foreign military sales order"]},
             # REMOVED "clssa" - NOT in query!
            {"id": 215, "query": "What is Category C case development?",
             "expected": ["category c", "case development"]},
        ]
    },
    
    # Pattern 4: Case Development Standards
    "pattern_c5_4_standards": {
        "description": "Case development timeline and standards queries",
        "tests": [
            {"id": 216, "query": "What is the case development standard for Category A?",
             "expected": ["category a", "case development", "case development standard"]},
            {"id": 217, "query": "What is a CDEF Case Development Extenuating Factor?",
             "expected": ["cdef", "case development extenuating factor", "case development"]},
            {"id": 218, "query": "What is a CPOHOLD?",
             "expected": ["cpohold", "case processing office hold"]},  # Expansion IS valid!
            {"id": 219, "query": "How long does Category B case development take?",
             "expected": ["category b", "case development"]},
            {"id": 220, "query": "What is the 150 day standard for?",
             "expected": []},  # No entities in query! Just asking about "150 day"
        ]
    },
    
    # Pattern 5: P&A Queries
    "pattern_c5_5_pa": {
        "description": "Price and Availability data queries",
        "tests": [
            {"id": 221, "query": "What is P&A Price and Availability data?",
             "expected": ["p&a", "price and availability"]},
            {"id": 222, "query": "How long does P&A preparation take?",
             "expected": ["p&a", "price and availability"]},
            {"id": 223, "query": "Is P&A valid for LOA preparation?",
             "expected": ["p&a", "loa", "price and availability", "letter of offer and acceptance"]},
            {"id": 224, "query": "What is in P&A data per Table C5.T5?",
             "expected": ["p&a", "table c5.t5", "price and availability"]},
            {"id": 225, "query": "Who prepares P&A data?",
             "expected": ["p&a", "price and availability"]},  # REMOVED "ia" - NOT in query!
        ]
    },
    
    # Pattern 6: LOA Queries
    "pattern_c5_6_loa": {
        "description": "Letter of Offer and Acceptance queries",
        "tests": [
            {"id": 226, "query": "What is an LOA Letter of Offer and Acceptance?",
             "expected": ["loa", "letter of offer and acceptance"]},
            {"id": 227, "query": "What are LOA Standard Terms and Conditions?",
             "expected": ["loa", "standard terms and conditions", "letter of offer and acceptance"]},
             # "Standard Terms and Conditions" IS in query!
            {"id": 228, "query": "How is an LOA prepared in DSAMS?",
             "expected": ["loa", "dsams", "letter of offer and acceptance",
                         "defense security assistance management system"]},
            {"id": 229, "query": "What is an LOA Amendment vs Modification?",
             "expected": ["loa", "loa amendment", "letter of offer and acceptance"]},
             # "Amendment" and "Modification" should be full compound terms
            {"id": 230, "query": "What is LOA restatement?",
             "expected": ["loa", "restatement", "letter of offer and acceptance"]},
        ]
    },
    
    # Pattern 7: CTA Queries
    "pattern_c5_7_cta": {
        "description": "Country Team Assessment queries",
        "tests": [
            {"id": 231, "query": "What is a CTA Country Team Assessment?",
             "expected": ["cta", "country team assessment"]},
            {"id": 232, "query": "When is a CTA required for an LOR?",
             "expected": ["cta", "lor", "country team assessment", "letter of request"]},
            {"id": 233, "query": "What elements are required in a CTA per Table C5.T1?",
             "expected": ["cta", "table c5.t1", "country team assessment"]},
            {"id": 234, "query": "Who signs a CTA?",
             "expected": ["cta", "country team assessment"]},  # REMOVED "country team" - CTA is the entity
            {"id": 235, "query": "Does CCMD need to endorse a CTA?",
             "expected": ["cta", "ccmd", "country team assessment", "combatant command"]},
        ]
    },
    
    # Pattern 8: Special Items Queries
    "pattern_c5_8_special_items": {
        "description": "Special items requiring additional review queries",
        "tests": [
            {"id": 236, "query": "What is required for MTCR Category I ISR UAV?",
             "expected": ["mtcr category i", "mtcr", "isr uav", "isr", 
                         "missile technology control regime", "intelligence surveillance reconnaissance"]},
             # REMOVED "cta" - NOT in query! Expansions ARE valid!
            {"id": 237, "query": "What CTA elements are needed for NVDs?",
             "expected": ["nvds", "cta", "night vision devices", "country team assessment"]},
             # "NVDs" plural, not "NVD" singular
            {"id": 238, "query": "What is the LOR Advisory for MANPADS?",
             "expected": ["lor", "lor advisory", "manpads", "letter of request", 
                         "man-portable air defense system"]},
            {"id": 239, "query": "What is required for working dogs LOR?",
             "expected": ["working dogs", "lor", "letter of request"]},
            {"id": 240, "query": "What is SO-P Special Operations Peculiar?",
             "expected": ["so-p", "special operations peculiar"]},
        ]
    },
    
    # Pattern 9: Response Types Queries  
    "pattern_c5_9_response_types": {
        "description": "Types of LOR response queries",
        "tests": [
            {"id": 241, "query": "What is a hybrid FMS response?",
             "expected": ["hybrid", "fms", "foreign military sales"]},
            {"id": 242, "query": "What is a negotiated response?",
             "expected": ["negotiated response"]},  # FIXED: Full term, not just "negotiated"
            {"id": 243, "query": "What is NTE Not-to-Exceed pricing?",
             "expected": ["nte", "not-to-exceed"]},
            {"id": 244, "query": "What is Firm Fixed Price FFP?",
             "expected": ["ffp", "firm fixed price"]},
            {"id": 245, "query": "What responses can the IA provide to an LOR?",
             "expected": ["ia", "lor", "implementing agency", "letter of request"]},
        ]
    },
    
    # Pattern 10: DSCA Organization Queries
    "pattern_c5_10_dsca_org": {
        "description": "DSCA organization and office queries",
        "tests": [
            {"id": 246, "query": "What does IOPS/GEX/CWD do?",
             "expected": ["iops/gex/cwd", "iops/gex", "iops", "case writing and development division",
                         "international operations global execution directorate", "international operations"]},
             # Hierarchical acronyms all valid
            {"id": 247, "query": "What is the role of the CPD Country Portfolio Director?",
             "expected": ["cpd", "country portfolio director"]},
            {"id": 248, "query": "What does IOPS/WPN handle?",
             "expected": ["iops/wpn", "iops", "weapons directorate", "international operations"]},
            {"id": 249, "query": "Who approves a CPOHOLD?",
             "expected": ["cpohold", "case processing office hold"]},
             # REMOVED "adm/pie" - NOT in query!
            {"id": 250, "query": "What is OBO/FPRE/FRC responsible for?",
             "expected": ["obo/fpre/frc", "obo/fpre", "obo", "financial reporting and compliance division",
                         "financial policy and regional execution directorate", "office of business operations"]},
        ]
    },
    
    # Pattern 11: Yockey Waiver Queries
    "pattern_c5_11_yockey": {
        "description": "Pre-OT&E sales and Yockey Waiver queries",
        "tests": [
            {"id": 251, "query": "What is a Yockey Waiver?",
             "expected": ["yockey waiver"]},  # REMOVED "ot&e" - NOT in query!
            {"id": 252, "query": "When is a Yockey Waiver required?",
             "expected": ["yockey waiver"]},  # REMOVED MDE - NOT in query!
            {"id": 253, "query": "Who approves Yockey Waivers?",
             "expected": ["yockey waiver"]},  # REMOVED USD(A&S) - NOT in query!
            {"id": 254, "query": "Does NPOR require a Yockey Waiver?",
             "expected": ["npor", "yockey waiver", "non-program of record"]},
        ]
    },
    
    # Pattern 12: Systems and Tools Queries
    "pattern_c5_12_systems": {
        "description": "DSAMS and case management systems queries",
        "tests": [
            {"id": 255, "query": "What is DSAMS?",
             "expected": ["dsams", "defense security assistance management system"]},
            {"id": 256, "query": "How is LOR data entered in DSAMS?",
             "expected": ["lor", "dsams", "letter of request", 
                         "defense security assistance management system"]},
            {"id": 257, "query": "What is the MASL Military Articles and Services List?",
             "expected": ["masl", "military articles and services list"]},
            {"id": 258, "query": "What is CTS Case Tracking System?",
             "expected": ["cts", "case tracking system"]},
            {"id": 259, "query": "What is SCIP used for?",
             "expected": ["scip", "security cooperation information portal"]},
            {"id": 260, "query": "How are case milestones tracked?",
             "expected": []},  # No specific entities in query - generic question
        ]
    },
}

# =============================================================================
# ENTITY PATTERNS FOR APP INTEGRATION
# =============================================================================
CHAPTER_5_ENTITY_PATTERNS = {
    "chapter5_documents": [
        "LOR", "Letter of Request",
        "LOA", "Letter of Offer and Acceptance",
        "P&A", "Price and Availability",
        "LOAD", "LOA Data",
        "CTA", "Country Team Assessment",
        "CN", "Congressional Notification",
        "MFR", "Memorandum for Record",
        "RFP", "Request for Proposal",
        "RFI", "Request for Information",
        "LOR Actionable", "LOR Complete", "LOR Insufficient",
        "LOR Receipt", "LOR Date", "LOR Assessment",
        "LOR checklist", "LOR Advisory", "actionable LOR",
        "actionable criteria", "Customer Request",
        "Standard Terms and Conditions", "LOA Amendment",
        "LOA Modification", "case lines", "line item",
        "case notes", "LOA notes", "sole source",
        "nonrecurring cost", "assessorial charges",
    ],
    "chapter5_case_types": [
        "Defined Order", "Blanket Order",
        "Defined Order case", "Blanket Order case",
        "blanket order LOA", "defined order LOA",
        "FMS case", "FMS cases", "Multi-Service LOA",
        "case development", "case initialization",
        "Case Identifier", "case category",
        "CLSSA", "Cooperative Logistics Supply Support Arrangement",
        "FMSO", "Foreign Military Sales Order",
        "FMSO I", "FMSO II",
        "Category A", "Category B", "Category C", "Category D",
    ],
    "chapter5_response_types": [
        "hybrid response", "negotiated response", "hybrid",
        "NTE", "Not-to-Exceed", "not-to-exceed",
        "FFP", "Firm Fixed Price", "firm fixed price",
        "negative response", "disapproval recommendation",
        "EOQ", "Economic Order Quantity",
    ],
    "chapter5_processing": [
        "MILAP", "Military Department Approval",
        "MILSGN", "Military Signature",
        "CPOHOLD", "Case Processing Office Hold",
        "CPOHOLDREM", "CPOHOLD Removal",
        "CDEF", "Case Development Extenuating Factor",
        "OED", "Offer Expiration Date",
        "case development standard", "processing time",
        "restatement", "counteroffer",
    ],
    "chapter5_special_items": [
        "SO-P", "Special Operations-Peculiar", "Special Operations Peculiar",
        "USSOCOM", "U.S. Special Operations Command",
        "SOF", "Special Operations Force",
        "SOF AT&L-IO",
        "MTCR Category I", "MTCR Category 1", "MTCR",
        "Missile Technology Control Regime",
        "ISR UAV", "ISR UCAV", "ISR",
        "Intelligence, Surveillance and Reconnaissance",
        "Intelligence Surveillance Reconnaissance",
        "MANPADS", "Man-Portable Air Defense System",
        "NVD", "Night Vision Device", "NVDs", "Night Vision Devices",
        "FoM", "Figure of Merit",
        "white phosphorus", "White Phosphorous Munitions",
        "working dogs", "working dog",
    ],
    "chapter5_approvals": [
        "Yockey Waiver", "Yockey waiver",
        "OT&E", "Operational Testing and Evaluation",
        "pre-OT&E", "technology release", "policy release",
        "disclosure approval", "ENDP",
        "Exception to National Disclosure Policy",
        "NPOR", "Non-Program of Record",
    ],
    "chapter5_organizations": [
        "IOPS", "Office of International Operations", "International Operations",
        "IOPS/WPN", "IOPS/WPNS", "Weapons Directorate",
        "IOPS/REX", "Regional Execution Directorate",
        "IOPS/GEX", "Global Execution Directorate", 
        "International Operations Global Execution Directorate",
        "IOPS/GEX/CWD", "Case Writing and Development Division",
        "SPP", "Office of Strategy, Plans, and Policy",
        "SPP/EPA", "Execution Policy and Analysis Directorate",
        "ADM/PIE",
        "ADM/PIE/AME", "Assessment, Monitoring and Evaluation Division",
        "OBO", "Office of Business Operations",
        "OBO/FPRE", "Financial Policy & Regional Execution Directorate",
        "Financial Policy and Regional Execution Directorate",
        "OBO/FPRE/FRC", "Financial Reporting and Compliance Division",
        "FO/OGC",
        "CPD", "Country Portfolio Director",
        "PM/SA", "Office of Security Assistance",
        "PM/RSAT",
    ],
    "chapter5_systems": [
        "DSAMS", "Defense Security Assistance Management System",
        "CTS", "Case Tracking System",
        "SCIP", "Security Cooperation Information Portal",
        "DTS", "Defense Transportation System",
        "MASL", "Military Articles and Services List",
    ],
    "chapter5_references": [
        "Table C5.T1", "Table C5.T1A", "Table C5.T1B", "Table C5.T1C",
        "Table C5.T1D", "Table C5.T1E", "Table C5.T1F", "Table C5.T1G", "Table C5.T1H",
        "Table C5.T2A", "Table C5.T2B", "Table C5.T3A", "Table C5.T3B",
        "Table C5.T4", "Table C5.T5", "Table C5.T6", "Table C5.T7",
        "Figure C5.F1", "Figure C5.F1A", "Figure C5.F1B",
        "Figure C5.F2", "Figure C5.F3", "Figure C5.F4", "Figure C5.F5",
        "C5.1", "C5.2", "C5.3", "C5.4", "C5.5", "C5.6",
    ],
}

# =============================================================================
# ENTITY RELATIONSHIPS
# =============================================================================
CHAPTER_5_ENTITY_RELATIONSHIPS = {
    "LOR": ["initiates FMS process", "submitted by SCO", "must meet actionable criteria"],
    "LOR Actionable": ["meets C5.1.7 checklist", "enables case development"],
    "Defined Order": ["specific items", "detailed requirements", "fixed quantities"],
    "Blanket Order": ["recurring support", "flexible quantities", "multi-year"],
    "CLSSA": ["cooperative logistics", "supply support", "stock replenishment"],
    "FMSO I": ["initial order", "major equipment"],
    "FMSO II": ["follow-on support", "spare parts"],
    "CDEF": ["extends processing time", "documented justification"],
    "CPOHOLD": ["delays LOA", "requires resolution"],
    "Category A": ["up to 60 days", "simple cases"],
    "Category B": ["up to 90 days", "moderate complexity"],
    "Category C": ["up to 120 days", "complex cases"],
    "Category D": ["over 120 days", "highly complex"],
    "SO-P": ["USSOCOM coordination", "SOF AT&L-IO"],
    "MTCR Category I": ["highest sensitivity", "DSCA/OUSD(P) approval"],
    "Yockey Waiver": ["pre-OT&E release", "USD(A&S) approval"],
    "CPD": ["manages country cases", "DSCA primary POC"],
    "DSAMS": ["case management", "LOA preparation"],
    "CTS": ["status monitoring", "milestone tracking"],
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_all_chapter5_tests():
    """Return all Chapter 5 tests as a flat list"""
    all_tests = []
    for pattern_name, pattern_data in TEST_CASES_CHAPTER_5.items():
        for test in pattern_data["tests"]:
            test["pattern"] = pattern_name
            all_tests.append(test)
    return all_tests

def get_chapter5_ground_truth_entities():
    """Get flattened set of all Chapter 5 ground truth entities"""
    all_entities = set()
    for category, entities in CHAPTER_5_GROUND_TRUTH.items():
        for entity in entities:
            all_entities.add(entity.lower())
    return all_entities

def is_valid_expansion(extracted_entity, query):
    """
    Check if an extracted entity is a valid expansion of something in the query.
    Returns True if valid (NOT a hallucination).
    """
    extracted_lower = extracted_entity.lower()
    query_lower = query.lower()
    
    # Check if it's a direct expansion of an acronym in the query
    for acronym, expansion in VALID_EXPANSIONS.items():
        if acronym.lower() in query_lower:
            if extracted_lower == expansion.lower():
                return True
    
    return False

def get_test_count():
    """Return total number of test cases"""
    return sum(len(p["tests"]) for p in TEST_CASES_CHAPTER_5.values())

# =============================================================================
# PRINT SUMMARY
# =============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("CHAPTER 5 ENTITY IMPLEMENTATION - CORRECTED v2")
    print("=" * 80)
    
    print(f"\n📊 Acronym Pairs: {len(CHAPTER_5_ACRONYM_PAIRS)}")
    print(f"📊 Ground Truth Categories: {len(CHAPTER_5_GROUND_TRUTH)}")
    print(f"📊 Valid Expansions: {len(VALID_EXPANSIONS)}")
    print(f"📊 Test Patterns: {len(TEST_CASES_CHAPTER_5)}")
    print(f"📊 Total Test Cases: {get_test_count()}")
    
    print("\n" + "=" * 80)
    print("FIXES APPLIED:")
    print("=" * 80)
    print("1. Expected entities only include what's IN THE QUERY")
    print("2. Acronym expansions are marked as VALID (not hallucinations)")
    print("3. Removed entities that weren't in the query text")
    print("4. Added VALID_EXPANSIONS dictionary for proper scoring")
