"""
SAMM Chapter 7 - App Integration Code
=====================================

Copy this code to your app_5_0_E1_5_2.py to enable Chapter 7 entity extraction.

Just paste the CHAPTER_7_ACRONYMS section and the merge code at the end.
"""

# =============================================================================
# PASTE THIS IN YOUR APP (after existing ACRONYM_TO_FULLFORM)
# =============================================================================

CHAPTER_7_ACRONYMS = {
    # Defense Transportation System (C7.6)
    "dts": "defense transportation system",
    "ustranscom": "united states transportation command",
    "amc": "air mobility command",
    "sddc": "surface deployment and distribution command",
    "msc": "military sealift command",
    "dtr": "defense transportation regulation",
    
    # Delivery Terms (C7.4)
    "dtc": "delivery term code",
    "dtc 4": "delivery term code 4",
    "dtc 5": "delivery term code 5",
    "dtc 7": "delivery term code 7",
    "dtc 8": "delivery term code 8",
    "dtc 9": "delivery term code 9",
    "fob": "free on board",
    "poe": "port of embarkation",
    "pod": "port of debarkation",
    
    # MAPAD (C7.7)
    "mapad": "military assistance program address directory",
    "tac": "type address code",
    "tac 1": "type address code 1",
    "tac 2": "type address code 2",
    "tac 3": "type address code 3",
    "tac 4": "type address code 4",
    "tac 5": "type address code 5",
    "tac 6": "type address code 6",
    "tac a": "type address code a",
    "tac b": "type address code b",
    "tac c": "type address code c",
    "tac d": "type address code d",
    "tac m": "type address code m",
    "cric": "communication routing identifier code",
    "ilcs": "integrated logistics communication system",
    
    # Documentation (C7.6, C7.11)
    "noa": "notice of availability",
    "orc": "offer release code",
    "orc a": "offer release code a",
    "orc x": "offer release code x",
    "orc y": "offer release code y",
    "orc z": "offer release code z",
    "bl": "bill of lading",
    "cbl": "commercial bill of lading",
    "gbl": "government bill of lading",
    "irapt": "invoicing receipt acceptance and property transfer",
    
    # Special Transportation (C7.6.2)
    "saam": "special assignment airlift mission",
    "ngds": "next generation delivery services",
    
    # Cargo Preference (C7.9)
    "dna": "determination of non-availability",
    "marad": "maritime administration",
    "p1": "priority 1 service",
    "p2": "priority 2 service",
    "p3": "priority 3 service",
    
    # Packaging/Marking (C7.8)
    "wpm": "wood packaging material",
    "ispm 15": "international standards for phytosanitary measures 15",
    "mil-std-129": "military standard 129",
    
    # Classified Transportation (C7.13, C7.14)
    "comsec": "communications security",
    "cci": "controlled cryptographic items",
    "cismoa": "communications interoperability and security memorandum of agreement",
    "dcsa": "defense counterintelligence and security agency",
    "nispom": "national industrial security program operating manual",
    "cnss": "committee on national security systems",
    "sf-153": "comsec material report",
    
    # AA&E (C7.15)
    "aa&e": "arms ammunition and explosives",
    "src": "security risk category",
    "src i": "security risk category i",
    "src ii": "security risk category ii",
    "src iii": "security risk category iii",
    "src iv": "security risk category iv",
    "manpads": "man portable air defense systems",
    
    # HAZMAT (C7.16)
    "hazmat": "hazardous materials",
    "hmr": "hazardous materials regulations",
    "phmsa": "pipeline and hazardous materials safety administration",
    "hc1": "hazard class 1",
    "ex-number": "exemption number",
    
    # Export Compliance (C7.17)
    "eei": "electronic export information",
    "aes": "automated export system",
    "cbp": "customs and border protection",
    "itn": "internal transaction number",
    
    # Organizations
    "dgr": "designated government representative",
    "dtsa": "defense technology security administration",
    
    # Claims (C7.21)
    "tdr": "transportation discrepancy report",
}

# =============================================================================
# CHAPTER 7 ENTITY PATTERNS - Add to your samm_entity_patterns list
# =============================================================================

CHAPTER_7_PATTERNS = [
    # DTS
    r"\bDTS\b", r"\bDefense\s+Transportation\s+System\b",
    r"\bUSTRANSCOM\b", r"\bSDDC\b", r"\bMSC\b",
    
    # Delivery Terms
    r"\bDTC\s*[4-9]?\b", r"\bDelivery\s+Term\s+Code\b",
    r"\bFOB\b", r"\bFree\s+On\s+Board\b",
    r"\bPOE\b", r"\bPort\s+of\s+Embarkation\b",
    r"\bPOD\b", r"\bPort\s+of\s+Debarkation\b",
    
    # MAPAD
    r"\bMAPAD\b", r"\bMilitary\s+Assistance\s+Program\s+Address\s+Directory\b",
    r"\bTAC\s*[1-6ABCDM]?\b", r"\bType\s+Address\s+Code\b",
    r"\bmark-for\s+address\b",
    
    # Documentation
    r"\bNOA\b", r"\bNotice\s+of\s+Availability\b",
    r"\bORC\s*[AXYZ]?\b", r"\bOffer\s+Release\s+Code\b",
    r"\bBill\s+of\s+Lading\b", r"\b[CG]?BL\b",
    r"\biRAPT\b",
    r"\bDD\s+Form\s+1348-[15]A?\b", r"\bDD\s+Form\s+361\b",
    r"\bSF-153\b",
    
    # Special Transportation
    r"\bSAAM\b", r"\bSpecial\s+Assignment\s+Airlift\s+Mission\b",
    r"\bNGDS\b", r"\bNext\s+Generation\s+Delivery\s+Services\b",
    r"\bDCS\b", r"\bDefense\s+Courier\s+Service\b",
    r"\bAMC\s+Channel\b", r"\bsmall\s+parcel\b",
    
    # Cargo Preference
    r"\bCargo\s+Preference\b", r"\bUS\s+Flag\b",
    r"\bP[123]\b", r"\bP[123]\s+service\b",
    r"\bDNA\b", r"\bDetermination\s+of\s+Non-Availability\b",
    r"\bMARAD\b", r"\bMaritime\s+Administration\b",
    r"\bFly\s+America\s+Act\b",
    
    # Packaging
    r"\bMIL-STD-129\b", r"\bMilitary\s+Level\s+[AB]\b",
    r"\bWPM\b", r"\bWood\s+Packaging\s+Material\b",
    r"\bISPM\s*15\b",
    
    # Classified
    r"\bTransportation\s+Plan\b",
    r"\bCOMSEC\b", r"\bCommunications\s+Security\b",
    r"\bCCI\b", r"\bControlled\s+Cryptographic\s+Items?\b",
    r"\bCISMOA\b", r"\bDCSA\b", r"\bNISPOM\b",
    r"\bclassified\s+materiel\b",
    
    # AA&E
    r"\bAA&E\b", r"\bArms[,]?\s+Ammunition[,]?\s+and\s+Explosives\b",
    r"\bSRC\s*I{0,3}V?\b", r"\bSecurity\s+Risk\s+Categor(?:y|ies)\b",
    r"\bMANPADS\b", r"\bMan\s+Portable\s+Air\s+Defense\s+Systems?\b",
    r"\bsensitive\s+materiel\b",
    
    # HAZMAT
    r"\bHAZMAT\b", r"\bHazardous\s+Materials?\b",
    r"\bHMR\b", r"\bHC1\b", r"\bHazard\s+Class\s+1\b",
    r"\bEX-Number\b", r"\bPHMSA\b",
    
    # Export
    r"\bEEI\b", r"\bElectronic\s+Export\s+Information\b",
    r"\bAES\b", r"\bAutomated\s+Export\s+System\b",
    r"\bCBP\b", r"\bCustoms\s+and\s+Border\s+Protection\b",
    r"\bITN\b", r"\bInternal\s+Transaction\s+Number\b",
    
    # Title
    r"\btitle\s+transfer\b", r"\bretention\s+of\s+title\b",
    r"\bpoint\s+of\s+origin\b",
    
    # Costs
    r"\btransportation\s+costs?\b", r"\baccessorial\s+charges?\b",
    r"\bstorage\s+charges?\b",
    
    # Claims
    r"\bTDR\b", r"\bTransportation\s+Discrepancy\s+Report\b",
    r"\btracer\s+action\b", r"\bproof\s+of\s+delivery\b",
    
    # Freight Forwarder
    r"\bfreight\s+forwarder\b", r"\bFMS\s+freight\s+forwarder\b",
    r"\bDGR\b", r"\bDesignated\s+Government\s+Representative\b",
    
    # Insurance
    r"\bcommercial\s+insurance\b", r"\bself-insure\b",
    
    # Organizations
    r"\bDTSA\b", r"\bDefense\s+Technology\s+Security\s+Administration\b",
    r"\bhusbanding\s+agent\b",
    
    # Regulations
    r"\bDTR\b", r"\bDefense\s+Transportation\s+Regulation\b",
]

# =============================================================================
# MERGE CODE - Paste this after your existing dictionaries
# =============================================================================

# Add Chapter 7 acronyms
# ACRONYM_TO_FULLFORM.update(CHAPTER_7_ACRONYMS)

# Add reverse mappings
# for acr, full in CHAPTER_7_ACRONYMS.items():
#     FULLFORM_TO_ACRONYM[full] = acr.upper()

# Add patterns
# samm_entity_patterns.extend(CHAPTER_7_PATTERNS)

# =============================================================================
# TEST
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("CHAPTER 7 APP INTEGRATION")
    print("=" * 60)
    print(f"\n✅ Acronym pairs: {len(CHAPTER_7_ACRONYMS)}")
    print(f"✅ Entity patterns: {len(CHAPTER_7_PATTERNS)}")
    print("\n📋 Instructions:")
    print("1. Copy CHAPTER_7_ACRONYMS to your app")
    print("2. Copy CHAPTER_7_PATTERNS to your app")
    print("3. Uncomment and run the merge code")
    print("4. Restart your app")
    print("5. Run tests again!")
