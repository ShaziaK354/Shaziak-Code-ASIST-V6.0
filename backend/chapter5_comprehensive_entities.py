"""
CHAPTER 5 COMPREHENSIVE ENTITY LIST
====================================

Extracted SYSTEMATICALLY from SAMM Chapter 5 content (samm.dsca.mil/chapter/chapter-5)
NOT based on test questions - covers ALL entities in chapter for ANY query.

This is like the SAMM Acronym Glossary - comprehensive from source document.
"""

# =============================================================================
# CHAPTER 5 ACRONYMS (Extracted from Chapter 5 text)
# Format: "acronym": "full form"
# =============================================================================
CHAPTER_5_ACRONYMS = {
    # Core Document Acronyms
    "LOR": "Letter of Request",
    "LOA": "Letter of Offer and Acceptance",
    "P&A": "Price and Availability",
    "LOAD": "LOA Data",  # C5.3.1 - "data compiled for an LOA are referred to as LOA data (LOAD)"
    "CTA": "Country Team Assessment",  # C5.1.4
    "CN": "Congressional Notification",  # C5.1.4
    "MFR": "Memorandum for Record",  # C5.1.3
    "RFP": "Request for Proposal",  # C5.1.2
    "RFI": "Request for Information",  # C5.1.3.4.2
    
    # Case Types
    "CLSSA": "Cooperative Logistics Supply Support Arrangement",  # C5.4.3.3
    "FMSO": "Foreign Military Sales Order",  # C5.4.3.3
    "FMSO I": "Foreign Military Sales Order I",  # C5.4.3.3
    "FMSO II": "Foreign Military Sales Order II",  # C5.4.3.3
    
    # Response Types
    "NTE": "Not-to-Exceed",  # C5.2.1.3
    "FFP": "Firm Fixed Price",  # C5.2.1.3
    "EOQ": "Economic Order Quantity",  # C5.2.2.2.1
    
    # Programs
    "FMS": "Foreign Military Sales",
    "DCS": "Direct Commercial Sales",  # C5.2.1
    "BPC": "Building Partner Capacity",  # C5.4.1
    "FMF": "Foreign Military Financing",  # C5.1.3.3
    "EDA": "Excess Defense Articles",  # Table C5.T4
    "NPOR": "Non-Program of Record",  # C5.1.3.7
    "POR": "Program of Record",  # C5.4.10
    "TPA": "Total Package Approach",  # C5.4.6.1
    "EUM": "End Use Monitoring",  # C5.4.8.11.1.4
    "SC": "Security Cooperation",  # C5.1.3.4.2
    
    # Equipment Categories
    "SME": "Significant Military Equipment",  # C5.1.3.1
    "MDE": "Major Defense Equipment",  # C5.1.3.2
    "TDP": "Technical Data Package",  # C5.4.3.1.2
    "SRC": "Security Risk Category",  # C5.4.3.1.2
    
    # Weapons/Systems
    "NVD": "Night Vision Device",  # Table C5.T1E
    "NVDs": "Night Vision Devices",  # Table C5.T1A
    "MANPADS": "Man-Portable Air Defense System",  # Table C5.T1F
    "UAV": "Unmanned Aerial Vehicle",  # Table C5.T1B
    "UCAV": "Unmanned Combat Aerial Vehicle",  # Table C5.T1B
    "ISR": "Intelligence, Surveillance and Reconnaissance",  # Table C5.T1B
    "C4ISR": "Command, Control, Communications, Computer, Intelligence, Surveillance and Reconnaissance",  # Table C5.T1C
    "GEOINT": "Geospatial Intelligence",  # Table C5.T1D
    "EW": "Electronic Warfare",  # Table C5.T4
    "EWIRDB": "EW Integrated Reprogramming Database",  # Table C5.T4
    "COMSEC": "Communications Security",  # C5.1.7.1
    "MTCR": "Missile Technology Control Regime",  # Table C5.T1B
    "AD": "Air Defense",  # Table C5.T1F
    "A/G": "Air-to-Ground",  # Table C5.T1A
    "S/S": "Surface-to-Surface",  # Table C5.T1A
    "S/A": "Surface-to-Air",  # Table C5.T1A
    "A/S": "Air-to-Surface",  # Table C5.T4
    "FoM": "Figure of Merit",  # Table C5.T1E
    "TCM": "Target Coordinate Mensuration",  # Table C5.T1H
    "CDE": "Collateral Damage Estimation",  # Table C5.T1H
    "PDT": "Population Density Tables",  # Table C5.T1H
    
    # DSCA Organizations
    "DSCA": "Defense Security Cooperation Agency",
    "IOPS": "Office of International Operations",  # C5.1.3.1
    "IOPS/WPN": "International Operations, Weapons Directorate",  # C5.1.3.4.1
    "IOPS/WPNS": "International Operations, Weapons Directorate",  # C5.1.3.7
    "IOPS/REX": "International Operations, Regional Execution Directorate",  # C5.1.4
    "IOPS/GEX": "International Operations, Global Execution Directorate",  # C5.1.7.2.3
    "IOPS/GEX/CWD": "Case Writing and Development Division",  # C5.1.7.2.3
    "SPP": "Office of Strategy, Plans, and Policy",  # C5.2.2.2
    "SPP/EPA": "Execution Policy and Analysis Directorate",  # C5.1.3.7
    "ADM/PIE": "Office of Administration, Performance, Improvement, and Effectiveness Directorate",  # C5.1.7.4
    "ADM/PIE/AME": "Assessment, Monitoring and Evaluation Division",  # C5.1.3.6.1
    "OBO": "Office of Business Operations",  # C5.4.8.11.1.1
    "OBO/FPRE": "Financial Policy & Regional Execution Directorate",  # C5.4.8.11.1.1
    "OBO/FPRE/FRC": "Financial Reporting and Compliance Division",  # C5.4.8.11.1.1
    "FO/OGC": "Front Office, Office of the General Counsel",  # C5.4.8.3
    "CPD": "Country Portfolio Director",  # C5.1.3.4.1
    
    # State Department
    "PM": "Bureau of Political-Military Affairs",  # C5.1.5.1
    "PM/SA": "Office of Security Assistance",  # C5.1.3.3
    "PM/RSAT": "Office of Regional Security and Arms Transfers",  # C5.2.2.1.2
    "State (RM)": "Bureau of Information Resource Management",  # C5.4.8.6
    
    # DoD Organizations
    "DoD": "Department of Defense",
    "MILDEP": "Military Department",  # C5.1.2.1
    "IA": "Implementing Agency",  # C5.1.2.1
    "CCMD": "Combatant Command",  # C5.1.3.1
    "CCDR": "Combatant Commander",  # Table C5.T1
    "OUSD(P)": "Office of the Under Secretary of Defense for Policy",  # C5.2.2.1.2
    "OUSD(A&S)": "Office of the Under Secretary of Defense for Acquisition and Sustainment",  # C5.2.2.1.2
    "USD(A&S)": "Under Secretary of Defense for Acquisition & Sustainment",  # C5.1.8.1
    "SECDEF": "Secretary of Defense",  # C5.3.2.1
    "DTSA": "Defense Technology Security Administration",  # C5.2.2.1.2
    "NSA": "National Security Agency",  # C5.1.7.1
    "MDA": "Missile Defense Agency",  # Table C5.T4
    "USSOCOM": "U.S. Special Operations Command",  # C5.1.3.4.1
    "SOF": "Special Operations Force",  # C5.1.3.4.2
    "SOF AT&L-IO": "SOF Acquisition, Technology and Logistics International Operations",  # C5.1.3.4.2
    "SCO": "Security Cooperation Organization",  # C5.1.1
    "COM": "Chief of Mission",  # C5.4.8.6
    "MOD": "Ministry of Defense",  # C5.1.5.2
    "NATO": "North Atlantic Treaty Organization",  # Table C5.T1B
    "UN": "United Nations",  # C5.4.8.11.1.4
    
    # Systems
    "DSAMS": "Defense Security Assistance Management System",  # C5.1.2.1
    "CTS": "Case Tracking System",  # C5.2.2.1.1
    "SCIP": "Security Cooperation Information Portal",  # C5.4.3.2
    "DTS": "Defense Transportation System",  # C5.4.3.1.1
    "CAC": "Common Access Card",  # C5.1.3.7
    
    # Documents/Forms
    "MASL": "Military Articles and Services List",  # C5.4.3.2.2
    "MTDS": "Manpower Travel Data Sheet",  # C5.4.3.1.1
    "MOU": "Memorandum of Understanding",  # C5.4.8.8
    "SOW": "Statement of Work",  # C5.4.8.8
    "PWS": "Performance Work Statement",  # C5.4.8.8
    "ILS": "Integrated Logistics Support",  # Table C5.T5
    "PMR": "Program Management Review",  # C5.4.6.1
    
    # Case Processing Milestones
    "MILAP": "Military Department Approval",  # C5.1.7.2.3
    "MILSGN": "Military Signature",  # C5.4.2.1
    "CPOHOLD": "Case Processing Office Hold",  # C5.4.2.2.1
    "CPOHOLDREM": "CPOHOLD Removal",  # C5.4.2.2.3.1
    "CDEF": "Case Development Extenuating Factor",  # C5.4.2.1
    "OED": "Offer Expiration Date",  # C5.4.2.3.2
    
    # Special Processing
    "OT&E": "Operational Testing and Evaluation",  # C5.1.8.3
    "ENDP": "Exception to National Disclosure Policy",  # C5.1.8.2
    "JVI": "Joint Visual Inspection",  # C5.4.8.10.8
    "SO-P": "Special Operations-Peculiar",  # C5.1.3.4
    
    # Personnel
    "PCS": "Permanent Change of Station",  # C5.4.8.6
    "TDY": "Temporary Duty",  # C5.4.8.6
    "OCONUS": "Outside the Continental United States",  # C5.4.8.7.3
    "CONUS": "Continental United States",  # C5.4.8.5
    "SOFA": "Status of Forces Agreement",  # C5.4.8.7.1
    "POC": "Point of Contact",  # C5.4.8.11.1.1
    
    # Financial
    "NC": "Nonrecurring Cost",  # C5.1.3.2
    "CAS": "Contract Administration Services",  # Table C5.T3B
    "DoD FMR": "DoD Financial Management Regulation",  # C5.2.1.3
    
    # Codes
    "AAC": "Acquisition Advice Code",  # C5.4.3.3.2
    "SIDN": "Selected Item Description Number",  # C5.4.8.11.1.4
    "SISC": "Selected Item Sequence Code",  # C5.4.8.11.1.4
    "SISN": "Selected Item Sequence Number",  # C5.4.8.11.1.4
    "SCC": "Significant Category Code",  # C5.4.8.11.1.4
    "MOS": "Months of Supply",  # C5.4.8.5
    "ITAR": "International Traffic in Arms Regulations",  # C5.4.8.11.1.4
    "UNTIA": "UN Transparency in Armaments",  # C5.4.8.11.1.4
    
    # Legal
    "AECA": "Arms Export Control Act",  # C5.1.3.2
    "USML": "United States Munitions List",  # C5.1.3.2
    "USG": "United States Government",  # C5.1.2.1
    "FAR": "Federal Acquisition Regulation",  # C5.4.11
    "CJCSI": "Chairman of the Joint Chiefs of Staff Instruction",  # Table C5.T1H
    "DoDI": "Department of Defense Instruction",  # C5.1.8.3
    "DoDD": "Department of Defense Directive",  # C5.1.3.4
}

# =============================================================================
# CHAPTER 5 MULTI-WORD ENTITIES (Terms that need pattern matching)
# These are compound terms from Chapter 5 that appear as-is in text
# =============================================================================
CHAPTER_5_MULTIWORD_ENTITIES = [
    # LOR Status Terms (C5.1.7)
    "LOR Actionable",
    "LOR Complete", 
    "LOR Insufficient",
    "LOR Receipt",
    "LOR Date",
    "LOR Assessment",
    "LOR checklist",
    "LOR Advisory",
    "actionable LOR",
    "actionable criteria",
    "Customer Request",
    
    # Case Types (C5.4.3)
    "Defined Order",
    "Blanket Order", 
    "Defined Order case",
    "Blanket Order case",
    "blanket order LOA",
    "defined order LOA",
    "FMS case",
    "FMS cases",
    "Multi-Service LOA",
    "case development",
    "case initialization",
    "Case Identifier",
    "case category",
    
    # Categories (Table C5.T6)
    "Category A",
    "Category B",
    "Category C",
    "Category D",
    
    # Response Types (C5.2)
    "hybrid response",
    "negotiated response",
    "Not-to-Exceed",
    "Firm Fixed Price",
    "negative response",
    "disapproval recommendation",
    
    # Country Team Assessment (C5.1.4)
    "Country Team Assessment",
    "Country Team",
    "CCMD endorsement",
    "first introduction",
    
    # Special Items (Table C5.T1A, C5.T4)
    "MTCR Category I",
    "MTCR Category 1",
    "ISR UAV",
    "ISR UCAV",
    "Night Vision Device",
    "Night Vision Devices",
    "white phosphorus",
    "White Phosphorous Munitions",
    "air-to-surface munitions",
    "surface-to-surface munitions",
    "Ballistic Missile Defense",
    "working dogs",
    "working dog",
    "long-term care plan",
    
    # Processing (C5.4.2)
    "Case Development Extenuating Factor",
    "case development standard",
    "processing time",
    "Offer Expiration Date",
    "restatement",
    "counteroffer",
    
    # Approvals/Waivers
    "Yockey Waiver",
    "Yockey waiver",
    "pre-OT&E",
    "technology release",
    "policy release",
    "disclosure approval",
    
    # LOA Components (C5.4)
    "Standard Terms and Conditions",
    "LOA Amendment",
    "LOA Modification",
    "case lines",
    "line item",
    "case notes",
    "LOA notes",
    "sole source",
    "nonrecurring cost",
    "assessorial charges",
    
    # Organizations
    "Country Portfolio Director",
    "Implementing Agency",
    "Security Cooperation Organization",
    "Combatant Command",
    "defense industrial base",
    "program office",
    "contracting officer",
    
    # Personnel
    "permanent change of station",
    "temporary duty",
    "Status of Forces Agreement",
    
    # Other Key Terms
    "defense articles",
    "defense services",
    "partner nation",
    "purchaser requirements",
    "Economic Order Quantity",
    "spare parts",
    "concurrent spares",
    "initial support package",
    "logistics support",
    "Total Package Approach",
]

# =============================================================================
# CHAPTER 5 TABLES AND FIGURES (References)
# =============================================================================
CHAPTER_5_REFERENCES = [
    # Tables
    "Table C5.T1", "Table C5.T1A", "Table C5.T1B", "Table C5.T1C",
    "Table C5.T1D", "Table C5.T1E", "Table C5.T1F", "Table C5.T1G", "Table C5.T1H",
    "Table C5.T2A", "Table C5.T2B",
    "Table C5.T3A", "Table C5.T3B",
    "Table C5.T4", "Table C5.T5", "Table C5.T6", "Table C5.T7",
    "Table C5.T19", "Table C5.T20",
    "Table C9.T2A",  # Referenced
    
    # Figures
    "Figure C5.F1", "Figure C5.F1A", "Figure C5.F1B",
    "Figure C5.F2", "Figure C5.F3", "Figure C5.F4", "Figure C5.F5", "Figure C5.F6",
    "Figure C5.F13", "Figure C5.F14", "Figure C5.F15", "Figure C5.F23",
    
    # Sections
    "C5.1", "C5.2", "C5.3", "C5.4", "C5.5", "C5.6",
    "Section C5.1.4", "Section C5.1.7", "Section C5.4.3",
]

# =============================================================================
# COMBINED ENTITY PATTERNS FOR APP INTEGRATION
# =============================================================================
def get_chapter5_entity_patterns():
    """
    Returns all Chapter 5 entities formatted for samm_entity_patterns
    """
    patterns = []
    
    # Add all acronyms
    for acronym, fullform in CHAPTER_5_ACRONYMS.items():
        patterns.append(acronym)
        patterns.append(fullform)
        # Add lowercase versions
        patterns.append(acronym.lower())
        patterns.append(fullform.lower())
    
    # Add multi-word entities
    for entity in CHAPTER_5_MULTIWORD_ENTITIES:
        patterns.append(entity)
        patterns.append(entity.lower())
    
    # Add references
    patterns.extend(CHAPTER_5_REFERENCES)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_patterns = []
    for p in patterns:
        if p.lower() not in seen:
            seen.add(p.lower())
            unique_patterns.append(p)
    
    return unique_patterns

# =============================================================================
# PRINT SUMMARY
# =============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("CHAPTER 5 COMPREHENSIVE ENTITY LIST")
    print("Extracted from SAMM Chapter 5 Content")
    print("=" * 80)
    
    print(f"\n📊 ACRONYMS: {len(CHAPTER_5_ACRONYMS)}")
    print(f"📊 MULTI-WORD ENTITIES: {len(CHAPTER_5_MULTIWORD_ENTITIES)}")
    print(f"📊 REFERENCES (Tables/Figures): {len(CHAPTER_5_REFERENCES)}")
    
    all_patterns = get_chapter5_entity_patterns()
    print(f"📊 TOTAL UNIQUE PATTERNS: {len(all_patterns)}")
    
    print("\n" + "=" * 80)
    print("SAMPLE ACRONYMS (first 20):")
    print("=" * 80)
    for i, (acr, full) in enumerate(list(CHAPTER_5_ACRONYMS.items())[:20]):
        print(f"   {acr}: {full}")
    
    print("\n" + "=" * 80)
    print("SAMPLE MULTI-WORD ENTITIES (first 20):")
    print("=" * 80)
    for entity in CHAPTER_5_MULTIWORD_ENTITIES[:20]:
        print(f"   {entity}")
