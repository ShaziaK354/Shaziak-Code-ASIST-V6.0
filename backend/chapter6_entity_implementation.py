"""
SAMM Chapter 6 Entity Implementation
=====================================

Chapter 6: FMS Case Implementation and Execution

This module contains:
1. Chapter 6 Ground Truth Entities
2. Chapter 6 Specific Acronym Pairs
3. Chapter 6 Entity Patterns
4. Chapter 6 Entity Relationships
5. Chapter 6 Test Cases (60 tests)

Chapter 6 covers:
- C6.1: Case Implementation
- C6.2: Case Execution
- C6.3: FMS Acquisition
- C6.4: Logistics
- C6.5: Case Reviews
- C6.6: Suspension and Cancellation by USG
- C6.7: Amendments and Modifications
- C6.8: Purchaser-Requested Cancellations
"""

# =============================================================================
# CHAPTER 6 SPECIFIC ACRONYM PAIRS (NEW - Not in Chapters 1-5)
# =============================================================================
CHAPTER_6_ACRONYM_PAIRS = {
    # Implementation Terms
    "ei": "emergency implementation",
    "oa": "obligational authority",
    "ssc": "supply services complete",
    
    # Data Systems
    "difs": "defense integrated financial system",
    "cprs": "case performance reporting system",
    
    # Financial Organizations
    "dfas-in": "defense finance and accounting services indianapolis",
    "cfd": "country finance director",
    "dwcf": "defense working capital fund",
    "wcf": "working capital fund",
    
    # DSCA Offices (new for C6)
    "obo/fpre/fp": "financial policy division",
    "obo/imt/eads": "enterprise application development and support division",
    "iops/gex/scd": "security cooperation division",
    
    # Acquisition Terms
    "far": "federal acquisition regulation",
    "dfars": "defense far supplement",
    "cica": "competition in contracting act",
    "taa": "technical assistance agreement",
    "clin": "contract line item number",
    "arp": "acquisition requirements package",
    
    # Supply/Logistics
    "milstrip": "military standard requisitioning and issue procedures",
    "f/ad": "force activity designator",
    "und": "urgency of need designator",
    "jmpab": "joint materiel priority allocation board",
    "ummips": "uniform material movement and issue priority system",
    "cbs": "commercial buying service",
    "tvl": "tailored vendor logistics",
    "pros": "parts and repair ordering system",
    "snap": "simplified non-standard acquisition process",
    "nsn": "national stock number",
    "tcn": "transportation control number",
    "icp": "inventory control point",
    "ilco": "international logistics control office",
    
    # Documents/Forms
    "sdr": "supply discrepancy report",
    "sf 364": "standard form 364",
    "euc": "end use certificate",
    "eeum": "enhanced end use monitoring",
    "dlm": "defense logistics management",
    "dlms": "defense logistics management standards",
    "jtr": "joint travel regulations",
    
    # Equipment/Programs
    "gfe": "government furnished equipment",
    "gfm": "government furnished materiel",
    "mtt": "mobile training team",
    "ltd": "language training detachment",
    "r&r": "repair and return",
    
    # Review Types
    "fmr": "financial management review",
    "sar": "security assistance review",
    "crr": "case reconciliation review",
    "samr": "security assistance management review",
    
    # Special Programs
    "enjjpt": "euro nato joint jet pilot training program",
    "ecisap": "electronic combat international security assistance program",
    
    # Codes/Terms
    "ta": "type of assistance",
    "sos": "source of supply",
    "orc": "offer release code",
    "scml": "small case management line",
    "etp": "exception to policy",
    "cui": "controlled unclassified information",
    
    # Financial
    "vat": "value added tax",
    "pc&h": "packing crating and handling",
    "o&m": "operations and maintenance",
    "rdt&e": "research development test and evaluation",
    
    # Milestone Codes
    "dreact": "reactivation authorized milestone",
    "milreact": "mildep reactivation",
}

# =============================================================================
# CHAPTER 6 GROUND TRUTH ENTITIES
# =============================================================================
CHAPTER_6_GROUND_TRUTH = {
    # Organizations (C6.1 - C6.8)
    "organizations": {
        # DSCA Offices
        "DSCA", "Defense Security Cooperation Agency",
        "OBO", "Office of Business Operations",
        "OBO/FPRE", "Financial Policy & Regional Execution Directorate",
        "OBO/FPRE/FP", "Financial Policy Division",
        "OBO/IMT/EADS", "Enterprise Application Development and Support Division",
        "IOPS", "Office of International Operations",
        "IOPS/REX", "Regional Execution Directorate",
        "IOPS/GEX/SCD", "Security Cooperation Division",
        "IOPS/GEX/CWD", "Case Writing and Development Division",
        "IOPS/WPN", "Weapons Directorate",
        "SPP", "Office of Strategy, Plans, and Policy",
        "SPP/EPA", "Execution Policy and Analysis Directorate",
        "ADM/PIE", "Performance Improvement and Effectiveness Directorate",
        "FO/OGC", "Office of the General Counsel",
        "CPD", "Country Portfolio Director",
        "CFD", "Country Finance Director",
        
        # Financial
        "DFAS", "Defense Finance and Accounting Service",
        "DFAS-IN", "Defense Finance and Accounting Services - Indianapolis",
        
        # DoD Components
        "DoD", "Department of Defense",
        "MILDEP", "MILDEPS", "Military Department",
        "IA", "IAS", "Implementing Agency",
        "DLA", "Defense Logistics Agency",
        "ICP", "Inventory Control Point",
        "ILCO", "International Logistics Control Office",
        "OSD", "Office of the Secretary of Defense",
        
        # Defense Officials
        "USD(P)", "Under Secretary of Defense for Policy",
        "USD(A&S)", "Under Secretary of Defense for Acquisition and Sustainment",
        "ASD(RA)", "Assistant Secretary of Defense for Reserve Affairs",
        "CJCS", "Chairman of the Joint Chiefs of Staff",
        "CCDR", "Combatant Commander",
        
        # State Department
        "State", "Department of State",
        "State (PM)", "Bureau of Political-Military Affairs",
        
        # Other
        "SCO", "SCOS", "Security Cooperation Organization",
        "JMPAB", "Joint Materiel Priority Allocation Board",
    },
    
    # Documents (C6.1 - C6.8)
    "documents": {
        # Core Documents
        "LOA", "Letter of Offer and Acceptance",
        "LOR", "Letter of Request",
        "CN", "Congressional Notification",
        "SDR", "Supply Discrepancy Report",
        "SF 364", "Standard Form 364",
        "EUC", "End Use Certificate",
        "SOW", "Statement of Work",
        "PWS", "Performance Work Statement",
        
        # Regulations
        "FAR", "Federal Acquisition Regulation",
        "DFARS", "Defense FAR Supplement",
        "AECA", "Arms Export Control Act",
        "CICA", "Competition in Contracting Act",
        "DoD FMR", "DoD Financial Management Regulation",
        "DLM", "Defense Logistics Management",
        "DLMS", "Defense Logistics Management Standards",
        "JTR", "Joint Travel Regulations",
        "CJCSI", "Chairman of the Joint Chiefs of Staff Instruction",
        
        # Amendments/Modifications
        "Amendment", "LOA Amendment",
        "Modification", "LOA Modification",
        "Concurrent Modification",
        "ETP", "Exception to Policy",
    },
    
    # Systems (C6.1)
    "systems": {
        "DSAMS", "Defense Security Assistance Management System",
        "DIFS", "Defense Integrated Financial System",
        "CPRS", "Case Performance Reporting System",
        "CTS", "Case Tracking System",
        "SCIP", "Security Cooperation Information Portal",
        "DTS", "Defense Transportation System",
    },
    
    # Case Types (C6.1, C6.4)
    "case_types": {
        "FMS", "Foreign Military Sales",
        "CLSSA", "Cooperative Logistics Supply Support Arrangement",
        "FMSO I", "Foreign Military Sales Order I",
        "FMSO II", "Foreign Military Sales Order II",
        "Defined Order", "Blanket Order",
    },
    
    # Financial Terms (C6.1 - C6.8)
    "financial": {
        # Implementation
        "EI", "Emergency Implementation",
        "OA", "Obligational Authority",
        "initial deposit",
        "termination liability",
        
        # Funds
        "FMF", "Foreign Military Financing",
        "DWCF", "Defense Working Capital Fund",
        "WCF", "Working Capital Fund",
        "O&M", "Operations and Maintenance",
        "PA", "Procurement Appropriation",
        "RDT&E", "Research Development Test and Evaluation",
        "PC&H", "Packing Crating and Handling",
        
        # Costs
        "Contingent Fees", "agent fees", "sales commissions",
        "Offset", "offset costs", "offset arrangements",
        "FMS Administrative Surcharge",
        "SCML", "Small Case Management Line",
        "VAT", "Value Added Tax",
    },
    
    # Logistics (C6.4)
    "logistics": {
        # Priority
        "F/AD", "Force/Activity Designator",
        "UND", "Urgency of Need Designator",
        "Project Codes",
        "UMMIPS", "Uniform Material Movement and Issue Priority System",
        
        # Requisitions
        "MILSTRIP", "Military Standard Requisitioning and Issue Procedures",
        "ICP", "Inventory Control Point",
        "standard requisitions",
        "backorder",
        
        # Programs
        "CBS", "Commercial Buying Service",
        "TVL", "Tailored Vendor Logistics",
        "PROS", "Parts and Repair Ordering System",
        "SNAP", "Simplified Non-Standard Acquisition Process",
        
        # Equipment
        "GFE", "Government Furnished Equipment",
        "GFM", "Government Furnished Materiel",
        "EDA", "Excess Defense Articles",
        
        # Repair
        "Direct Exchange",
        "R&R", "Repair and Return",
        
        # Identifiers
        "NSN", "National Stock Number",
        "TCN", "Transportation Control Number",
        "TA", "Type of Assistance",
        "SOS", "Source of Supply",
    },
    
    # Review Types (C6.5)
    "reviews": {
        "FMR", "Financial Management Review",
        "PMR", "Program Management Review",
        "SAR", "Security Assistance Review",
        "CRR", "Case Reconciliation Review",
        "SAMR", "Security Assistance Management Review",
        "Country-Level Review",
        "Service-Level Review",
        "Program-Level Review",
        "Case-Level Review",
        "Cultural Days",
    },
    
    # Suspension/Cancellation (C6.6, C6.8)
    "suspension": {
        "Suspension", "suspension of delivery",
        "Brooke Amendment",
        "sanctions",
        "contract termination",
        "case cancellation",
        "MTT", "Mobile Training Team",
        "LTD", "Language Training Detachment",
        "IMET", "International Military Education and Training",
    },
    
    # Amendment/Modification Terms (C6.7)
    "amendments": {
        "Amendment", "Modification",
        "Concurrent Modification",
        "change in scope",
        "within-scope changes",
        "Restatement", "Counteroffer",
        "Pen and Ink Changes",
        "DREACT", "Reactivation Authorized Milestone",
        "MILREACT", "MILDEP Reactivation",
        "OED", "Offer Expiration Date",
        "SSC", "Supply Services Complete",
    },
    
    # Acquisition (C6.3)
    "acquisition": {
        "sole source",
        "other than full and open competition",
        "International Agreement",
        "CICA", "Competition in Contracting Act",
        "Warranties",
        "TAA", "Technical Assistance Agreement",
        "CLIN", "Contract Line Item Number",
        "ARP", "Acquisition Requirements Package",
        "RFP", "Request for Proposal",
        "contracting officer",
    },
    
    # Equipment Categories
    "equipment": {
        "SME", "Significant Military Equipment",
        "MDE", "Major Defense Equipment",
        "EUM", "End Use Monitoring",
        "EEUM", "Enhanced End Use Monitoring",
    },
    
    # Special Programs
    "special_programs": {
        "ENJJPT", "Euro-NATO Joint Jet Pilot Training Program",
        "ECISAP", "Electronic Combat International Security Assistance Program",
        "EW", "Electronic Warfare",
        "BPC", "Building Partner Capacity",
        "NATO", "North Atlantic Treaty Organization",
    },
}

# =============================================================================
# CHAPTER 6 ENTITY PATTERNS (For pattern matching in queries)
# =============================================================================
CHAPTER_6_ENTITY_PATTERNS = {
    "implementation_patterns": [
        r"\bcase\s+implementation\b",
        r"\bimplementing\s+instructions\b",
        r"\bemergency\s+implementation\b",
        r"\bdelayed\s+implementation\b",
        r"\bfinancial\s+implementation\b",
        r"\broutine\s+implementation\b",
        r"\bobligation(?:al)?\s+authority\b",
        r"\binitial\s+deposit\b",
    ],
    "execution_patterns": [
        r"\bcase\s+execution\b",
        r"\bFMS\s+case\s+life\s+cycle\b",
        r"\bcase\s+files?\b",
        r"\bexecution\s+records?\b",
        r"\bdisbursement\s+documentation\b",
        r"\baudit\s+trail\b",
        r"\bretention\s+period\b",
    ],
    "acquisition_patterns": [
        r"\bsole\s+source\b",
        r"\bother\s+than\s+full\s+and\s+open\b",
        r"\binternational\s+agreement\b",
        r"\bcontingent\s+fees?\b",
        r"\bagent\s+fees?\b",
        r"\bsales\s+commissions?\b",
        r"\boffset(?:s)?\b",
        r"\bwarrant(?:y|ies)\b",
        r"\bEnd\s+Use\s+Certificate\b",
    ],
    "logistics_patterns": [
        r"\bForce[\s/]Activity\s+Designator\b",
        r"\bF/AD\b",
        r"\bUrgency\s+of\s+Need\b",
        r"\bproject\s+codes?\b",
        r"\brequisition(?:s)?\b",
        r"\bbackorder\b",
        r"\bdiversions?\b",
        r"\bwithdrawals?\b",
        r"\bdirect\s+exchange\b",
        r"\brepair\s+and\s+return\b",
    ],
    "review_patterns": [
        r"\bcase\s+review(?:s)?\b",
        r"\bfinancial\s+management\s+review\b",
        r"\bprogram\s+management\s+review\b",
        r"\bsecurity\s+assistance\s+review\b",
        r"\breconciliation\s+review\b",
        r"\bcultural\s+days?\b",
    ],
    "amendment_patterns": [
        r"\bamendment(?:s)?\b",
        r"\bmodification(?:s)?\b",
        r"\bconcurrent\s+modification\b",
        r"\bchange\s+in\s+scope\b",
        r"\bwithin[\s-]scope\b",
        r"\brestatement\b",
        r"\bcounteroffer\b",
        r"\bpen\s+and\s+ink\b",
        r"\bexception\s+to\s+policy\b",
    ],
    "suspension_patterns": [
        r"\bsuspension\b",
        r"\bsanctions?\b",
        r"\bBrooke\s+Amendment\b",
        r"\bcase\s+cancellation\b",
        r"\btermination\s+costs?\b",
    ],
    "sdr_patterns": [
        r"\bsupply\s+discrepancy\b",
        r"\bSDR\b",
        r"\bSF\s*364\b",
        r"\bshipment\s+documentation\b",
        r"\bdiscrepanc(?:y|ies)\b",
    ],
}

# =============================================================================
# CHAPTER 6 ENTITY RELATIONSHIPS
# =============================================================================
CHAPTER_6_ENTITY_RELATIONSHIPS = {
    # Implementation relationships (C6.1)
    "case implementation": ["requires initial deposit", "recorded in DSAMS", "requires OA"],
    "Emergency Implementation": ["approved by CFD", "requires purchaser acceptance", "urgent situations"],
    "DFAS-IN": ["processes deposits", "posts financial implementation", "notifies SCO"],
    "CFD": ["approves EI", "confirms deposit timing", "coordinates with IA"],
    
    # Execution relationships (C6.2)
    "case execution": ["longest phase", "includes logistics and acquisition", "tracked by case managers"],
    "case managers": ["track delivery status", "maintain case files", "ensure accurate records"],
    "SCO": ["coordinates with purchasers", "administrative arrangements", "receives notifications"],
    
    # Acquisition relationships (C6.3)
    "sole source": ["International Agreement exception", "requires purchaser request", "FAR 6.302-4"],
    "Contingent Fees": ["require purchaser approval", "include agent fees", "sales commissions"],
    "Offsets": ["negotiated with U.S. firms", "USG does not commit", "contractor responsibility"],
    "Warranties": ["same as DoD", "exercised through SDR", "described in LOA note"],
    
    # Logistics relationships (C6.4)
    "F/AD": ["assigned by CJCS", "determines priority", "I through V ranking"],
    "CLSSA": ["same basis as U.S. Forces", "FMSO I and FMSO II", "equity investment"],
    "SDR": ["submitted within one year", "SF 364", "$200 minimum value"],
    "Direct Exchange": ["same type item", "not an end item", "from DoD stocks"],
    
    # Review relationships (C6.5)
    "FMR": ["outlined in Chapter 9", "financial management", "country-level review"],
    "PMR": ["event-driven", "milestone plan", "program-level review"],
    "Cultural Days": ["host nation culture", "approved by IA and partner", "with review agenda"],
    
    # Amendment relationships (C6.7)
    "Amendment": ["change in scope", "requires purchaser acceptance", "can be restated"],
    "Modification": ["no change in scope", "unilateral by USG", "administrative changes"],
    "Concurrent Modification": ["transfers funding", "multiple cases", "same time implementation"],
    "ETP": ["submitted through tracker", "10 business days routine", "approved by DSCA"],
    
    # Suspension relationships (C6.6)
    "Suspension": ["directed by State", "not same as cancellation", "deliveries stopped"],
    "Brooke Amendment": ["default in payment", "one year period", "FMF affected"],
    
    # Cancellation relationships (C6.8)
    "case cancellation": ["purchaser or USG requested", "termination costs apply", "closure process"],
    "FMS Administrative Surcharge": ["non-refundable minimum", "SCML value", "up to $15,000"],
}

# =============================================================================
# TEST CASES - 60 TESTS FOR CHAPTER 6
# =============================================================================
TEST_CASES_CHAPTER_6 = {
    # Pattern 1: Case Implementation Queries (C6.1)
    "pattern_c6_1_implementation": {
        "description": "Case Implementation queries",
        "tests": [
            {"id": 301, "query": "What is routine case implementation?",
             "expected": ["routine case implementation", "case implementation"]},
            {"id": 302, "query": "How does Emergency Implementation EI work?",
             "expected": ["ei", "emergency implementation"]},
            {"id": 303, "query": "What causes delayed case implementation?",
             "expected": ["delayed case implementation", "case implementation"]},
            {"id": 304, "query": "What is Obligational Authority OA?",
             "expected": ["oa", "obligational authority"]},
            {"id": 305, "query": "When is an initial deposit required for FMS case implementation?",
             "expected": ["initial deposit", "fms", "case implementation"]},
        ]
    },
    
    # Pattern 2: Data Systems Queries (C6.1)
    "pattern_c6_2_systems": {
        "description": "Data systems and tracking queries",
        "tests": [
            {"id": 306, "query": "What systems like DSAMS and DIFS are used for FMS case implementation?",
             "expected": ["dsams", "difs", "fms", "case implementation"]},
            {"id": 307, "query": "What is DIFS?",
             "expected": ["difs", "defense integrated financial system"]},
            {"id": 308, "query": "What is CPRS Case Performance Reporting System?",
             "expected": ["cprs", "case performance reporting system"]},
            {"id": 309, "query": "How is CTS used in amendments?",
             "expected": ["cts", "case tracking system", "amendment"]},
            {"id": 310, "query": "What is SCIP Security Cooperation Information Portal used for?",
             "expected": ["scip", "security cooperation information portal"]},
        ]
    },
    
    # Pattern 3: Case Execution Queries (C6.2)
    "pattern_c6_3_execution": {
        "description": "Case execution and records queries",
        "tests": [
            {"id": 311, "query": "What is FMS case execution?",
             "expected": ["fms", "case execution"]},
            {"id": 312, "query": "What are General FMS Case Files?",
             "expected": ["fms", "case files"]},
            {"id": 313, "query": "What is the retention period for FMS case files?",
             "expected": ["fms", "retention period"]},
            {"id": 314, "query": "What are case execution records?",
             "expected": ["case execution", "execution records"]},
            {"id": 315, "query": "What is disbursement documentation for FMS?",
             "expected": ["disbursement documentation", "fms"]},
        ]
    },
    
    # Pattern 4: Acquisition Queries (C6.3)
    "pattern_c6_4_acquisition": {
        "description": "FMS acquisition process queries",
        "tests": [
            {"id": 316, "query": "What is sole source procurement in FMS?",
             "expected": ["sole source", "fms"]},
            {"id": 317, "query": "What is the International Agreement exception?",
             "expected": ["international agreement"]},
            {"id": 318, "query": "How does CICA Competition in Contracting Act apply to FMS?",
             "expected": ["cica", "competition in contracting act", "fms"]},
            {"id": 319, "query": "What role does the contracting officer play in FMS?",
             "expected": ["contracting officer", "fms"]},
            {"id": 320, "query": "What is certified cost or pricing data in FMS acquisition?",
             "expected": ["fms", "acquisition"]},
        ]
    },
    
    # Pattern 5: Contingent Fees and Offsets (C6.3.7, C6.3.9)
    "pattern_c6_5_fees_offsets": {
        "description": "Contingent fees and offset queries",
        "tests": [
            {"id": 321, "query": "What are contingent fees in FMS?",
             "expected": ["contingent fees", "fms"]},
            {"id": 322, "query": "Which countries must approve all contingent fees?",
             "expected": ["contingent fees"]},
            {"id": 323, "query": "What is the contingent fee threshold of $50,000?",
             "expected": ["contingent fees"]},
            {"id": 324, "query": "What are FMS offsets?",
             "expected": ["offset", "fms"]},
            {"id": 325, "query": "Can FMF funds pay for offsets?",
             "expected": ["offset", "fmf"]},
        ]
    },
    
    # Pattern 6: Logistics and Priority (C6.4)
    "pattern_c6_6_logistics": {
        "description": "Logistics and priority queries",
        "tests": [
            {"id": 326, "query": "What is Force/Activity Designator F/AD?",
             "expected": ["f/ad", "force activity designator"]},
            {"id": 327, "query": "What are Project Codes assigned by CJCS?",
             "expected": ["project codes", "cjcs"]},
            {"id": 328, "query": "What is UMMIPS?",
             "expected": ["ummips", "uniform material movement and issue priority system"]},
            {"id": 329, "query": "How do standard requisitions work with ICP?",
             "expected": ["standard requisitions", "icp"]},
            {"id": 330, "query": "What is the ILCO International Logistics Control Office?",
             "expected": ["ilco", "international logistics control office"]},
        ]
    },
    
    # Pattern 7: CLSSA and FMSO (C6.4.3.2)
    "pattern_c6_7_clssa": {
        "description": "CLSSA and FMSO queries",
        "tests": [
            {"id": 331, "query": "What is CLSSA?",
             "expected": ["clssa", "cooperative logistics supply support arrangement"]},
            {"id": 332, "query": "What is FMSO I Foreign Military Sales Order I?",
             "expected": ["fmso i", "foreign military sales order"]},
            {"id": 333, "query": "What is FMSO II Foreign Military Sales Order II?",
             "expected": ["fmso ii", "foreign military sales order"]},
            {"id": 334, "query": "What is FMSO I maturity?",
             "expected": ["fmso i", "fmso i maturity"]},
            {"id": 335, "query": "How does DLA support CLSSA?",
             "expected": ["dla", "clssa"]},
        ]
    },
    
    # Pattern 8: Repair and Returns (C6.4.8, C6.4.9)
    "pattern_c6_8_repair": {
        "description": "Repair programs and returns queries",
        "tests": [
            {"id": 336, "query": "What is Direct Exchange?",
             "expected": ["direct exchange"]},
            {"id": 337, "query": "What is Repair and Return R&R?",
             "expected": ["r&r", "repair and return"]},
            {"id": 338, "query": "What is Concurrent Modification for R&R?",
             "expected": ["concurrent modification", "r&r"]},
            {"id": 339, "query": "What defense articles can be returned?",
             "expected": ["returns", "defense article"]},
            {"id": 340, "query": "What are the AECA requirements for returns?",
             "expected": ["returns", "aeca"]},
        ]
    },
    
    # Pattern 9: Supply Discrepancy Reports (C6.4.10)
    "pattern_c6_9_sdr": {
        "description": "SDR process queries",
        "tests": [
            {"id": 341, "query": "What is a Supply Discrepancy Report SDR using SF 364?",
             "expected": ["sdr", "supply discrepancy report", "sf 364"]},
            {"id": 342, "query": "What is the timeframe for submitting an SDR?",
             "expected": ["sdr", "supply discrepancy report"]},
            {"id": 343, "query": "What is the minimum value for SDR processing?",
             "expected": ["sdr", "minimum value"]},
            {"id": 344, "query": "What causes supply discrepancies in FMS?",
             "expected": ["supply discrepancy", "fms"]},
            {"id": 345, "query": "Who at DSCA OBO/FPRE/FP reviews SDRs over $50,000?",
             "expected": ["sdr", "dsca", "obo/fpre/fp"]},
        ]
    },
    
    # Pattern 10: Case Reviews (C6.5)
    "pattern_c6_10_reviews": {
        "description": "Case review process queries",
        "tests": [
            {"id": 346, "query": "What is a Financial Management Review FMR?",
             "expected": ["fmr", "financial management review"]},
            {"id": 347, "query": "What is a Program Management Review PMR?",
             "expected": ["pmr", "program management review"]},
            {"id": 348, "query": "What is the Security Assistance Management Review SAMR?",
             "expected": ["samr", "security assistance management review"]},
            {"id": 349, "query": "How often should FMS case reviews occur?",
             "expected": ["fms", "case review"]},
            {"id": 350, "query": "What are Cultural Days in FMS reviews?",
             "expected": ["cultural days", "fms"]},
        ]
    },
    
    # Pattern 11: Suspension and Sanctions (C6.6)
    "pattern_c6_11_suspension": {
        "description": "Suspension and sanctions queries",
        "tests": [
            {"id": 351, "query": "How does State suspend FMS deliveries?",
             "expected": ["suspension", "state", "fms"]},
            {"id": 352, "query": "What is the Brooke Amendment?",
             "expected": ["brooke amendment", "amendment"]},
            {"id": 353, "query": "What happens to IMET training during suspension?",
             "expected": ["suspension", "imet"]},
            {"id": 354, "query": "What is the CCDR impact assessment for suspension?",
             "expected": ["suspension", "ccdr"]},
            {"id": 355, "query": "Can a suspension become a case cancellation?",
             "expected": ["suspension", "case cancellation"]},
        ]
    },
    
    # Pattern 12: Amendments (C6.7)
    "pattern_c6_12_amendments": {
        "description": "Amendment process queries",
        "tests": [
            {"id": 356, "query": "When is an FMS case Amendment required for change in scope?",
             "expected": ["amendment", "fms", "change in scope"]},
            {"id": 357, "query": "What is the $50,000 break point for amendments?",
             "expected": ["amendment"]},
            {"id": 358, "query": "What is a restatement of an amendment?",
             "expected": ["restatement", "amendment"]},
            {"id": 359, "query": "What is a counteroffer?",
             "expected": ["counteroffer"]},
            {"id": 360, "query": "How are amendments implemented?",
             "expected": ["amendment"]},
        ]
    },
    
    # Pattern 13: Modifications (C6.7)
    "pattern_c6_13_modifications": {
        "description": "Modification process queries",
        "tests": [
            {"id": 361, "query": "When is a Modification used instead of Amendment?",
             "expected": ["modification", "amendment"]},
            {"id": 362, "query": "What is a Concurrent Modification?",
             "expected": ["concurrent modification", "modification"]},
            {"id": 363, "query": "What within-scope changes can be made on a Modification?",
             "expected": ["modification", "within-scope"]},
            {"id": 364, "query": "Are Pen and Ink Changes allowed on Modifications?",
             "expected": ["pen and ink", "modification"]},
            {"id": 365, "query": "What is the DREACT milestone?",
             "expected": ["dreact", "reactivation authorized milestone"]},
        ]
    },
    
    # Pattern 14: Exception to Policy (C6.7.5)
    "pattern_c6_14_etp": {
        "description": "Exception to Policy queries",
        "tests": [
            {"id": 366, "query": "What is an Exception to Policy ETP?",
             "expected": ["etp", "exception to policy"]},
            {"id": 367, "query": "How long to process ETP requests?",
             "expected": ["etp", "exception to policy"]},
            {"id": 368, "query": "How long are ETP approvals valid?",
             "expected": ["etp", "exception to policy"]},
            {"id": 369, "query": "What is needed for an ETP request?",
             "expected": ["etp", "exception to policy"]},
            {"id": 370, "query": "Where are ETP requests submitted?",
             "expected": ["etp", "exception to policy"]},
        ]
    },
    
    # Pattern 15: Case Cancellation (C6.8)
    "pattern_c6_15_cancellation": {
        "description": "Case cancellation queries",
        "tests": [
            {"id": 371, "query": "What is a purchaser-requested case cancellation?",
             "expected": ["case cancellation"]},
            {"id": 372, "query": "What is the minimum SCML administrative charge for cancelled cases?",
             "expected": ["scml", "case cancellation"]},
            {"id": 373, "query": "Can the USG cancel an FMS case?",
             "expected": ["fms", "case cancellation"]},
            {"id": 374, "query": "What happens to unused FMS cases in closure?",
             "expected": ["fms", "case closure"]},
            {"id": 375, "query": "What is a minimal-dollar value line on FMS cases?",
             "expected": ["minimal-dollar value", "fms"]},
        ]
    },
    
    # Pattern 16: DSCA Organizations (C6)
    "pattern_c6_16_organizations": {
        "description": "DSCA organization queries",
        "tests": [
            {"id": 376, "query": "What does OBO/FPRE/FP Financial Policy Division do?",
             "expected": ["obo/fpre/fp", "financial policy division"]},
            {"id": 377, "query": "What is the role of the CFD Country Finance Director?",
             "expected": ["cfd", "country finance director"]},
            {"id": 378, "query": "What does SPP/EPA Execution Policy and Analysis Directorate handle?",
             "expected": ["spp/epa", "execution policy and analysis directorate"]},
            {"id": 379, "query": "What is DFAS-IN responsible for?",
             "expected": ["dfas-in", "dfas"]},
            {"id": 380, "query": "What does IOPS/GEX/CWD Case Writing and Development Division do?",
             "expected": ["iops/gex/cwd", "case writing and development division"]},
        ]
    },
    
    # Pattern 17: Special Programs (C6)
    "pattern_c6_17_special": {
        "description": "Special program queries",
        "tests": [
            {"id": 381, "query": "What is ENJJPT Euro-NATO Joint Jet Pilot Training?",
             "expected": ["enjjpt", "euro-nato joint jet pilot training"]},
            {"id": 382, "query": "What is ECISAP Electronic Combat International Security Assistance Program?",
             "expected": ["ecisap", "electronic combat international security assistance program"]},
            {"id": 383, "query": "What is FMS TVL Tailored Vendor Logistics?",
             "expected": ["fms", "tvl", "tailored vendor logistics"]},
            {"id": 384, "query": "What is the Commercial Buying Service CBS?",
             "expected": ["cbs", "commercial buying service"]},
            {"id": 385, "query": "What is PROS Parts and Repair Ordering System?",
             "expected": ["pros", "parts and repair ordering system"]},
        ]
    },
    
    # Pattern 18: Financial Guidelines (C6)
    "pattern_c6_18_financial": {
        "description": "Financial guidelines queries",
        "tests": [
            {"id": 386, "query": "What is the Defense Working Capital Fund DWCF?",
             "expected": ["dwcf", "defense working capital fund"]},
            {"id": 387, "query": "How are SDR Supply Discrepancy Reports financed?",
             "expected": ["sdr", "supply discrepancy report"]},
            {"id": 388, "query": "What is PC&H Packing Crating and Handling?",
             "expected": ["pc&h", "packing crating and handling"]},
            {"id": 389, "query": "What is the FMS Administrative Surcharge?",
             "expected": ["fms", "fms administrative surcharge"]},
            {"id": 390, "query": "What is the SCML Small Case Management Line?",
             "expected": ["scml", "small case management line"]},
        ]
    },
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_all_chapter6_tests():
    """Return all Chapter 6 tests as a flat list"""
    all_tests = []
    for pattern_name, pattern_data in TEST_CASES_CHAPTER_6.items():
        for test in pattern_data["tests"]:
            test["pattern"] = pattern_name
            all_tests.append(test)
    return all_tests

def get_chapter6_ground_truth_entities():
    """Get flattened set of all Chapter 6 ground truth entities INCLUDING all valid expansions"""
    all_entities = set()
    
    # Add all entities from ground truth categories
    for category, entities in CHAPTER_6_GROUND_TRUTH.items():
        all_entities.update(entities)
    
    # Add ALL valid acronym expansions (these are NOT hallucinations!)
    VALID_EXPANSIONS = {
        # Implementation expansions
        "Emergency Implementation", "emergency implementation",
        "Obligational Authority", "obligational authority",
        "case implementation", "financial implementation",
        "initial deposit", "routine implementation",
        "Routine Case Implementation", "routine case implementation",
        "Delayed Case Implementation", "delayed case implementation",
        "case execution", "FMS case", "fms case",
        "FMS cases", "fms cases",
        
        # System expansions
        "Defense Security Assistance Management System", "defense security assistance management system",
        "Defense Integrated Financial System", "defense integrated financial system",
        "Case Performance Reporting System", "case performance reporting system",
        "Case Tracking System", "case tracking system",
        
        # Organization expansions
        "Defense Finance and Accounting Service", "defense finance and accounting service",
        "Defense Finance and Accounting Services - Indianapolis",
        "Country Finance Director", "country finance director",
        "Financial Policy Division", "financial policy division",
        "Implementing Agency", "implementing agency",
        "Inventory Control Point", "inventory control point",
        "International Logistics Control Office", "international logistics control office",
        
        # Logistics expansions
        "Force/Activity Designator", "force activity designator",
        "Urgency of Need Designator", "urgency of need designator",
        "Military Standard Requisitioning and Issue Procedures",
        "Uniform Material Movement and Issue Priority System",
        "Commercial Buying Service", "commercial buying service",
        "Tailored Vendor Logistics", "tailored vendor logistics",
        "Parts and Repair Ordering System", "parts and repair ordering system",
        "Repair and Return", "repair and return",
        
        # Document expansions
        "Supply Discrepancy Report", "supply discrepancy report",
        "Federal Acquisition Regulation", "federal acquisition regulation",
        "Defense FAR Supplement", "defense far supplement",
        "Competition in Contracting Act", "competition in contracting act",
        "supply discrepancy", "discrepancies",
        "minimum value", "minimal-dollar value",
        
        # Review expansions
        "Financial Management Review", "financial management review",
        "Program Management Review", "program management review",
        "Security Assistance Review", "security assistance review",
        "Security Assistance Management Review",
        "case review", "case reviews",
        
        # Amendment/Modification expansions
        "Amendments", "amendments", "Modifications", "modifications",
        "pen and ink", "Pen and Ink Changes",
        "International Agreement exception", "international agreement exception",
        
        # Special program expansions
        "Euro-NATO Joint Jet Pilot Training Program",
        "Euro NATO Joint Jet Pilot Training Program",
        "euro nato joint jet pilot training program",
        "Electronic Combat International Security Assistance Program",
        
        # Financial expansions
        "Defense Working Capital Fund", "defense working capital fund",
        "Small Case Management Line", "small case management line",
        "FMS Administrative Surcharge", "fms administrative surcharge",
        "Financial Policy and Regional Execution Directorate",
        "Defense Finance and Accounting Services Indianapolis",
        "defense finance and accounting services indianapolis",
        
        # Organization expansions
        "International Operations", "international operations",
        "International Operations Global Execution Directorate",
        "Strategy Plans and Policy", "strategy plans and policy",
        "Office of Business Operations", "office of business operations",
        "Returns", "returns", "offsets",
        
        # FMSO variations
        "Foreign Military Sales Order", "foreign military sales order",
        "FMSO I maturity", "fmso i maturity",
        "Foreign Military Sales Order I", "Foreign Military Sales Order II",
        "foreign military sales order i", "foreign military sales order ii",
        
        # Plurals (NOT hallucinations!)
        "Amendments", "amendments", "Modifications", "modifications",
        "FMS cases", "fms cases", "FMS case", "fms case",
        "case reviews", "Case Reviews", "discrepancies", "Discrepancies",
        "Offsets", "offsets",
        
        # Compound entities from queries
        "International Agreement exception", "international agreement exception",
        "minimal-dollar value", "Minimal-Dollar Value",
        "Reactivation Authorized Milestone", "reactivation authorized milestone",
        "supply discrepancy", "Supply Discrepancy",
        "Pen and Ink Changes", "pen and ink changes",
        
        # Parent acronyms (valid extractions)
        "OBO", "obo", "SPP", "spp", "IOPS", "iops",
        "OBO/FPRE", "obo/fpre", "IOPS/GEX", "iops/gex",
        "WCF", "wcf", "Working Capital Fund", "working capital fund",
        "SA", "sa", "Security Assistance", "security assistance",
        
        # Full program names
        "Euro NATO Joint Jet Pilot Training Program",
        "Euro-NATO Joint Jet Pilot Training Program",
        "euro nato joint jet pilot training program",
        
        # Common terms used in tests
        "longest phase", "10 years", "one year", "$200", "$50,000",
        "within-scope", "change in scope", "administrative",
        "purchaser acceptance", "unilateral", "not authorized",
        "10 business days", "15 business days", "six months",
        "non-refundable", "$15,000", "$0", "$1",
        
        # Acronyms
        "EI", "ei", "OA", "oa", "SSC", "ssc",
        "DSAMS", "dsams", "DIFS", "difs", "CPRS", "cprs",
        "DFAS", "dfas", "DFAS-IN", "dfas-in", "CFD", "cfd",
        "SDR", "sdr", "FAR", "far", "DFARS", "dfars",
        "F/AD", "f/ad", "CLSSA", "clssa", "FMSO", "fmso",
        "ETP", "etp", "SCML", "scml", "DWCF", "dwcf",
    }
    
    all_entities.update(VALID_EXPANSIONS)
    
    return all_entities

# =============================================================================
# PRINT SUMMARY
# =============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("CHAPTER 6 ENTITY IMPLEMENTATION SUMMARY")
    print("FMS Case Implementation and Execution")
    print("=" * 80)
    
    print(f"\n📊 NEW ACRONYM PAIRS: {len(CHAPTER_6_ACRONYM_PAIRS)}")
    print(f"📊 GROUND TRUTH CATEGORIES:")
    for cat, entities in CHAPTER_6_GROUND_TRUTH.items():
        print(f"   - {cat}: {len(entities)} entities")
    
    print(f"\n📊 ENTITY PATTERNS:")
    for cat, patterns in CHAPTER_6_ENTITY_PATTERNS.items():
        print(f"   - {cat}: {len(patterns)} patterns")
    
    print(f"\n📊 TEST CASES:")
    total_tests = 0
    for pattern_name, pattern_data in TEST_CASES_CHAPTER_6.items():
        count = len(pattern_data["tests"])
        total_tests += count
        print(f"   - {pattern_name}: {count} tests")
    print(f"   TOTAL: {total_tests} tests")
    
    print(f"\n📊 ENTITY RELATIONSHIPS: {len(CHAPTER_6_ENTITY_RELATIONSHIPS)} relationship groups")
