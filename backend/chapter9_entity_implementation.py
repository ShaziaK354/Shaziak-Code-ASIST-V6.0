"""
SAMM Chapter 9 Entity Implementation
=====================================

Chapter 9: Financial Policies and Procedures

This module contains:
1. Chapter 9 Ground Truth Entities
2. Chapter 9 Specific Acronym Pairs
3. Chapter 9 Entity Patterns
4. Chapter 9 Entity Relationships
5. Chapter 9 Test Cases (90 tests - 18 patterns × 5)

Chapter 9 covers:
- C9.1: Purpose - Financial Policies And Procedures
- C9.2: Financial Management Legal Provisions
- C9.3: General Financial Policies
- C9.4: Specific Line Item Pricing Information
- C9.5: Foreign Military Sales Charges
- C9.6: Pricing Waivers
- C9.7: Methods Of Financing
- C9.8: Letters Of Offer And Acceptance - Terms Of Sale
- C9.9: Payment Schedules
- C9.10: Billing
- C9.11: Foreign Military Sales Payments From Purchasers
- C9.12: Disbursement For Foreign Military Sales Agreements
- C9.13: Performance Reporting
- C9.14: Financial Reviews
- C9.15: FMS Trust Fund Administrative Surcharge Account Management
- C9.16: FMS Contract Administration Services Cost Clearing Account
- C9.17: FMS Trust Fund Transportation Cost Clearing Account
- C9.18: Program Support Charge
"""

# =============================================================================
# CHAPTER 9 SPECIFIC ACRONYM PAIRS (NEW - Not in Chapters 1-8)
# =============================================================================
CHAPTER_9_ACRONYM_PAIRS = {
    # Financial Management Terms
    "fms trust fund": "foreign military sales trust fund",
    "nc": "nonrecurring cost",
    "ncr": "nonrecurring cost recoupment",
    "sdaf": "special defense acquisition fund",
    "ucr": "unfunded civilian retirement",
    "merhc": "medicare-eligible retiree health care",
    "bos": "base operating support",
    "tla": "travel and living allowance",
    "pe": "price element",
    "cc": "contract cost",
    "tl": "termination liability",
    
    # Payment & Billing Terms
    "du": "dependable undertaking",
    "raps": "risk assessed payment schedules",
    "caps": "credit assured payment schedules",
    "bloc": "bank letter of credit",
    "lc": "letter of credit",
    "sblc": "standby letter of credit",
    "sba": "special billing arrangement",
    "sbl": "special bill letter",
    "tcv": "total case value",
    "dd 645": "billing statement form",
    "dd form 645": "billing statement form",
    
    # Pricing Components
    "ipc": "indirect pricing component",
    "pcc": "primary category code",
    "lsc": "logistics support charge",
    "psc": "program support charge",
    "cas": "contract administration services",
    "pc&h": "packing crating and handling",
    "dtc": "delivery term code",
    
    # Administrative
    "pml": "program management line",
    "scml": "small case management line",
    "mtds": "manpower travel data sheets",
    "fte": "full-time equivalent",
    "wy": "work year",
    
    # Organizations (C9 Specific)
    "obo/fpre": "financial policy and regional execution directorate",
    "obo/fpre/fp": "financial policy division",
    "iops/gex": "international operations global execution directorate",
    "iops/gex/cwd": "case writing and development division",
    "cfm": "country financial management division",
    "dbo": "directorate of business operations",
    
    # Financial Systems
    "fmscs": "fms credit system",
    "mcr": "monthly case report",
    "sf 1081": "voucher and schedule of withdrawals and credits",
    "of 1017-g": "journal voucher form",
    
    # NATO/International
    "nspa": "nato support and procurement agency",
    "nspo": "nato support organization",
    "shape": "supreme headquarters allied powers europe",
    "nsip": "nato security investment program",
    "nicsma": "nato integrated communication system management agency",
    "epg": "european participating governments",
    "mfp": "major force program",
    
    # Legal References
    "22 usc 2761": "aeca section 21",
    "22 usc 2762": "aeca section 22",
    "22 usc 2763": "aeca section 23",
    "22 usc 2764": "aeca section 24",
    "22 usc 2769": "aeca section 29",
    "22 usc 2774": "aeca section 34",
    "22 usc 2777": "aeca section 37",
    "22 usc 2791": "aeca section 42",
    "22 usc 2792": "aeca section 43",
    "22 usc 2795": "aeca section 51",
    "ffb": "federal financing bank",
    
    # Tuition/Training Rates
    "rate a": "full cost tuition rate",
    "rate c": "incremental tuition rate",
    "rate d": "tuition rate d",
    "rate e": "tuition rate e",
    
    # Waivers
    "qa": "quality assurance",
    "qai": "quality assurance and inspection",
    
    # Other Terms
    "npor": "non-program of record",
    "ufr": "unfunded requirement",
    "mou": "memorandum of understanding",
    "opm": "office of personnel management",
    "saam": "special assignment airlift mission",
}

# =============================================================================
# CHAPTER 9 GROUND TRUTH ENTITIES
# =============================================================================
CHAPTER_9_GROUND_TRUTH = {
    # Organizations (C9.1 - C9.18)
    "organizations": {
        # DSCA Offices
        "DSCA", "Defense Security Cooperation Agency",
        "OBO", "Office of Business Operations",
        "OBO/FPRE", "Financial Policy & Regional Execution Directorate",
        "OBO/FPRE/FP", "Financial Policy Division",
        "OBO/IMT", "Information Management and Technology Directorate",
        "IOPS", "Office of International Operations",
        "IOPS/GEX", "Global Execution Directorate",
        "IOPS/GEX/CWD", "Case Writing and Development Division",
        "SPP", "Office of Strategy, Plans, and Policy",
        "CFD", "Country Finance Director",
        "CPD", "Country Portfolio Director",
        "CFM", "Country Financial Management Division",
        "DBO", "Directorate of Business Operations",
        
        # Financial Organizations
        "DFAS", "Defense Finance and Accounting Service",
        "DFAS-IN", "Defense Finance and Accounting Services - Indianapolis",
        "FRB", "Federal Reserve Bank",
        "FFB", "Federal Financing Bank",
        "OPM", "Office of Personnel Management",
        
        # DoD Components
        "DoD", "Department of Defense",
        "MILDEP", "MILDEPS", "Military Department",
        "IA", "IAS", "Implementing Agency",
        "DLA", "Defense Logistics Agency",
        "OSD", "Office of the Secretary of Defense",
        
        # Defense Officials
        "USD(P)", "Under Secretary of Defense for Policy",
        "USD(A&S)", "Under Secretary of Defense for Acquisition and Sustainment",
        "USD(C)", "Under Secretary of Defense Comptroller",
        
        # State Department
        "State", "Department of State",
        "PM/RSAT", "Bureau of Political-Military Affairs, Office of Regional Security and Arms Transfers",
        
        # NATO Organizations
        "NATO", "North Atlantic Treaty Organization",
        "NSPA", "NATO Support and Procurement Agency",
        "NSPO", "NATO Support Organization",
        "SHAPE", "Supreme Headquarters Allied Powers Europe",
        "NICSMA", "NATO Integrated Communication System Management Agency",
        
        # Other
        "SCO", "SCOS", "Security Cooperation Organization",
        "DCAA", "Defense Contract Audit Agency",
        "DCMA", "Defense Contract Management Agency",
    },
    
    # Documents & Forms (C9.1 - C9.18)
    "documents": {
        # Core Documents
        "LOA", "Letter of Offer and Acceptance",
        "LOR", "Letter of Request",
        "MOU", "Memorandum of Understanding",
        "LOAD", "LOA Data",
        
        # Billing Forms
        "DD 645", "DD Form 645", "Billing Statement",
        "SF 1081", "Voucher and Schedule of Withdrawals and Credits",
        "OF 1017-G", "Journal Voucher",
        "SBL", "Special Bill Letter",
        
        # Regulations
        "AECA", "Arms Export Control Act",
        "FAA", "Foreign Assistance Act",
        "DoD FMR", "DoD Financial Management Regulation",
        "DoD 7000.14-R", "DoD Financial Management Regulation Volume 15",
        "FAR", "Federal Acquisition Regulation",
        "DFARS", "Defense Federal Acquisition Regulation Supplement",
        
        # Manpower Documents
        "MTDS", "Manpower Travel Data Sheets",
        
        # Tables
        "Table C9.T1", "Financial Management Legal References",
        "Table C9.T2A", "FMS Case-Related Manpower Functions Matrix",
        "Table C9.T2B", "BPC Case-Related Manpower Functions Matrix",
        "Table C9.T2C", "NPOR Manpower Functions Matrix",
        "Table C9.T3", "Historical Rules for Program Management Lines",
        "Table C9.T4", "Table of Charges",
        "Table C9.T4A", "Delivery Term Codes and Percentages",
        "Table C9.T5", "Reciprocal Country Agreement Listing",
        "Table C9.T6", "Participating Groups Agreements",
        "Table C9.T7", "NATO CAS Reciprocal Agreements",
        "Table C9.T11", "Terms of Sale",
        
        # Figures
        "Figure C9.F1", "Notification Memo Template",
        "Figure C9.F2", "Manpower and Travel Data Sheet",
    },
    
    # Financial Concepts (C9.3 - C9.18)
    "financial_concepts": {
        # Fund Types
        "FMS Trust Fund", "Foreign Military Sales Trust Fund",
        "FMS Administrative Surcharge", "FMS Admin",
        "FMS Administrative Surcharge Account",
        "SDAF", "Special Defense Acquisition Fund",
        "WCF", "Working Capital Fund",
        "DWCF", "Defense Working Capital Fund",
        "FMF", "Foreign Military Financing",
        "MAP", "Military Assistance Program",
        "MAP Merger",
        
        # Pricing Components
        "IPC", "Indirect Pricing Component",
        "PCC", "Primary Category Code",
        "PE", "Price Element",
        "NC", "Nonrecurring Cost",
        "NCR", "Nonrecurring Cost Recoupment",
        "CAS", "Contract Administration Services",
        "LSC", "Logistics Support Charge",
        "PSC", "Program Support Charge",
        "PC&H", "Packing Crating and Handling",
        "DTC", "Delivery Term Code",
        
        # Cost Types
        "direct charges", "indirect charges",
        "above-the-line charges", "below-the-line charges",
        "accessorial charges", "surcharges",
        "termination liability", "TL",
        "initial deposit",
        "UCR", "Unfunded Civilian Retirement",
        "MERHC", "Medicare-Eligible Retiree Health Care",
        
        # Management Lines
        "PML", "Program Management Line",
        "SCML", "Small Case Management Line",
        "Generic Code R6B", "Generic Code L8A", "Generic Code R6C",
    },
    
    # Payment Terms (C9.7 - C9.11)
    "payment_terms": {
        # Terms of Sale
        "Cash with Acceptance", "CWA",
        "Cash Prior to Delivery",
        "Dependable Undertaking", "DU",
        "Cash Flow Financing",
        "Payment on Delivery",
        
        # Payment Schedules
        "RAPS", "Risk Assessed Payment Schedules",
        "CAPS", "Credit Assured Payment Schedules",
        "payment schedule",
        
        # Financing Methods
        "national funds", "cash",
        "third-party funds", "private financing",
        "BLOC", "Bank Letter of Credit",
        "LC", "Letter of Credit",
        "SBLC", "Standby Letter of Credit",
        "SBA", "Special Billing Arrangement",
        
        # Billing
        "quarterly billing", "DD 645",
        "Special Bill Letter", "SBL",
        "advance cash requirements",
        "cash summary account",
    },
    
    # Waivers (C9.6)
    "waivers": {
        "FMS Administrative Surcharge Waiver",
        "CAS Waiver", "Contract Administration Services Waiver",
        "NC Waiver", "Nonrecurring Cost Waiver",
        "QA Waiver", "Quality Assurance Waiver",
        "Tooling Rental Waiver",
        "reciprocal agreement",
        "loss of sale waiver",
        "NATO standardization",
    },
    
    # Training/Tuition (C9.4.3)
    "training": {
        "IMET", "International Military Education and Training",
        "E-IMET", "Expanded IMET",
        "Rate A", "full cost tuition",
        "Rate B",
        "Rate C", "incremental tuition rate",
        "Rate D",
        "Rate E",
        "tuition rates",
        "attrition charges",
        "TLA", "Travel and Living Allowance",
        "fringe benefits",
        "civilian fringe benefits",
        "military fringe benefits",
    },
    
    # Manpower (C9.4.2)
    "manpower": {
        "MTDS", "Manpower Travel Data Sheets",
        "FTE", "full-time equivalent",
        "WY", "Work Year",
        "USG contracted manpower",
        "case-funded manpower",
        "CONUS", "Continental United States",
        "OCONUS", "Outside Continental United States",
        "base salary",
        "leave and holiday factor",
    },
    
    # Processes (C9.1 - C9.18)
    "processes": {
        "pricing estimates", "billing and reporting",
        "LOA pricing", "line item pricing",
        "case development", "pre-LOR activities",
        "financial implementation",
        "disbursement", "collection",
        "financial review", "FMR", "Financial Management Review",
        "performance reporting",
        "case reconciliation",
        "materiality assessment",
        "cost recovery",
    },
    
    # Systems (C9)
    "systems": {
        "DSAMS", "Defense Security Assistance Management System",
        "DIFS", "Defense Integrated Financial System",
        "CTS", "Case Tracking System",
        "FMSCS", "FMS Credit System",
        "MCR", "Monthly Case Report",
    },
}

# =============================================================================
# CHAPTER 9 ENTITY PATTERNS
# =============================================================================
CHAPTER_9_ENTITY_PATTERNS = {
    "financial_patterns": [
        r"\bFMS\s+Trust\s+Fund\b",
        r"\bFMS\s+Administrative\s+Surcharge\b",
        r"\binitial\s+deposit\b",
        r"\bcash\s+requirements?\b",
        r"\bpayment\s+schedule\b",
        r"\bbilling\s+statement\b",
        r"\bDD\s*645\b",
        r"\bnonrecurring\s+cost(?:s)?\b",
        r"\btermination\s+liability\b",
    ],
    "pricing_patterns": [
        r"\bline\s+item\s+pricing\b",
        r"\bdirect\s+charges?\b",
        r"\bindirect\s+charges?\b",
        r"\baccessorial\s+charges?\b",
        r"\babove[\s-]the[\s-]line\b",
        r"\bbelow[\s-]the[\s-]line\b",
        r"\bPrice\s+Element\b",
        r"\bPrimary\s+Category\s+Code\b",
    ],
    "payment_patterns": [
        r"\bCash\s+with\s+Acceptance\b",
        r"\bDependable\s+Undertaking\b",
        r"\bCash\s+Flow\s+Financing\b",
        r"\bRisk\s+Assessed\s+Payment\b",
        r"\bCredit\s+Assured\s+Payment\b",
        r"\bStandby\s+Letter\s+of\s+Credit\b",
        r"\bLetter\s+of\s+Credit\b",
        r"\bSpecial\s+Billing\s+Arrangement\b",
    ],
    "waiver_patterns": [
        r"\b(?:FMS\s+)?Administrative\s+Surcharge\s+(?:W|w)aiver\b",
        r"\bCAS\s+(?:W|w)aiver\b",
        r"\bNC\s+(?:W|w)aiver\b",
        r"\bNonrecurring\s+Cost\s+(?:W|w)aiver\b",
        r"\breciprocal\s+agreement\b",
        r"\bloss\s+of\s+sale\b",
    ],
    "training_patterns": [
        r"\bRate\s+[A-E]\b",
        r"\bfull\s+cost\s+tuition\b",
        r"\bincremental\s+(?:tuition\s+)?rate\b",
        r"\battrition\s+charges?\b",
        r"\bfringe\s+benefits?\b",
    ],
    "manpower_patterns": [
        r"\bManpower\s+Travel\s+Data\s+Sheet\b",
        r"\bMTDS\b",
        r"\bWork\s+Year\b",
        r"\bfull[\s-]time\s+equivalent\b",
        r"\bcase[\s-]funded\s+manpower\b",
    ],
    "management_line_patterns": [
        r"\bProgram\s+Management\s+Line\b",
        r"\bPML\b",
        r"\bSmall\s+Case\s+Management\s+Line\b",
        r"\bSCML\b",
        r"\bGeneric\s+Code\s+[A-Z]\d[A-Z]\b",
    ],
}

# =============================================================================
# CHAPTER 9 ENTITY RELATIONSHIPS
# =============================================================================
CHAPTER_9_ENTITY_RELATIONSHIPS = {
    # FMS Trust Fund Relationships (C9.3.10)
    "FMS Trust Fund": ["payments from purchasers", "disbursements", "DSCA manages", "purchaser account solvency"],
    
    # Payment Terms Relationships (C9.7-C9.8)
    "Dependable Undertaking": ["eligible purchasers", "payment schedule", "RAPS eligibility"],
    "Cash with Acceptance": ["initial deposit equals TCV", "no payment schedule"],
    "CAPS": ["requires SBLC", "75% TCV minimum", "CFD monitors"],
    "SBLC": ["issued by bank", "DSCA beneficiary", "supports CAPS"],
    
    # Pricing Relationships (C9.4)
    "NC": ["MDE items", "waiver possible", "prorated charge"],
    "CAS": ["procurement lines", "reciprocal waiver", "NATO agreements"],
    "FMS Administrative Surcharge": ["calculated on case value", "SCML minimum", "waiver requires reimbursement"],
    
    # Billing Relationships (C9.10)
    "DD 645": ["quarterly billing", "DFAS prepares", "cash requirements"],
    "SBL": ["supersedes DD 645", "SBA established", "custom frequency"],
    
    # Manpower Relationships (C9.4.2)
    "MTDS": ["validates manpower costs", "DSAMS format", "LOA requirement"],
    "PML": ["pre-August 2006", "Generic Code R6B", "no surcharge"],
    
    # Waiver Relationships (C9.6)
    "CAS Waiver": ["reciprocal agreement", "Table C9.T5 countries", "QA and inspection"],
    "NC Waiver": ["loss of sale", "NATO standardization", "DSCA Director approval"],
}

# =============================================================================
# TEST CASES - 90 TESTS FOR CHAPTER 9 (18 patterns × 5)
# =============================================================================
TEST_CASES_CHAPTER_9 = {
    # Pattern 1: Financial Policies Overview (C9.1-C9.2)
    "pattern_c9_1_overview": {
        "description": "Financial Policies Overview queries",
        "tests": [
            {"id": 901, "query": "What is the purpose of Chapter 9 Financial Policies and Procedures?",
             "expected": ["fms"]},
            {"id": 902, "query": "What are the two critical financial functions in FMS case life cycle?",
             "expected": ["fms", "loa"]},
            {"id": 903, "query": "What is the DoD FMR Volume 15?",
             "expected": ["dod fmr"]},
            {"id": 904, "query": "What legal references govern FMS financial management under AECA?",
             "expected": ["aeca", "fms"]},
            {"id": 905, "query": "What does Table C9.T1 contain?",
             "expected": ["table c9.t1"]},
        ]
    },
    
    # Pattern 2: FMS Trust Fund (C9.3.10)
    "pattern_c9_2_trust_fund": {
        "description": "FMS Trust Fund queries",
        "tests": [
            {"id": 906, "query": "What is the FMS Trust Fund?",
             "expected": ["fms trust fund"]},
            {"id": 907, "query": "Who manages the FMS Trust Fund? Is it DSCA?",
             "expected": ["dsca", "fms trust fund"]},
            {"id": 908, "query": "How are payments handled in the FMS Trust Fund?",
             "expected": ["fms trust fund"]},
            {"id": 909, "query": "What is DSCA responsibility for FMS Trust Fund?",
             "expected": ["dsca", "fms trust fund"]},
            {"id": 910, "query": "How are FMS Trust Fund disbursements processed?",
             "expected": ["fms trust fund"]},
        ]
    },
    
    # Pattern 3: Pricing Policies (C9.3-C9.4)
    "pattern_c9_3_pricing": {
        "description": "Pricing policies and line item pricing queries",
        "tests": [
            {"id": 911, "query": "What is LOA line item pricing?",
             "expected": ["loa", "line item pricing"]},
            {"id": 912, "query": "What are direct charges vs indirect charges in FMS?",
             "expected": ["direct charges", "indirect charges", "fms"]},
            {"id": 913, "query": "What are above-the-line and below-the-line charges?",
             "expected": ["above-the-line", "below-the-line"]},
            {"id": 914, "query": "What is a Primary Category Code PCC?",
             "expected": ["pcc", "primary category code"]},
            {"id": 915, "query": "What are Indirect Pricing Components IPC?",
             "expected": ["ipc", "indirect pricing component"]},
        ]
    },
    
    # Pattern 4: FMS Administrative Surcharge (C9.3.4, C9.6.1)
    "pattern_c9_4_admin_surcharge": {
        "description": "FMS Administrative Surcharge queries",
        "tests": [
            {"id": 916, "query": "What is the FMS Administrative Surcharge?",
             "expected": ["fms administrative surcharge"]},
            {"id": 917, "query": "How is the FMS Administrative Surcharge calculated?",
             "expected": ["fms administrative surcharge"]},
            {"id": 918, "query": "What is the eight percent limit on pre-LOR activities for FMS Admin?",
             "expected": ["pre-lor", "fms admin"]},
            {"id": 919, "query": "When can the FMS Administrative Surcharge be waived?",
             "expected": ["fms administrative surcharge"]},
            {"id": 920, "query": "What is the FMS Administrative Surcharge Account?",
             "expected": ["fms administrative surcharge account"]},
        ]
    },
    
    # Pattern 5: SCML - Small Case Management Line (C9.4.7)
    "pattern_c9_5_scml": {
        "description": "Small Case Management Line queries",
        "tests": [
            {"id": 921, "query": "What is the Small Case Management Line SCML?",
             "expected": ["scml", "small case management line"]},
            {"id": 922, "query": "When is SCML applied to FMS cases?",
             "expected": ["scml", "fms"]},
            {"id": 923, "query": "What is the $15,000 minimum for SCML?",
             "expected": ["scml", "$15,000"]},
            {"id": 924, "query": "What Generic Code R6C is used for SCML?",
             "expected": ["scml", "generic code r6c"]},
            {"id": 925, "query": "When was SCML rescinded in July 2012?",
             "expected": ["scml"]},
        ]
    },
    
    # Pattern 6: Nonrecurring Cost (C9.4.5)
    "pattern_c9_6_nc": {
        "description": "Nonrecurring Cost Recoupment queries",
        "tests": [
            {"id": 926, "query": "What is Nonrecurring Cost NC in FMS?",
             "expected": ["nc", "nonrecurring cost", "fms"]},
            {"id": 927, "query": "How are NC Nonrecurring Cost charges approved by DSCA?",
             "expected": ["nc", "dsca"]},
            {"id": 928, "query": "What is the NC waiver process?",
             "expected": ["nc waiver"]},
            {"id": 929, "query": "When can NC charges be waived for NATO?",
             "expected": ["nc", "nato"]},
            {"id": 930, "query": "How is NC reported on DSCA reports?",
             "expected": ["nc", "dsca"]},
        ]
    },
    
    # Pattern 7: Contract Administration Services CAS (C9.5, C9.6.2)
    "pattern_c9_7_cas": {
        "description": "Contract Administration Services queries",
        "tests": [
            {"id": 931, "query": "What is Contract Administration Services CAS?",
             "expected": ["cas", "contract administration services"]},
            {"id": 932, "query": "How is CAS applied to FMS procurement?",
             "expected": ["cas", "fms"]},
            {"id": 933, "query": "What is a CAS waiver?",
             "expected": ["cas waiver"]},
            {"id": 934, "query": "Which countries have CAS agreements in Table C9.T5?",
             "expected": ["cas", "table c9.t5"]},
            {"id": 935, "query": "How does NATO CAS waiver work in Table C9.T7?",
             "expected": ["cas", "nato", "table c9.t7"]},
        ]
    },
    
    # Pattern 8: Terms of Sale (C9.8)
    "pattern_c9_8_terms_sale": {
        "description": "Terms of Sale queries",
        "tests": [
            {"id": 936, "query": "What are the FMS Terms of Sale?",
             "expected": ["terms of sale", "fms"]},
            {"id": 937, "query": "What is Cash with Acceptance CWA?",
             "expected": ["cwa", "cash with acceptance"]},
            {"id": 938, "query": "What is Dependable Undertaking DU?",
             "expected": ["du", "dependable undertaking"]},
            {"id": 939, "query": "What is Cash Flow Financing?",
             "expected": ["cash flow financing"]},
            {"id": 940, "query": "What are Risk Assessed Payment Schedules RAPS?",
             "expected": ["raps", "risk assessed payment schedules"]},
        ]
    },
    
    # Pattern 9: CAPS and SBLC (C9.8.5)
    "pattern_c9_9_caps": {
        "description": "Credit Assured Payment Schedules queries",
        "tests": [
            {"id": 941, "query": "What is Credit Assured Payment Schedules CAPS?",
             "expected": ["caps", "credit assured payment schedules"]},
            {"id": 942, "query": "What is a Standby Letter of Credit SBLC?",
             "expected": ["sblc", "standby letter of credit"]},
            {"id": 943, "query": "What is the 75% TCV requirement for SBLC?",
             "expected": ["sblc", "tcv"]},
            {"id": 944, "query": "How does CFD monitor CAPS?",
             "expected": ["cfd", "caps"]},
            {"id": 945, "query": "What happens when SBLC is terminated?",
             "expected": ["sblc"]},
        ]
    },
    
    # Pattern 10: Payment Schedules (C9.9)
    "pattern_c9_10_payment": {
        "description": "Payment Schedules queries",
        "tests": [
            {"id": 946, "query": "What are FMS payment schedules?",
             "expected": ["payment schedule", "fms"]},
            {"id": 947, "query": "How is initial deposit calculated for FMS?",
             "expected": ["initial deposit", "fms"]},
            {"id": 948, "query": "What is advance cash requirement?",
             "expected": ["advance cash"]},
            {"id": 949, "query": "How are payment schedules revised for LOA Amendments?",
             "expected": ["payment schedule", "loa"]},
            {"id": 950, "query": "What is termination liability TL?",
             "expected": ["tl", "termination liability"]},
        ]
    },
    
    # Pattern 11: Billing (C9.10)
    "pattern_c9_11_billing": {
        "description": "FMS Billing queries",
        "tests": [
            {"id": 951, "query": "What is the DD 645 Billing Statement?",
             "expected": ["dd 645", "billing statement"]},
            {"id": 952, "query": "When are FMS quarterly bills issued?",
             "expected": ["quarterly billing", "fms"]},
            {"id": 953, "query": "What is a Special Billing Arrangement SBA?",
             "expected": ["sba", "special billing arrangement"]},
            {"id": 954, "query": "What is a Special Bill Letter SBL?",
             "expected": ["sbl", "special bill letter"]},
            {"id": 955, "query": "How does DFAS prepare billing statements?",
             "expected": ["dfas", "billing statement"]},
        ]
    },
    
    # Pattern 12: Letter of Credit (C9.7.1.2)
    "pattern_c9_12_loc": {
        "description": "Letter of Credit and Bank Financing queries",
        "tests": [
            {"id": 956, "query": "What is a Bank Letter of Credit BLOC?",
             "expected": ["bloc", "bank letter of credit"]},
            {"id": 957, "query": "How is Letter of Credit LC used for FMS?",
             "expected": ["lc", "letter of credit", "fms"]},
            {"id": 958, "query": "What are the LC Letter of Credit eligibility requirements?",
             "expected": ["lc", "letter of credit"]},
            {"id": 959, "query": "How is LC replenishment handled?",
             "expected": ["lc"]},
            {"id": 960, "query": "What is the MOU requirement for LC?",
             "expected": ["mou", "lc"]},
        ]
    },
    
    # Pattern 13: Manpower and MTDS (C9.4.2)
    "pattern_c9_13_manpower": {
        "description": "Manpower and MTDS queries",
        "tests": [
            {"id": 961, "query": "What are Manpower Travel Data Sheets MTDS?",
             "expected": ["mtds", "manpower travel data sheets"]},
            {"id": 962, "query": "How is Work Year WY calculated?",
             "expected": ["wy", "work year"]},
            {"id": 963, "query": "What is full-time equivalent FTE manpower?",
             "expected": ["fte", "full-time equivalent"]},
            {"id": 964, "query": "How does DSCA review MTDS?",
             "expected": ["dsca", "mtds"]},
            {"id": 965, "query": "What are MTDS exemptions?",
             "expected": ["mtds"]},
        ]
    },
    
    # Pattern 14: Program Management Lines (C9.4.2.3)
    "pattern_c9_14_pml": {
        "description": "Program Management Line queries",
        "tests": [
            {"id": 966, "query": "What is a Program Management Line PML?",
             "expected": ["pml", "program management line"]},
            {"id": 967, "query": "When were PMLs used before August 2006?",
             "expected": ["pml"]},
            {"id": 968, "query": "What Generic Code R6B was used for PML?",
             "expected": ["pml", "generic code r6b"]},
            {"id": 969, "query": "What types of sales include PMLs?",
             "expected": ["pml"]},
            {"id": 970, "query": "How are program management services tracked?",
             "expected": ["program management services"]},
        ]
    },
    
    # Pattern 15: Training Tuition Rates (C9.4.3)
    "pattern_c9_15_tuition": {
        "description": "Training Tuition Rates queries",
        "tests": [
            {"id": 971, "query": "What is Rate A full cost tuition?",
             "expected": ["rate a", "full cost tuition"]},
            {"id": 972, "query": "What is Rate C incremental tuition?",
             "expected": ["rate c", "incremental tuition"]},
            {"id": 973, "query": "How does IMET status affect tuition rates?",
             "expected": ["imet", "tuition rates"]},
            {"id": 974, "query": "What are attrition charges for FMS training?",
             "expected": ["attrition charges", "fms"]},
            {"id": 975, "query": "What are civilian fringe benefits?",
             "expected": ["civilian fringe benefits"]},
        ]
    },
    
    # Pattern 16: Financial Reviews (C9.14)
    "pattern_c9_16_reviews": {
        "description": "Financial Review queries",
        "tests": [
            {"id": 976, "query": "What is a Financial Management Review FMR?",
             "expected": ["fmr", "financial management review"]},
            {"id": 977, "query": "How are FMS financial reviews conducted?",
             "expected": ["financial review", "fms"]},
            {"id": 978, "query": "What is performance reporting?",
             "expected": ["performance reporting"]},
            {"id": 979, "query": "How does OBO/FPRE manage financial policy?",
             "expected": ["obo/fpre", "financial policy"]},
            {"id": 980, "query": "What is the role of Country Finance Director CFD?",
             "expected": ["cfd", "country finance director"]},
        ]
    },
    
    # Pattern 17: SDAF and Fund Deposits (C9.4.8)
    "pattern_c9_17_sdaf": {
        "description": "Special Defense Acquisition Fund queries",
        "tests": [
            {"id": 981, "query": "What is the Special Defense Acquisition Fund SDAF?",
             "expected": ["sdaf", "special defense acquisition fund"]},
            {"id": 982, "query": "How are sales from stock proceeds deposited to SDAF?",
             "expected": ["sales from stock", "sdaf"]},
            {"id": 983, "query": "What is sale with intent to replace?",
             "expected": ["sale with intent to replace"]},
            {"id": 984, "query": "What is sale without intent to replace?",
             "expected": ["sale without intent to replace"]},
            {"id": 985, "query": "How are munitions valued for FMS?",
             "expected": ["munitions", "fms"]},
        ]
    },
    
    # Pattern 18: NATO and International Agreements (C9.6)
    "pattern_c9_18_nato": {
        "description": "NATO and International Agreement queries",
        "tests": [
            {"id": 986, "query": "What is the NATO CAS waiver for NSPA?",
             "expected": ["nato", "cas", "nspa"]},
            {"id": 987, "query": "What is NSIP NATO Security Investment Program?",
             "expected": ["nsip", "nato security investment program"]},
            {"id": 988, "query": "How do reciprocal agreements work?",
             "expected": ["reciprocal agreement"]},
            {"id": 989, "query": "What is the SHAPE CAS waiver?",
             "expected": ["shape", "cas"]},
            {"id": 990, "query": "What are European Participating Governments EPG?",
             "expected": ["epg", "european participating governments"]},
        ]
    },
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_all_chapter9_tests():
    """Return all Chapter 9 tests as a flat list"""
    all_tests = []
    for pattern_name, pattern_data in TEST_CASES_CHAPTER_9.items():
        for test in pattern_data["tests"]:
            test["pattern"] = pattern_name
            all_tests.append(test)
    return all_tests

def get_chapter9_ground_truth_entities():
    """Get flattened set of all Chapter 9 ground truth entities INCLUDING all valid expansions"""
    all_entities = set()
    
    # Add all entities from ground truth categories
    for category, entities in CHAPTER_9_GROUND_TRUTH.items():
        all_entities.update(entities)
    
    # Add ALL valid acronym expansions (these are NOT hallucinations!)
    VALID_EXPANSIONS = {
        # Core FMS expansions (NOT hallucinations!)
        "Foreign Military Sales", "foreign military sales",
        "FMS case", "fms case", "FMS cases", "fms cases",
        "Letter Of Offer And Acceptance", "letter of offer and acceptance",
        "Letter Of Request", "letter of request",
        "Defense Security Cooperation Agency", "defense security cooperation agency",
        "Defense Finance And Accounting Service", "defense finance and accounting service",
        "International Military Education And Training", "international military education and training",
        "Office Of Business Operations", "office of business operations",
        
        # Financial expansions
        "Foreign Military Sales Trust Fund", "foreign military sales trust fund",
        "FMS Trust Fund", "fms trust fund",
        "FMS Administrative Surcharge", "fms administrative surcharge",
        "FMS Admin", "fms admin",
        "Foreign Military Financing", "foreign military financing",
        "Special Defense Acquisition Fund", "special defense acquisition fund",
        "Defense Working Capital Fund", "defense working capital fund",
        "Working Capital Fund", "working capital fund",
        
        # Pricing expansions
        "Nonrecurring Cost", "nonrecurring cost", "NC", "nc",
        "Nonrecurring Cost Recoupment", "nonrecurring cost recoupment",
        "Contract Administration Services", "contract administration services",
        "Indirect Pricing Component", "indirect pricing component",
        "Primary Category Code", "primary category code",
        "Delivery Term Code", "delivery term code",
        "Price Element", "price element",
        "Logistics Support Charge", "logistics support charge",
        "Program Support Charge", "program support charge",
        "Packing Crating and Handling", "packing crating and handling",
        "direct charges", "indirect charges",
        "above-the-line", "below-the-line",
        "accessorial charges", "surcharges",
        
        # Payment expansions
        "Dependable Undertaking", "dependable undertaking",
        "Cash with Acceptance", "cash with acceptance",
        "Cash Flow Financing", "cash flow financing",
        "Risk Assessed Payment Schedules", "risk assessed payment schedules",
        "Credit Assured Payment Schedules", "credit assured payment schedules",
        "Standby Letter of Credit", "standby letter of credit",
        "Letter of Credit", "letter of credit",
        "Bank Letter of Credit", "bank letter of credit",
        "Special Billing Arrangement", "special billing arrangement",
        "Special Bill Letter", "special bill letter",
        "payment schedule", "payment schedules",
        "initial deposit", "advance cash",
        "termination liability", "quarterly billing",
        "Total Case Value", "total case value",
        
        # Management Lines
        "Program Management Line", "program management line",
        "Small Case Management Line", "small case management line",
        "Generic Code R6B", "generic code r6b",
        "Generic Code R6C", "generic code r6c",
        "Generic Code L8A", "generic code l8a",
        "$15,000", "minimum", "rescinded", "july 2012",
        "august 2006", "August 2006",
        
        # Manpower expansions
        "Manpower Travel Data Sheets", "manpower travel data sheets",
        "Work Year", "work year",
        "full-time equivalent", "Full-Time Equivalent",
        "case-funded manpower", "USG contracted manpower",
        "base salary", "fringe benefits",
        "leave and holiday factor",
        "civilian fringe benefits", "military fringe benefits",
        
        # Training expansions
        "Rate A", "rate a", "full cost tuition",
        "Rate B", "rate b",
        "Rate C", "rate c", "incremental tuition", "incremental tuition rate",
        "Rate D", "rate d",
        "Rate E", "rate e",
        "tuition rates", "attrition charges",
        "Travel and Living Allowance", "travel and living allowance",
        
        # Organization expansions
        "Financial Policy & Regional Execution Directorate",
        "Financial Policy and Regional Execution Directorate",
        "financial policy and regional execution directorate",
        "Financial Policy Division", "financial policy division",
        "Global Execution Directorate", "global execution directorate",
        "Case Writing and Development Division",
        "Country Finance Director", "country finance director",
        "Country Portfolio Director", "country portfolio director",
        "Country Financial Management Division",
        "Directorate of Business Operations",
        "Defense Finance and Accounting Service",
        "Defense Finance and Accounting Services - Indianapolis",
        "defense finance and accounting services indianapolis",
        
        # NATO expansions
        "North Atlantic Treaty Organization",
        "NATO Support and Procurement Agency",
        "NATO Support Organization",
        "Supreme Headquarters Allied Powers Europe",
        "NATO Security Investment Program",
        "NATO Integrated Communication System Management Agency",
        "European Participating Governments",
        "Major Force Program",
        
        # System expansions
        "Defense Security Assistance Management System",
        "Defense Integrated Financial System",
        "Case Tracking System", "FMS Credit System",
        "Monthly Case Report",
        
        # Waiver expansions
        "FMS Administrative Surcharge Waiver",
        "CAS Waiver", "cas waiver",
        "NC Waiver", "nc waiver",
        "Nonrecurring Cost Waiver", "nonrecurring cost waiver",
        "Quality Assurance Waiver", "quality assurance waiver",
        "reciprocal agreement", "loss of sale",
        "NATO standardization",
        
        # Document expansions
        "DoD Financial Management Regulation",
        "DoD 7000.14-R", "Volume 15",
        "Billing Statement", "billing statement",
        "DD Form 645", "dd form 645",
        "Table C9.T1", "Table C9.T2A", "Table C9.T2B",
        "Table C9.T3", "Table C9.T4", "Table C9.T5",
        "Table C9.T6", "Table C9.T7", "Table C9.T11",
        "Figure C9.F1", "Figure C9.F2",
        
        # Process expansions
        "pricing estimates", "billing and reporting",
        "LOA pricing", "line item pricing",
        "case development", "pre-LOR activities", "pre-lor",
        "financial implementation",
        "disbursement", "collection",
        "Financial Management Review", "financial management review",
        "performance reporting",
        "case reconciliation",
        "materiality assessment", "cost recovery",
        
        # Acronyms
        "FMS", "fms", "LOA", "loa", "LOR", "lor",
        "NC", "nc", "NCR", "ncr",
        "CAS", "cas", "DTC", "dtc",
        "IPC", "ipc", "PCC", "pcc", "PE", "pe",
        "LSC", "lsc", "PSC", "psc",
        "TL", "tl", "TCV", "tcv",
        "PML", "pml", "SCML", "scml",
        "MTDS", "mtds", "WY", "wy", "FTE", "fte",
        "DU", "du", "RAPS", "raps", "CAPS", "caps",
        "SBLC", "sblc", "BLOC", "bloc", "LC", "lc",
        "SBA", "sba", "SBL", "sbl",
        "SDAF", "sdaf", "WCF", "wcf", "DWCF", "dwcf",
        "FMF", "fmf", "MAP", "map",
        "FMR", "fmr", "MCR", "mcr",
        "MOU", "mou", "OPM", "opm",
        "UCR", "ucr", "MERHC", "merhc",
        "IMET", "imet", "E-IMET", "e-imet",
        "TLA", "tla", "BOS", "bos",
        "NATO", "nato", "NSPA", "nspa",
        "NSPO", "nspo", "SHAPE", "shape",
        "NSIP", "nsip", "NICSMA", "nicsma",
        "EPG", "epg", "MFP", "mfp",
        "FFB", "ffb", "FRB", "frb",
        "DFAS", "dfas", "DFAS-IN", "dfas-in",
        "CFD", "cfd", "CPD", "cpd",
        "OBO", "obo", "IOPS", "iops",
        "OBO/FPRE", "obo/fpre",
        "OBO/FPRE/FP", "obo/fpre/fp",
        "IOPS/GEX", "iops/gex",
        "CFM", "cfm", "DBO", "dbo",
        "DSAMS", "dsams", "DIFS", "difs",
        "CTS", "cts", "FMSCS", "fmscs",
        
        # Common query terms
        "chapter 9", "Chapter 9",
        "financial policies", "financial procedures",
        "calculated", "approved", "waiver", "waived",
        "eligibility", "eligible",
        "75%", "eight percent",
        
        # Common extractions that are NOT hallucinations
        "Amendment", "amendment", "Amendments", "amendments",
        "Modification", "modification",
        "State", "state", "Department of State",
        "DoD", "dod", "Department of Defense",
        "line item", "Line Item",
        "liability", "Liability",
        "Category C", "category c",
    }
    
    all_entities.update(VALID_EXPANSIONS)
    
    return all_entities

# =============================================================================
# PRINT SUMMARY
# =============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("CHAPTER 9 ENTITY IMPLEMENTATION SUMMARY")
    print("Financial Policies and Procedures")
    print("=" * 80)
    
    print(f"\n📊 NEW ACRONYM PAIRS: {len(CHAPTER_9_ACRONYM_PAIRS)}")
    print(f"📊 GROUND TRUTH CATEGORIES:")
    for cat, entities in CHAPTER_9_GROUND_TRUTH.items():
        print(f"   - {cat}: {len(entities)} entities")
    
    print(f"\n📊 ENTITY PATTERNS:")
    for cat, patterns in CHAPTER_9_ENTITY_PATTERNS.items():
        print(f"   - {cat}: {len(patterns)} patterns")
    
    print(f"\n📊 TEST CASES:")
    total_tests = 0
    for pattern_name, pattern_data in TEST_CASES_CHAPTER_9.items():
        count = len(pattern_data["tests"])
        total_tests += count
        print(f"   - {pattern_name}: {count} tests")
    print(f"   TOTAL: {total_tests} tests")
    
    print(f"\n📊 ENTITY RELATIONSHIPS: {len(CHAPTER_9_ENTITY_RELATIONSHIPS)} relationship groups")
