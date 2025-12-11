"""
SAMM Chapter 7 Entity Implementation
=====================================

Chapter 7: Transportation

This module contains:
1. Chapter 7 Ground Truth Entities
2. Chapter 7 Specific Acronym Pairs
3. Chapter 7 Entity Patterns
4. Chapter 7 Entity Relationships
5. Chapter 7 Test Cases (90 tests)

Chapter 7 covers:
- C7.1: Overview
- C7.2: Responsibilities
- C7.3: Title Transfer
- C7.4: Delivery Terms
- C7.5: Freight Forwarders
- C7.6: Defense Transportation System
- C7.7: MAPAD
- C7.8: Packaging and Marking
- C7.9: Cargo Preference
- C7.10-C7.12: Special Cargo Categories
- C7.13-C7.14: Classified Transportation
- C7.15-C7.16: AA&E and HAZMAT
- C7.17: Export Compliance
- C7.18-C7.21: Costs, Insurance, Claims
"""

# =============================================================================
# CHAPTER 7 SPECIFIC ACRONYM PAIRS (NEW - Not in Chapters 1-6)
# =============================================================================
CHAPTER_7_ACRONYM_PAIRS = {
    # Defense Transportation System
    "dts": "defense transportation system",
    "ustranscom": "united states transportation command",
    "amc": "air mobility command",
    "sddc": "surface deployment and distribution command",
    "msc": "military sealift command",
    "dtr": "defense transportation regulation",
    
    # Delivery Terms
    "dtc": "delivery term code",
    "fob": "free on board",
    "poe": "port of embarkation",
    "pod": "port of debarkation",
    
    # MAPAD
    "mapad": "military assistance program address directory",
    "tac": "type address code",
    "cric": "communication routing identifier code",
    "ilcs": "integrated logistics communication system",
    
    # Documentation
    "noa": "notice of availability",
    "orc": "offer release code",
    "tcn": "transportation control number",
    "bl": "bill of lading",
    "cbl": "commercial bill of lading",
    "gbl": "government bill of lading",
    "irapt": "invoicing receipt acceptance and property transfer",
    
    # Special Transportation
    "saam": "special assignment airlift mission",
    "ngds": "next generation delivery services",
    "dcs": "defense courier service",
    
    # Cargo Preference
    "dna": "determination of non-availability",
    "marad": "maritime administration",
    
    # Packaging/Marking
    "wpm": "wood packaging material",
    "ispm": "international standards for phytosanitary measures",
    
    # Classified Transportation
    "comsec": "communications security",
    "cci": "controlled cryptographic items",
    "cismoa": "communications interoperability and security memorandum of agreement",
    "dcsa": "defense counterintelligence and security agency",
    "nispom": "national industrial security program operating manual",
    "cnss": "committee on national security systems",
    "etp": "exception to policy",
    
    # AA&E
    "aa&e": "arms ammunition and explosives",
    "src": "security risk category",
    "manpads": "man portable air defense systems",
    
    # HAZMAT
    "hazmat": "hazardous materials",
    "hmr": "hazardous materials regulations",
    "phmsa": "pipeline and hazardous materials safety administration",
    "hc1": "hazard class 1",
    
    # Export Compliance
    "itar": "international traffic in arms regulations",
    "eei": "electronic export information",
    "aes": "automated export system",
    "cbp": "customs and border protection",
    "itn": "internal transaction number",
    
    # Organizations
    "dgr": "designated government representative",
    "dcma": "defense contract management agency",
    "dtsa": "defense technology security administration",
    
    # Claims
    "tdr": "transportation discrepancy report",
    
    # Forms
    "sf-153": "comsec material report",
}

# =============================================================================
# CHAPTER 7 GROUND TRUTH ENTITIES
# =============================================================================
CHAPTER_7_GROUND_TRUTH = {
    # Organizations (C7.2)
    "organizations": {
        # Transportation Commands
        "DTS", "Defense Transportation System",
        "USTRANSCOM", "United States Transportation Command",
        "AMC", "Air Mobility Command",
        "SDDC", "Surface Deployment and Distribution Command",
        "MSC", "Military Sealift Command",
        
        # Security/Oversight
        "DCSA", "Defense Counterintelligence and Security Agency",
        "DCMA", "Defense Contract Management Agency",
        "DTSA", "Defense Technology Security Administration",
        "CBP", "Customs and Border Protection",
        "MARAD", "Maritime Administration",
        "PHMSA", "Pipeline and Hazardous Materials Safety Administration",
        
        # DoD/DSCA
        "DoD", "Department of Defense",
        "DSCA", "Defense Security Cooperation Agency",
        "SCO", "Security Cooperation Organization",
        "IA", "Implementing Agency",
        "DLA", "Defense Logistics Agency",
        
        # Other
        "DGR", "Designated Government Representative",
        "USPS", "United States Postal Service",
        "APO", "Army Post Office",
        "FPO", "Fleet Post Office",
        "DCS", "Defense Courier Service",
    },
    
    # Delivery Terms (C7.4)
    "delivery_terms": {
        "DTC", "Delivery Term Code",
        "DTC 4", "DTC 5", "DTC 7", "DTC 8", "DTC 9",
        "FOB", "Free On Board",
        "FOB origin", "FOB destination",
        "POE", "Port of Embarkation",
        "POD", "Port of Debarkation",
        "CONUS", "Continental United States",
        "OCONUS", "Outside Continental United States",
    },
    
    # MAPAD (C7.7)
    "mapad": {
        "MAPAD", "Military Assistance Program Address Directory",
        "TAC", "Type Address Code",
        "TAC 1", "TAC 2", "TAC 3", "TAC 4", "TAC 5", "TAC 6",
        "TAC A", "TAC B", "TAC C", "TAC D", "TAC M",
        "CRIC", "Communication Routing Identifier Code",
        "ILCS", "Integrated Logistics Communication System",
        "mark-for address", "ship-to address",
        "documentation address", "status address",
    },
    
    # Documentation (C7.6, C7.11)
    "documentation": {
        "NOA", "Notice of Availability",
        "ORC", "Offer Release Code",
        "ORC A", "ORC X", "ORC Y", "ORC Z",
        "TCN", "Transportation Control Number",
        "BL", "Bill of Lading",
        "CBL", "Commercial Bill of Lading",
        "GBL", "Government Bill of Lading",
        "DD Form 1348-5", "DD Form 1348-1A",
        "DD Form 361", "SF-153",
        "iRAPT", "Invoicing Receipt Acceptance and Property Transfer",
    },
    
    # Special Transportation (C7.6.2)
    "special_transportation": {
        "SAAM", "Special Assignment Airlift Mission",
        "NGDS", "Next Generation Delivery Services",
        "DCS", "Defense Courier Service",
        "AMC Channel", "channel airlift",
        "small parcel", "USPS",
    },
    
    # Cargo Preference (C7.9)
    "cargo_preference": {
        "Cargo Preference", "US Flag", "US Flag vessel",
        "P1 service", "P2 service", "P3 service",
        "P1", "P2", "P3",
        "DNA", "Determination of Non-Availability",
        "MARAD", "Maritime Administration",
        "Fly America Act", "46 USC 55305",
    },
    
    # Packaging/Marking (C7.8)
    "packaging": {
        "MIL-STD-129", "Military Level A", "Military Level B",
        "WPM", "Wood Packaging Material",
        "ISPM 15", "International Standards for Phytosanitary Measures",
        "phytosanitary", "marking requirements",
    },
    
    # Classified Transportation (C7.13, C7.14)
    "classified": {
        "Transportation Plan", "classified materiel",
        "COMSEC", "Communications Security",
        "CCI", "Controlled Cryptographic Items",
        "CISMOA", "Communications Interoperability and Security Memorandum of Agreement",
        "DCSA", "Defense Counterintelligence and Security Agency",
        "NISPOM", "National Industrial Security Program Operating Manual",
        "CNSS", "Committee on National Security Systems",
        "CONFIDENTIAL", "SECRET", "TOP SECRET",
        "facility clearance", "keyed", "un-keyed",
        "ETP", "Exception to Policy",
        "government courier",
    },
    
    # AA&E (C7.15)
    "aa_e": {
        "AA&E", "Arms Ammunition and Explosives",
        "SRC", "Security Risk Category",
        "SRC I", "SRC II", "SRC III", "SRC IV",
        "MANPADS", "Man Portable Air Defense Systems",
        "sensitive materiel", "night vision",
        "USD(I&S)", "waiver",
    },
    
    # HAZMAT (C7.16)
    "hazmat": {
        "HAZMAT", "Hazardous Materials",
        "HMR", "Hazardous Materials Regulations",
        "49 CFR", "Subchapter C",
        "HC1", "Hazard Class 1", "explosives",
        "EX-Number", "DOT EX-Number",
        "PHMSA", "Pipeline and Hazardous Materials Safety Administration",
        "1.4S", "small arms", ".50 cal",
    },
    
    # Export Compliance (C7.17)
    "export": {
        "ITAR", "International Traffic in Arms Regulations",
        "ITAR 126.6(a)", "ITAR 126.6(c)",
        "EEI", "Electronic Export Information",
        "AES", "Automated Export System",
        "CBP", "Customs and Border Protection",
        "ITN", "Internal Transaction Number",
        "export license", "license exemption",
    },
    
    # Title Transfer (C7.3)
    "title": {
        "title transfer", "title passage",
        "point of origin", "retention of title",
        "manufacturer", "depot", "loading facility",
        "EDA", "Excess Defense Articles",
        "ferrying aircraft",
    },
    
    # Costs (C7.12)
    "costs": {
        "transportation costs", "standard transportation percentage",
        "Transportation Cost Look-up Table", "Appendix 2",
        "accessorial charges", "storage charges",
        "containerization", "escorts",
        "above-the-line", "30 days",
    },
    
    # Claims (C7.21)
    "claims": {
        "TDR", "Transportation Discrepancy Report",
        "DD Form 361", "tracer action",
        "proof of delivery", "constructive proof",
        "carrier liability", "limited liability",
        "claims", "loss", "damage",
    },
    
    # Insurance (C7.18)
    "insurance": {
        "commercial insurance", "self-insure",
        "loss or damage", "liability",
        "high value items",
    },
    
    # Regulations/Standards
    "regulations": {
        "DTR", "Defense Transportation Regulation",
        "DTR 4500.9-R", "MIL-STD-129",
        "49 CFR", "46 USC 55305",
        "NISPOM", "ISPM 15",
    },
    
    # Freight Forwarders (C7.5)
    "freight_forwarders": {
        "freight forwarder", "FMS freight forwarder",
        "DGR", "Designated Government Representative",
        "ITAR registration", "PM/DDTC",
        "embassy authorization", "facility clearance",
    },
}

# =============================================================================
# CHAPTER 7 ENTITY PATTERNS
# =============================================================================
CHAPTER_7_ENTITY_PATTERNS = {
    "dts_patterns": [
        r"\bD(?:efense\s+)?T(?:ransportation\s+)?S(?:ystem)?\b",
        r"\bUSTRANSCOM\b",
        r"\bA(?:ir\s+)?M(?:obility\s+)?C(?:ommand)?\b",
        r"\bS(?:urface\s+)?D(?:eployment\s+and\s+)?D(?:istribution\s+)?C(?:ommand)?\b",
        r"\bM(?:ilitary\s+)?S(?:ealift\s+)?C(?:ommand)?\b",
    ],
    "delivery_patterns": [
        r"\bDTC\s*[4-9]\b",
        r"\bDelivery\s+Term\s+Code\b",
        r"\bFOB\b",
        r"\bFree\s+On\s+Board\b",
        r"\bPO[ED]\b",
        r"\bPort\s+of\s+(Embarkation|Debarkation)\b",
    ],
    "mapad_patterns": [
        r"\bMAPAD\b",
        r"\bMilitary\s+Assistance\s+Program\s+Address\s+Directory\b",
        r"\bTAC\s*[1-6ABCDM]\b",
        r"\bType\s+Address\s+Code\b",
        r"\bCRIC\b",
        r"\bmark-for\s+address\b",
    ],
    "documentation_patterns": [
        r"\bNOA\b",
        r"\bNotice\s+of\s+Availability\b",
        r"\bORC\s*[AXYZ]?\b",
        r"\bOffer\s+Release\s+Code\b",
        r"\bTCN\b",
        r"\bTransportation\s+Control\s+Number\b",
        r"\bBill\s+of\s+Lading\b",
        r"\b[CG]?BL\b",
        r"\bDD\s+Form\s+1348-[15]A?\b",
        r"\biRAPT\b",
    ],
    "special_transport_patterns": [
        r"\bSAAM\b",
        r"\bSpecial\s+Assignment\s+Airlift\s+Mission\b",
        r"\bNGDS\b",
        r"\bNext\s+Generation\s+Delivery\s+Services\b",
        r"\bDCS\b",
        r"\bDefense\s+Courier\s+Service\b",
        r"\bAMC\s+Channel\b",
        r"\bsmall\s+parcel\b",
    ],
    "cargo_patterns": [
        r"\bCargo\s+Preference\b",
        r"\bUS\s+Flag\b",
        r"\bP[123]\s+service\b",
        r"\bDNA\b",
        r"\bDetermination\s+of\s+Non-Availability\b",
        r"\bMARAD\b",
        r"\bFly\s+America\s+Act\b",
    ],
    "classified_patterns": [
        r"\bTransportation\s+Plan\b",
        r"\bCOMSEC\b",
        r"\bCommunications\s+Security\b",
        r"\bCCI\b",
        r"\bControlled\s+Cryptographic\s+Items?\b",
        r"\bCISMOA\b",
        r"\bDCSA\b",
        r"\bNISPOM\b",
        r"\bCONFIDENTIAL\b",
        r"\bSECRET\b",
        r"\bTOP\s+SECRET\b",
    ],
    "aa_e_patterns": [
        r"\bAA&E\b",
        r"\bArms[,]?\s+Ammunition[,]?\s+and\s+Explosives\b",
        r"\bSRC\s*I{1,4}V?\b",
        r"\bSecurity\s+Risk\s+Categor(?:y|ies)\b",
        r"\bMANPADS\b",
        r"\bMan\s+Portable\s+Air\s+Defense\s+Systems?\b",
    ],
    "hazmat_patterns": [
        r"\bHAZMAT\b",
        r"\bHazardous\s+Materials?\b",
        r"\bHMR\b",
        r"\bHC1\b",
        r"\bHazard\s+Class\s+1\b",
        r"\bEX-Number\b",
        r"\bPHMSA\b",
        r"\b49\s+CFR\b",
    ],
    "export_patterns": [
        r"\bITAR\b",
        r"\bInternational\s+Traffic\s+in\s+Arms\s+Regulations\b",
        r"\bITAR\s+126\.6\([ac]\)\b",
        r"\bEEI\b",
        r"\bElectronic\s+Export\s+Information\b",
        r"\bAES\b",
        r"\bAutomated\s+Export\s+System\b",
        r"\bCBP\b",
        r"\bITN\b",
    ],
    "claims_patterns": [
        r"\bTDR\b",
        r"\bTransportation\s+Discrepancy\s+Report\b",
        r"\bDD\s+Form\s+361\b",
        r"\btracer\s+action\b",
        r"\bproof\s+of\s+delivery\b",
        r"\bcarrier\s+liabilit(?:y|ies)\b",
    ],
}

# =============================================================================
# CHAPTER 7 ENTITY RELATIONSHIPS
# =============================================================================
CHAPTER_7_ENTITY_RELATIONSHIPS = {
    # DTS relationships (C7.6)
    "DTS": ["USTRANSCOM manages", "includes AMC SDDC MSC", "organic and commercial assets"],
    "USTRANSCOM": ["transportation command", "oversees DTS", "coordinates movements"],
    "AMC": ["air mobility", "airlift", "channel missions"],
    "SDDC": ["surface movement", "ocean shipments", "claims processing"],
    "MSC": ["sealift", "ocean transport", "vessel operations"],
    
    # Delivery Term relationships (C7.4)
    "DTC": ["determines DoD responsibility", "FOB origin basis", "purchaser pickup options"],
    "DTC 7": ["overseas POD", "DTS to port", "standard FMS"],
    "DTC 8": ["purchaser pickup at POE", "CONUS collection"],
    "DTC 9": ["overseas final destination", "extended DoD routing"],
    "FOB": ["title transfer point", "origin default", "risk transfer"],
    
    # MAPAD relationships (C7.7)
    "MAPAD": ["address directory", "TAC codes", "SCO maintains"],
    "TAC": ["address types", "ship-to mark-for NOA", "routing codes"],
    "TAC M": ["mark-for address", "ultimate consignee", "final recipient"],
    
    # Documentation relationships (C7.6.3, C7.11)
    "NOA": ["DD Form 1348-5", "material available", "triggers pickup"],
    "ORC": ["release authorization", "A X Y Z codes", "shipping release"],
    "TCN": ["shipment tracking", "unique identifier", "17 characters"],
    
    # Special transport relationships (C7.6.2)
    "SAAM": ["special airlift", "billed hourly", "dedicated mission"],
    "NGDS": ["small packages", "up to 300 lbs", "express delivery"],
    "DCS": ["classified courier", "sensitive items", "secure transport"],
    
    # Cargo Preference relationships (C7.9)
    "Cargo Preference": ["US Flag requirement", "50% minimum legal", "100% DSCA policy"],
    "DNA": ["non-availability waiver", "MARAD approval", "21 days notice"],
    "P1": ["US Flag throughout", "default service", "origin to destination"],
    
    # Classified relationships (C7.13, C7.14)
    "Transportation Plan": ["required for classified", "AA&E", "COMSEC CCI"],
    "COMSEC": ["communications security", "SF-153 report", "special handling"],
    "CCI": ["cryptographic items", "keyed vs un-keyed", "ETP for keyed"],
    
    # AA&E relationships (C7.15)
    "AA&E": ["arms ammunition explosives", "SRC categories", "special security"],
    "SRC I": ["highest risk", "MANPADS rockets", "USD(I&S) waiver"],
    "MANPADS": ["SRC I category", "DTS required", "no purchaser pickup"],
    
    # HAZMAT relationships (C7.16)
    "HAZMAT": ["49 CFR regulated", "HMR compliance", "special handling"],
    "EX-Number": ["DOT authorization", "HC1 explosives", "commercial movement"],
    "HC1": ["explosives class", "EX-Number required", "special permits"],
    
    # Export relationships (C7.17)
    "ITAR": ["export regulations", "126.6 exemptions", "PM/DDTC oversight"],
    "AES": ["CBP filing", "generates ITN", "export documentation"],
    "EEI": ["export data", "AES submission", "required for defense articles"],
    
    # Claims relationships (C7.21)
    "TDR": ["DD Form 361", "discrepancy report", "SCO submits"],
    "tracer": ["non-receipt investigation", "purchaser initiates", "shipment tracking"],
}

# =============================================================================
# TEST CASES - 90 TESTS FOR CHAPTER 7
# =============================================================================
TEST_CASES_CHAPTER_7 = {
    # Pattern 1: DTS Queries (C7.6)
    "pattern_c7_1_dts": {
        "description": "Defense Transportation System queries",
        "tests": [
            {"id": 401, "query": "What is the Defense Transportation System DTS?",
             "expected": ["dts", "defense transportation system"]},
            {"id": 402, "query": "What is USTRANSCOM United States Transportation Command?",
             "expected": ["ustranscom", "united states transportation command"]},
            {"id": 403, "query": "What is AMC Air Mobility Command?",
             "expected": ["amc", "air mobility command"]},
            {"id": 404, "query": "What is SDDC Surface Deployment and Distribution Command?",
             "expected": ["sddc", "surface deployment and distribution command"]},
            {"id": 405, "query": "What is MSC Military Sealift Command?",
             "expected": ["msc", "military sealift command"]},
        ]
    },
    
    # Pattern 2: Delivery Term Code Queries (C7.4)
    "pattern_c7_2_dtc": {
        "description": "Delivery Term Code queries",
        "tests": [
            {"id": 406, "query": "What is a Delivery Term Code DTC?",
             "expected": ["dtc", "delivery term code"]},
            {"id": 407, "query": "What does DTC 7 mean for FMS shipments?",
             "expected": ["dtc 7", "fms"]},
            {"id": 408, "query": "What is DTC 8 purchaser pickup?",
             "expected": ["dtc 8", "purchaser pickup"]},
            {"id": 409, "query": "What is FOB Free On Board origin?",
             "expected": ["fob", "free on board"]},
            {"id": 410, "query": "What is the difference between POE and POD?",
             "expected": ["poe", "pod"]},
        ]
    },
    
    # Pattern 3: Title Transfer Queries (C7.3)
    "pattern_c7_3_title": {
        "description": "Title transfer queries",
        "tests": [
            {"id": 411, "query": "When does title transfer occur in FMS?",
             "expected": ["title transfer", "fms"]},
            {"id": 412, "query": "What is the point of origin for title passage?",
             "expected": ["point of origin", "title"]},
            {"id": 413, "query": "When can USG retain title for FMS shipments?",
             "expected": ["usg", "title", "fms"]},
            {"id": 414, "query": "How does title transfer work for EDA Excess Defense Articles?",
             "expected": ["title transfer", "eda", "excess defense articles"]},
            {"id": 415, "query": "What is retention of title?",
             "expected": ["retention of title"]},
        ]
    },
    
    # Pattern 4: Freight Forwarder Queries (C7.5)
    "pattern_c7_4_freight": {
        "description": "Freight forwarder queries",
        "tests": [
            {"id": 416, "query": "What is an FMS freight forwarder?",
             "expected": ["fms", "freight forwarder"]},
            {"id": 417, "query": "What are freight forwarder requirements?",
             "expected": ["freight forwarder"]},
            {"id": 418, "query": "What is a DGR Designated Government Representative?",
             "expected": ["dgr", "designated government representative"]},
            {"id": 419, "query": "Who selects an FMS freight forwarder?",
             "expected": ["fms", "freight forwarder"]},
            {"id": 420, "query": "What ITAR registration is required for freight forwarders?",
             "expected": ["itar", "freight forwarder"]},
        ]
    },
    
    # Pattern 5: MAPAD Queries (C7.7)
    "pattern_c7_5_mapad": {
        "description": "MAPAD queries",
        "tests": [
            {"id": 421, "query": "What is the MAPAD Military Assistance Program Address Directory?",
             "expected": ["mapad", "military assistance program address directory"]},
            {"id": 422, "query": "What is a TAC Type Address Code?",
             "expected": ["tac", "type address code"]},
            {"id": 423, "query": "What is TAC M mark-for address?",
             "expected": ["tac m", "mark-for address"]},
            {"id": 424, "query": "What are MAPAD Special Instructions?",
             "expected": ["mapad", "special instructions"]},
            {"id": 425, "query": "How often should MAPAD addresses be reviewed?",
             "expected": ["mapad"]},
        ]
    },
    
    # Pattern 6: Documentation Queries (C7.6.3, C7.11)
    "pattern_c7_6_documentation": {
        "description": "Transportation documentation queries",
        "tests": [
            {"id": 426, "query": "What is a NOA Notice of Availability?",
             "expected": ["noa", "notice of availability"]},
            {"id": 427, "query": "What is an ORC Offer Release Code?",
             "expected": ["orc", "offer release code"]},
            {"id": 428, "query": "What is a TCN Transportation Control Number?",
             "expected": ["tcn", "transportation control number"]},
            {"id": 429, "query": "What is a Bill of Lading BL?",
             "expected": ["bill of lading", "bl"]},
            {"id": 430, "query": "What is DD Form 1348-5 used for?",
             "expected": ["dd form 1348-5"]},
        ]
    },
    
    # Pattern 7: Special Transportation Queries (C7.6.2)
    "pattern_c7_7_special": {
        "description": "Special transportation queries",
        "tests": [
            {"id": 431, "query": "What is a SAAM Special Assignment Airlift Mission?",
             "expected": ["saam", "special assignment airlift mission"]},
            {"id": 432, "query": "What is NGDS Next Generation Delivery Services?",
             "expected": ["ngds", "next generation delivery services"]},
            {"id": 433, "query": "What is DCS Defense Courier Service?",
             "expected": ["dcs", "defense courier service"]},
            {"id": 434, "query": "What is AMC Channel airlift?",
             "expected": ["amc channel", "amc"]},
            {"id": 435, "query": "How are small parcel shipments handled?",
             "expected": ["small parcel"]},
        ]
    },
    
    # Pattern 8: Cargo Preference Queries (C7.9)
    "pattern_c7_8_cargo": {
        "description": "Cargo preference queries",
        "tests": [
            {"id": 436, "query": "What is Cargo Preference for US Flag vessels?",
             "expected": ["cargo preference", "us flag"]},
            {"id": 437, "query": "What is P1 P2 P3 service?",
             "expected": ["p1", "p2", "p3"]},
            {"id": 438, "query": "What is a DNA Determination of Non-Availability?",
             "expected": ["dna", "determination of non-availability"]},
            {"id": 439, "query": "What role does MARAD Maritime Administration play?",
             "expected": ["marad", "maritime administration"]},
            {"id": 440, "query": "What is the Fly America Act?",
             "expected": ["fly america act"]},
        ]
    },
    
    # Pattern 9: Packaging and Marking Queries (C7.8)
    "pattern_c7_9_packaging": {
        "description": "Packaging and marking queries",
        "tests": [
            {"id": 441, "query": "What is MIL-STD-129 for FMS shipping?",
             "expected": ["mil-std-129", "fms"]},
            {"id": 442, "query": "What is Military Level A/B packaging?",
             "expected": ["military level a", "military level b"]},
            {"id": 443, "query": "What is WPM Wood Packaging Material?",
             "expected": ["wpm", "wood packaging material"]},
            {"id": 444, "query": "What is ISPM 15 for wood packaging?",
             "expected": ["ispm 15", "wood packaging"]},
            {"id": 445, "query": "What marking is required on FMS shipments?",
             "expected": ["marking", "fms"]},
        ]
    },
    
    # Pattern 10: Classified Transportation Queries (C7.13, C7.14)
    "pattern_c7_10_classified": {
        "description": "Classified transportation queries",
        "tests": [
            {"id": 446, "query": "What is a Transportation Plan for classified materiel?",
             "expected": ["transportation plan", "classified"]},
            {"id": 447, "query": "What is COMSEC Communications Security?",
             "expected": ["comsec", "communications security"]},
            {"id": 448, "query": "What are CCI Controlled Cryptographic Items?",
             "expected": ["cci", "controlled cryptographic items"]},
            {"id": 449, "query": "What does DCSA do for classified shipments?",
             "expected": ["dcsa", "classified"]},
            {"id": 450, "query": "What is a CISMOA agreement?",
             "expected": ["cismoa"]},
        ]
    },
    
    # Pattern 11: AA&E Queries (C7.15)
    "pattern_c7_11_aa_e": {
        "description": "Arms Ammunition and Explosives queries",
        "tests": [
            {"id": 451, "query": "What is AA&E Arms Ammunition and Explosives?",
             "expected": ["aa&e", "arms ammunition and explosives"]},
            {"id": 452, "query": "What are SRC Security Risk Categories I through IV?",
             "expected": ["src", "security risk category"]},
            {"id": 453, "query": "What are MANPADS Man Portable Air Defense Systems?",
             "expected": ["manpads", "man portable air defense systems"]},
            {"id": 454, "query": "What is SRC I for AA&E?",
             "expected": ["src i", "aa&e"]},
            {"id": 455, "query": "How is sensitive materiel transported?",
             "expected": ["sensitive materiel"]},
        ]
    },
    
    # Pattern 12: HAZMAT Queries (C7.16)
    "pattern_c7_12_hazmat": {
        "description": "Hazardous materials queries",
        "tests": [
            {"id": 456, "query": "What is HAZMAT Hazardous Materials?",
             "expected": ["hazmat", "hazardous materials"]},
            {"id": 457, "query": "What is an EX-Number from DOT PHMSA?",
             "expected": ["ex-number", "dot", "phmsa"]},
            {"id": 458, "query": "What is HC1 Hazard Class 1?",
             "expected": ["hc1", "hazard class 1"]},
            {"id": 459, "query": "What are HMR Hazardous Materials Regulations?",
             "expected": ["hmr", "hazardous materials regulations"]},
            {"id": 460, "query": "When is a DOT EX-Number required?",
             "expected": ["dot", "ex-number"]},
        ]
    },
    
    # Pattern 13: Export Compliance Queries (C7.17)
    "pattern_c7_13_export": {
        "description": "Export compliance queries",
        "tests": [
            {"id": 461, "query": "What ITAR exemptions apply to FMS?",
             "expected": ["itar", "fms"]},
            {"id": 462, "query": "What is EEI Electronic Export Information?",
             "expected": ["eei", "electronic export information"]},
            {"id": 463, "query": "What is AES Automated Export System?",
             "expected": ["aes", "automated export system"]},
            {"id": 464, "query": "What does CBP Customs and Border Protection require?",
             "expected": ["cbp", "customs and border protection"]},
            {"id": 465, "query": "What is an ITN Internal Transaction Number?",
             "expected": ["itn", "internal transaction number"]},
        ]
    },
    
    # Pattern 14: Insurance Queries (C7.18)
    "pattern_c7_14_insurance": {
        "description": "Insurance queries",
        "tests": [
            {"id": 466, "query": "Is commercial insurance required for FMS?",
             "expected": ["commercial insurance", "fms"]},
            {"id": 467, "query": "What is loss or damage liability for FMS?",
             "expected": ["loss", "damage", "fms"]},
            {"id": 468, "query": "Can purchasers self-insure FMS shipments?",
             "expected": ["self-insure", "fms"]},
            {"id": 469, "query": "Who arranges insurance for FMS freight?",
             "expected": ["insurance", "fms"]},
            {"id": 470, "query": "What insurance is needed for high value items?",
             "expected": ["insurance", "high value"]},
        ]
    },
    
    # Pattern 15: Transportation Costs Queries (C7.12)
    "pattern_c7_15_costs": {
        "description": "Transportation costs queries",
        "tests": [
            {"id": 471, "query": "How are DTS transportation costs calculated?",
             "expected": ["dts", "transportation costs"]},
            {"id": 472, "query": "What are standard transportation percentages?",
             "expected": ["standard transportation percentage"]},
            {"id": 473, "query": "What are storage charges for NOA delays?",
             "expected": ["storage charges", "noa"]},
            {"id": 474, "query": "How are SAAM costs billed on LOA?",
             "expected": ["saam", "loa"]},
            {"id": 475, "query": "What are accessorial charges?",
             "expected": ["accessorial charges"]},
        ]
    },
    
    # Pattern 16: Claims Queries (C7.21)
    "pattern_c7_16_claims": {
        "description": "Claims and discrepancy queries",
        "tests": [
            {"id": 476, "query": "What is a TDR Transportation Discrepancy Report?",
             "expected": ["tdr", "transportation discrepancy report"]},
            {"id": 477, "query": "What is DD Form 361?",
             "expected": ["dd form 361"]},
            {"id": 478, "query": "What is a tracer action for shipments?",
             "expected": ["tracer action"]},
            {"id": 479, "query": "What is constructive proof of delivery?",
             "expected": ["constructive proof of delivery", "proof of delivery"]},
            {"id": 480, "query": "Who submits claims against carriers?",
             "expected": ["claims", "carrier"]},
        ]
    },
    
    # Pattern 17: Organization Queries (C7.2)
    "pattern_c7_17_organizations": {
        "description": "Organization queries",
        "tests": [
            {"id": 481, "query": "What is the SCO Security Cooperation Organization role?",
             "expected": ["sco", "security cooperation organization"]},
            {"id": 482, "query": "What does DCMA Defense Contract Management Agency do?",
             "expected": ["dcma", "defense contract management agency"]},
            {"id": 483, "query": "What is DTSA Defense Technology Security Administration?",
             "expected": ["dtsa", "defense technology security administration"]},
            {"id": 484, "query": "What is a husbanding agent?",
             "expected": ["husbanding agent"]},
            {"id": 485, "query": "What does DFAS-IN handle for transportation?",
             "expected": ["dfas-in"]},
        ]
    },
    
    # Pattern 18: Forms and Standards Queries
    "pattern_c7_18_forms": {
        "description": "Forms and standards queries",
        "tests": [
            {"id": 486, "query": "What is DD Form 1348-1A used for?",
             "expected": ["dd form 1348-1a"]},
            {"id": 487, "query": "What is iRAPT Receiving Report?",
             "expected": ["irapt"]},
            {"id": 488, "query": "What is SF-153 COMSEC Material Report?",
             "expected": ["sf-153", "comsec"]},
            {"id": 489, "query": "What is the DTR Defense Transportation Regulation?",
             "expected": ["dtr", "defense transportation regulation"]},
            {"id": 490, "query": "What is NISPOM for contractor security?",
             "expected": ["nispom"]},
        ]
    },
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_all_chapter7_tests():
    """Return all Chapter 7 tests as a flat list"""
    all_tests = []
    for pattern_name, pattern_data in TEST_CASES_CHAPTER_7.items():
        for test in pattern_data["tests"]:
            test["pattern"] = pattern_name
            all_tests.append(test)
    return all_tests

def get_chapter7_ground_truth_entities():
    """Get flattened set of all Chapter 7 ground truth entities INCLUDING all valid expansions"""
    all_entities = set()
    
    # Add all entities from ground truth categories
    for category, entities in CHAPTER_7_GROUND_TRUTH.items():
        all_entities.update(entities)
    
    # Add ALL valid acronym expansions (these are NOT hallucinations!)
    VALID_EXPANSIONS = {
        # Common FMS terms (from earlier chapters - NOT hallucinations!)
        "Foreign Military Sales", "foreign military sales",
        "Letter of Offer and Acceptance", "letter of offer and acceptance",
        "Letter Of Offer And Acceptance", "Direct Commercial Sales", "direct commercial sales",
        "Security Cooperation", "security cooperation",
        "Defense Finance and Accounting Service", "defense finance and accounting service",
        "Defense Finance And Accounting Service",
        "Defense Finance and Accounting Services Indianapolis",
        "Defense Finance And Accounting Services Indianapolis",
        "defense finance and accounting services indianapolis",
        "defense articles", "Defense Articles",
        "Man-Portable Air Defense System", "man-portable air defense system",
        "State", "state",
        "SC", "sc",
        
        # DTS expansions
        "Defense Transportation System", "defense transportation system",
        "United States Transportation Command", "united states transportation command",
        "Air Mobility Command", "air mobility command",
        "Surface Deployment and Distribution Command", "surface deployment and distribution command",
        "Military Sealift Command", "military sealift command",
        "Defense Transportation Regulation", "defense transportation regulation",
        
        # Delivery Term expansions
        "Delivery Term Code", "delivery term code",
        "Free On Board", "free on board",
        "Port of Embarkation", "port of embarkation",
        "Port of Debarkation", "port of debarkation",
        "purchaser pickup", "overseas POD", "final destination",
        
        # MAPAD expansions
        "Military Assistance Program Address Directory", "military assistance program address directory",
        "Type Address Code", "type address code",
        "Communication Routing Identifier Code", "communication routing identifier code",
        "mark-for address", "ship-to address", "documentation address",
        "Special Instructions", "special instructions",
        
        # Documentation expansions
        "Notice of Availability", "notice of availability",
        "Offer Release Code", "offer release code",
        "Transportation Control Number", "transportation control number",
        "Bill of Lading", "bill of lading",
        "Commercial Bill of Lading", "commercial bill of lading",
        "Government Bill of Lading", "government bill of lading",
        "Invoicing Receipt Acceptance and Property Transfer",
        
        # Special Transportation expansions
        "Special Assignment Airlift Mission", "special assignment airlift mission",
        "Next Generation Delivery Services", "next generation delivery services",
        "Defense Courier Service", "defense courier service",
        "channel airlift", "AMC Channel",
        "small parcel", "Small Parcel",
        
        # Cargo Preference expansions
        "Cargo Preference", "cargo preference",
        "US Flag", "us flag", "US Flag vessel",
        "P1 service", "P2 service", "P3 service",
        "Determination of Non-Availability", "determination of non-availability",
        "Maritime Administration", "maritime administration",
        "Fly America Act", "fly america act",
        
        # Packaging expansions
        "MIL-STD-129", "mil-std-129",
        "Military Level A", "military level a", "Military Level B", "military level b",
        "Wood Packaging Material", "wood packaging material",
        "International Standards for Phytosanitary Measures",
        "marking", "marking requirements", "wood packaging",
        
        # Classified expansions
        "Transportation Plan", "transportation plan",
        "Communications Security", "communications security",
        "Controlled Cryptographic Items", "controlled cryptographic items",
        "Communications Interoperability and Security Memorandum of Agreement",
        "Defense Counterintelligence and Security Agency",
        "National Industrial Security Program Operating Manual",
        "Committee on National Security Systems",
        "classified", "classified materiel", "classified shipments",
        "facility clearance", "government courier",
        
        # AA&E expansions
        "Arms Ammunition and Explosives", "arms ammunition and explosives",
        "Security Risk Category", "security risk category",
        "Security Risk Categories", "security risk categories",
        "Man Portable Air Defense Systems", "man portable air defense systems",
        "sensitive materiel", "Sensitive Materiel",
        "night vision", "Night Vision",
        
        # HAZMAT expansions
        "Hazardous Materials", "hazardous materials",
        "Hazardous Materials Regulations", "hazardous materials regulations",
        "Pipeline and Hazardous Materials Safety Administration",
        "Hazard Class 1", "hazard class 1",
        "EX-Number", "ex-number", "DOT EX-Number",
        "explosives", "Explosives",
        
        # Export expansions
        "International Traffic in Arms Regulations", "international traffic in arms regulations",
        "Electronic Export Information", "electronic export information",
        "Automated Export System", "automated export system",
        "Customs and Border Protection", "customs and border protection",
        "Internal Transaction Number", "internal transaction number",
        "export license", "license exemption",
        
        # Title Transfer expansions
        "title transfer", "Title Transfer",
        "title passage", "Title Passage",
        "point of origin", "Point of Origin",
        "retention of title", "Retention of Title",
        "Excess Defense Articles", "excess defense articles",
        "ferrying aircraft", "manufacturer", "depot",
        
        # Cost expansions
        "transportation costs", "Transportation Costs",
        "standard transportation percentage", "Standard Transportation Percentage",
        "accessorial charges", "Accessorial Charges",
        "storage charges", "Storage Charges",
        "above-the-line", "30 days",
        
        # Claims expansions
        "Transportation Discrepancy Report", "transportation discrepancy report",
        "tracer action", "Tracer Action",
        "proof of delivery", "Proof of Delivery",
        "constructive proof of delivery", "Constructive Proof of Delivery",
        "carrier liability", "Carrier Liability",
        "claims", "Claims", "loss", "damage",
        
        # Insurance expansions
        "commercial insurance", "Commercial Insurance",
        "self-insure", "Self-Insure",
        "loss or damage", "liability",
        "high value", "High Value",
        
        # Organization expansions
        "Security Cooperation Organization", "security cooperation organization",
        "Defense Contract Management Agency", "defense contract management agency",
        "Defense Technology Security Administration", "defense technology security administration",
        "Designated Government Representative", "designated government representative",
        "husbanding agent", "Husbanding Agent",
        
        # Freight Forwarder expansions
        "freight forwarder", "Freight Forwarder",
        "FMS freight forwarder", "ITAR registration",
        "embassy authorization", "PM/DDTC",
        
        # Common entities from other chapters (NOT hallucinations!)
        "Foreign Military Sales", "foreign military sales",
        "Letter of Offer and Acceptance", "letter of offer and acceptance",
        "Letter Of Offer And Acceptance",
        "Direct Commercial Sales", "direct commercial sales",
        "Defense Finance and Accounting Service", "defense finance and accounting service",
        "Defense Finance And Accounting Service",
        "Defense Finance and Accounting Services Indianapolis",
        "Defense Finance And Accounting Services Indianapolis",
        "defense finance and accounting services indianapolis",
        "Security Cooperation", "security cooperation",
        "Man-Portable Air Defense System", "man-portable air defense system",
        "defense articles", "Defense Articles",
        "State", "state",
        "SC", "sc",
        "DFAS", "dfas",
        
        # Acronyms (case variations)
        "DTS", "dts", "USTRANSCOM", "ustranscom",
        "AMC", "amc", "SDDC", "sddc", "MSC", "msc",
        "DTC", "dtc", "FOB", "fob", "POE", "poe", "POD", "pod",
        "MAPAD", "mapad", "TAC", "tac", "CRIC", "cric",
        "NOA", "noa", "ORC", "orc", "TCN", "tcn", "BL", "bl",
        "SAAM", "saam", "NGDS", "ngds", "DCS", "dcs",
        "DNA", "dna", "MARAD", "marad",
        "WPM", "wpm", "ISPM", "ispm",
        "COMSEC", "comsec", "CCI", "cci", "CISMOA", "cismoa",
        "DCSA", "dcsa", "NISPOM", "nispom", "CNSS", "cnss",
        "AA&E", "aa&e", "SRC", "src", "MANPADS", "manpads",
        "HAZMAT", "hazmat", "HMR", "hmr", "PHMSA", "phmsa", "HC1", "hc1",
        "ITAR", "itar", "EEI", "eei", "AES", "aes", "CBP", "cbp", "ITN", "itn",
        "TDR", "tdr", "DGR", "dgr", "DCMA", "dcma", "DTSA", "dtsa",
        "DTR", "dtr", "SCO", "sco", "IA", "ia", "FMS", "fms",
        "LOA", "loa", "USG", "usg", "DOT", "dot",
        "DFAS-IN", "dfas-in", "iRAPT", "irapt",
        
        # Common terms used in tests
        "DTC 4", "DTC 5", "DTC 7", "DTC 8", "DTC 9",
        "dtc 4", "dtc 5", "dtc 7", "dtc 8", "dtc 9",
        "TAC 1", "TAC 2", "TAC 3", "TAC 4", "TAC 5", "TAC 6",
        "TAC A", "TAC B", "TAC C", "TAC D", "TAC M",
        "tac 1", "tac 2", "tac 3", "tac 4", "tac 5", "tac 6",
        "tac a", "tac b", "tac c", "tac d", "tac m",
        "ORC A", "ORC X", "ORC Y", "ORC Z",
        "orc a", "orc x", "orc y", "orc z",
        "SRC I", "SRC II", "SRC III", "SRC IV",
        "src i", "src ii", "src iii", "src iv",
        "P1", "P2", "P3", "p1", "p2", "p3",
        "DD Form 1348-5", "DD Form 1348-1A", "DD Form 361",
        "dd form 1348-5", "dd form 1348-1a", "dd form 361",
        "SF-153", "sf-153", "MIL-STD-129", "mil-std-129",
        "ISPM 15", "ispm 15", "49 CFR", "49 cfr",
        "46 USC 55305", "ITAR 126.6(a)", "ITAR 126.6(c)",
    }
    
    all_entities.update(VALID_EXPANSIONS)
    
    return all_entities

# =============================================================================
# PRINT SUMMARY
# =============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("CHAPTER 7 ENTITY IMPLEMENTATION SUMMARY")
    print("Transportation")
    print("=" * 80)
    
    print(f"\n📊 NEW ACRONYM PAIRS: {len(CHAPTER_7_ACRONYM_PAIRS)}")
    print(f"📊 GROUND TRUTH CATEGORIES:")
    for cat, entities in CHAPTER_7_GROUND_TRUTH.items():
        print(f"   - {cat}: {len(entities)} entities")
    
    print(f"\n📊 ENTITY PATTERNS:")
    for cat, patterns in CHAPTER_7_ENTITY_PATTERNS.items():
        print(f"   - {cat}: {len(patterns)} patterns")
    
    print(f"\n📊 TEST CASES:")
    total_tests = 0
    for pattern_name, pattern_data in TEST_CASES_CHAPTER_7.items():
        count = len(pattern_data["tests"])
        total_tests += count
        print(f"   - {pattern_name}: {count} tests")
    print(f"   TOTAL: {total_tests} tests")
    
    print(f"\n📊 ENTITY RELATIONSHIPS: {len(CHAPTER_7_ENTITY_RELATIONSHIPS)} relationship groups")
