"""
Chapter 7 Comprehensive Entity Extraction
==========================================
SAMM Chapter 7: Transportation

This module contains all entities extracted from Chapter 7 including:
- Acronyms and their expansions
- Multi-word domain entities
- Section/Table/Figure references
- Organizations and systems
"""

# =============================================================================
# ACRONYMS AND EXPANSIONS
# =============================================================================
CHAPTER_7_ACRONYMS = {
    # Transportation Systems
    "DTS": "Defense Transportation System",
    "DTC": "Delivery Term Code",
    "USTRANSCOM": "United States Transportation Command",
    "AMC": "Air Mobility Command",
    "SDDC": "Surface Deployment and Distribution Command",
    "MSC": "Military Sealift Command",
    "DTR": "Defense Transportation Regulation",
    
    # Address/Documentation Systems
    "MAPAD": "Military Assistance Program Address Directory",
    "TAC": "Type Address Code",
    "TCN": "Transportation Control Number",
    "NOA": "Notice of Availability",
    "ORC": "Offer Release Code",
    "CRIC": "Communication Routing Identifier Code",
    "ILCS": "International Logistics Communication System",
    
    # Shipping Terms
    "FOB": "Free On Board",
    "POE": "Port of Embarkation",
    "POD": "Port of Debarkation",
    "BL": "Bill of Lading",
    "CBL": "Commercial Bill of Lading",
    "CONUS": "Continental United States",
    "OCONUS": "Outside the Contiguous United States",
    
    # Special Transportation
    "SAAM": "Special Assignment Airlift Mission",
    "NGDS": "Next Generation Delivery Services",
    "DCS": "Defense Courier Service",
    "TDR": "Transportation Discrepancy Report",
    
    # Security/Classified
    "DCSA": "Defense Counterintelligence and Security Agency",
    "DGR": "Designated Government Representative",
    "COMSEC": "Communications Security",
    "CCI": "Controlled Cryptographic Items",
    "INFOSEC": "Information Security",
    "NISPOM": "National Industrial Security Program Operating Manual",
    "CISMOA": "Communications Interoperability and Security Memorandum of Agreement",
    "CNSS": "Committee on National Security Systems",
    "CNSSI": "Committee on National Security Systems Instruction",
    
    # Arms/Ammunition/Explosives
    "AA&E": "Arms Ammunition and Explosives",
    "SRC": "Security Risk Category",
    "MANPADS": "Man Portable Air Defense Systems",
    
    # Hazardous Materials
    "HAZMAT": "Hazardous Materials",
    "HMR": "Hazardous Materials Regulations",
    "HC1": "Hazard Class 1",
    "PHMSA": "Pipeline and Hazardous Materials Safety Administration",
    "WPM": "Wood Packaging Material",
    "ISPM": "International Standards for Phytosanitary Measures",
    
    # Export/Customs
    "ITAR": "International Traffic in Arms Regulations",
    "EEI": "Electronic Export Information",
    "AES": "Automated Export System",
    "CBP": "Customs and Border Protection",
    "ITN": "Internal Transaction Number",
    "DNA": "Determination of Non-Availability",
    
    # Organizations
    "MARAD": "Maritime Administration",
    "DOT": "Department of Transportation",
    "DTSA": "Defense Technology Security Administration",
    "DCMA": "Defense Contract Management Agency",
    "GSA": "General Services Administration",
    "NSA": "National Security Agency",
    "DEA": "Drug Enforcement Administration",
    
    # Documentation/Forms
    "DD": "Defense Department",
    "SF": "Standard Form",
    "NSN": "National Stock Number",
    "iRAPT": "Invoicing Receipt Acceptance and Property Transfer",
    
    # Systems
    "IGC": "Integrated Data Environment Global Transportation Network Convergence",
    "EFTS": "Enhanced Freight Tracking System",
    "CMCS": "COMSEC Material Control System",
    "MAPAC": "Military Assistance Program Address Code",
    
    # Other
    "MISWG": "Multinational Industrial Security Working Group",
    "NATO": "North Atlantic Treaty Organization",
    "ACA": "Airlift Clearance Authority",
    "SCO": "Security Cooperation Organization",
    "APO": "Army or Air Force Post Office",
    "FPO": "Fleet Post Office",
    "USPS": "United States Postal Service",
    "DSN": "Defense Switched Network",
    "UN": "United Nations",
    "EDA": "Excess Defense Articles",
    "REPSHIP": "Report of Shipment",
    "TPS": "Transportation Protective Service",
}

# =============================================================================
# MULTI-WORD ENTITIES
# =============================================================================
CHAPTER_7_ENTITIES = {
    # Core Transportation Concepts
    "transportation": [
        "Defense Transportation System",
        "transportation responsibilities",
        "transportation plan",
        "transportation costs",
        "transportation documents",
        "transportation discrepancy",
        "premium transportation",
        "organic transportation",
        "commercial transportation",
    ],
    
    # Title Transfer
    "title_transfer": [
        "title transfer",
        "title passage",
        "passage of title",
        "point of origin",
        "initial point of shipment",
        "retention of title",
        "title retention",
    ],
    
    # Delivery Terms
    "delivery_terms": [
        "Delivery Term Code",
        "Free On Board",
        "FOB origin",
        "point of delivery",
        "Port of Embarkation",
        "Port of Debarkation",
    ],
    
    # Freight Forwarders
    "freight_forwarder": [
        "FMS freight forwarder",
        "freight forwarder",
        "freight forwarder facility",
        "freight forwarder requirements",
    ],
    
    # DTS Components
    "dts_components": [
        "Air Mobility Command",
        "Surface Deployment and Distribution Command",
        "Military Sealift Command",
        "AMC Channel",
        "channel airlift",
        "organic assets",
        "military transportation",
    ],
    
    # Special Transportation
    "special_transport": [
        "Special Assignment Airlift Mission",
        "SAAM flights",
        "Next Generation Delivery Services",
        "Defense Courier Service",
        "small parcel shipments",
        "ocean liner service",
        "liner service",
    ],
    
    # MAPAD Related
    "mapad": [
        "Military Assistance Program Address Directory",
        "Type Address Code",
        "ship-to address",
        "mark-for address",
        "MAPAD address",
        "Special Instructions",
    ],
    
    # Documentation
    "documentation": [
        "Bill of Lading",
        "Commercial Bill of Lading",
        "Air Waybill",
        "Transportation Control Number",
        "Notice of Availability",
        "Offer Release Code",
        "ocean manifest",
        "air manifest",
        "packing list",
        "shipping documents",
    ],
    
    # Packaging/Marking
    "packaging": [
        "packaging requirements",
        "Military Level A/B",
        "Wood Packaging Material",
        "military shipping label",
        "MIL-STD-129",
        "marking requirements",
    ],
    
    # Cargo Preference
    "cargo_preference": [
        "Cargo Preference",
        "U.S. Flag vessel",
        "US Flag carrier",
        "P1 service",
        "P2 service", 
        "P3 service",
        "Determination of Non-Availability",
        "Fly America Act",
        "Merchant Marine Act",
    ],
    
    # Insurance
    "insurance": [
        "commercial insurance",
        "self-insure",
        "loss or damage",
    ],
    
    # Transportation Plans
    "transport_plans": [
        "Transportation Plan",
        "pre-case transportation assessment",
        "transportation requirements",
    ],
    
    # Classified/Sensitive
    "classified": [
        "classified materiel",
        "classified shipments",
        "classified information",
        "sensitive materiel",
        "Controlled Cryptographic Items",
        "COMSEC products",
        "Communications Security",
        "security clearance",
        "facility clearance",
        "personnel security clearance",
    ],
    
    # AA&E
    "aa_e": [
        "Arms Ammunition and Explosives",
        "Security Risk Category",
        "SRC I",
        "SRC II",
        "SRC III",
        "SRC IV",
        "Man Portable Air Defense Systems",
        "sensitive items",
    ],
    
    # HAZMAT
    "hazmat": [
        "hazardous materials",
        "Hazard Class 1",
        "EX-Number",
        "DOT EX-Number",
        "explosives",
        "HC1 articles",
    ],
    
    # Export/Customs
    "export": [
        "export license",
        "ITAR exemption",
        "Electronic Export Information",
        "Automated Export System",
        "Customs and Border Protection",
        "export authorization",
        "Internal Transaction Number",
    ],
    
    # Organizations
    "organizations": [
        "United States Transportation Command",
        "Maritime Administration",
        "Defense Counterintelligence and Security Agency",
        "Defense Technology Security Administration",
        "Defense Contract Management Agency",
        "Pipeline and Hazardous Materials Safety Administration",
        "Designated Government Representative",
        "Security Cooperation Organization",
        "husbanding agent",
    ],
    
    # Costs
    "costs": [
        "transportation costs",
        "storage charges",
        "storage fees",
        "accessorial charges",
        "Transportation Cost Clearing Account",
        "standard transportation percentages",
    ],
    
    # Claims/Discrepancies
    "claims": [
        "Transportation Discrepancy Report",
        "tracer action",
        "claims against carriers",
        "proof of delivery",
        "constructive proof of delivery",
        "non-receipt",
    ],
}

# =============================================================================
# TABLE/FIGURE/SECTION REFERENCES
# =============================================================================
CHAPTER_7_REFERENCES = {
    "tables": [
        "Table C7.T1",  # Transportation Responsibilities
        "Table C7.T2",  # Type of Address Codes
        "Table C7.T3",  # FMS Shipment Marking
        "Table C7.T4",  # Required DNA Application Information
        "Table C7.T5",  # Transportation Report Information
        "Table C7.T6",  # Offer Release Codes
        "Table C7.T7",  # Application Delivery Addresses
        "Table C7.T8",  # Individual Shipment-Level Requirements
        "Table C7.T9",  # TDR Contact Information
    ],
    "figures": [
        "Figure C7.F1",  # Transportation Plan Requirements
        "Figure C7.F2",  # Sample Transportation Plan
        "Figure C7.F3",  # Sample Transportation Plan Classified Annex
        "Figure C7.F4",  # CCI Transportation Plan Requirements
        "Figure C7.F5",  # HC1 EX-Number Documentation
        "Figure C7.F6",  # EX-Number Request Letter
    ],
    "sections": [
        "C7.1", "C7.2", "C7.3", "C7.4", "C7.5",
        "C7.6", "C7.7", "C7.8", "C7.9", "C7.10",
        "C7.11", "C7.12", "C7.13", "C7.14", "C7.15",
        "C7.16", "C7.17", "C7.18", "C7.19", "C7.20",
        "C7.21",
    ],
}

# =============================================================================
# FORMS AND STANDARDS
# =============================================================================
CHAPTER_7_FORMS = [
    "DD Form 1348-1A",  # Issue Release Receipt Document
    "DD Form 1348-5",   # Notice of Availability
    "DD Form 361",      # Transportation Discrepancy Report
    "SF-153",           # COMSEC Material Report
    "MIL-STD-129",      # Military Marking Standard
]

# =============================================================================
# HELPER FUNCTION
# =============================================================================
def get_chapter7_entity_patterns():
    """Return all Chapter 7 entities as a flat list for pattern matching"""
    patterns = set()
    
    # Add acronyms and expansions
    for acronym, expansion in CHAPTER_7_ACRONYMS.items():
        patterns.add(acronym)
        patterns.add(expansion)
        patterns.add(acronym.lower())
        patterns.add(expansion.lower())
    
    # Add multi-word entities
    for category, entities in CHAPTER_7_ENTITIES.items():
        for entity in entities:
            patterns.add(entity)
            patterns.add(entity.lower())
    
    # Add references
    for ref_type, refs in CHAPTER_7_REFERENCES.items():
        for ref in refs:
            patterns.add(ref)
    
    # Add forms
    for form in CHAPTER_7_FORMS:
        patterns.add(form)
    
    return patterns


# =============================================================================
# SUMMARY
# =============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("CHAPTER 7 ENTITY EXTRACTION SUMMARY")
    print("Transportation")
    print("=" * 80)
    
    print(f"\n📊 ACRONYMS: {len(CHAPTER_7_ACRONYMS)}")
    
    total_entities = sum(len(v) for v in CHAPTER_7_ENTITIES.values())
    print(f"📊 MULTI-WORD ENTITIES: {total_entities}")
    for cat, entities in CHAPTER_7_ENTITIES.items():
        print(f"   - {cat}: {len(entities)}")
    
    total_refs = sum(len(v) for v in CHAPTER_7_REFERENCES.values())
    print(f"📊 REFERENCES: {total_refs}")
    
    print(f"📊 FORMS: {len(CHAPTER_7_FORMS)}")
    
    all_patterns = get_chapter7_entity_patterns()
    print(f"\n📊 TOTAL UNIQUE PATTERNS: {len(all_patterns)}")
