"""
CHAPTER 6 COMPREHENSIVE ENTITY LIST
====================================

Extracted SYSTEMATICALLY from SAMM Chapter 6 content (samm.dsca.mil/chapter/chapter-6)
NOT based on test questions - covers ALL entities in chapter for ANY query.

Chapter 6: FMS Case Implementation and Execution

This is like the SAMM Acronym Glossary - comprehensive from source document.
"""

# =============================================================================
# CHAPTER 6 ACRONYMS (Extracted from Chapter 6 text)
# Format: "acronym": "full form"
# =============================================================================
CHAPTER_6_ACRONYMS = {
    # Core Implementation Terms
    "EI": "Emergency Implementation",  # C6.1.2
    "OA": "Obligational Authority",  # C6.1.1
    "OED": "Offer Expiration Date",  # C6.1.3
    "SSC": "Supply/Services Complete",  # C6.7.3.1.2
    
    # Data Systems
    "DSAMS": "Defense Security Assistance Management System",  # C6.1.1
    "DIFS": "Defense Integrated Financial System",  # C6.1.1
    "CPRS": "Case Performance Reporting System",  # C6.1.1
    "CTS": "Case Tracking System",  # C6.7.3.2
    "SCIP": "Security Cooperation Information Portal",  # C6.2.4
    
    # Financial Organizations
    "DFAS": "Defense Finance and Accounting Service",  # C6.1.2
    "DFAS-IN": "Defense Finance and Accounting Services - Indianapolis",  # C6.1.3
    "CFD": "Country Finance Director",  # C6.1.2
    "DWCF": "Defense Working Capital Fund",  # C6.4.3.2.9
    "WCF": "Working Capital Fund",  # C6.4.3.2.9
    
    # DSCA Organizations
    "DSCA": "Defense Security Cooperation Agency",
    "OBO": "Office of Business Operations",  # C6.1.2
    "OBO/FPRE": "Office of Business Operations, Financial Policy & Regional Execution Directorate",  # C6.8.1
    "OBO/FPRE/FP": "Financial Policy Division",  # C6.4.10.7
    "OBO/IMT/EADS": "Information Management and Technology Directorate, Enterprise Application Development and Support Division",  # C6.7.2.5
    "IOPS": "Office of International Operations",  # C6.2.3
    "IOPS/REX": "International Operations, Regional Execution Directorate",  # C6.3.7.7.1
    "IOPS/GEX/SCD": "International Operations, Global Execution Directorate, Security Cooperation Division",  # C6.6.1.8
    "IOPS/GEX/CWD": "International Operations, Global Execution Directorate, Case Writing and Development Division",  # C6.7.5.2
    "IOPS/WPN": "International Operations, Weapons Directorate",  # C6.3.9.4
    "SPP": "Office of Strategy, Plans, and Policy",  # C6.3.4.1.1
    "SPP/EPA": "Execution Policy and Analysis Directorate",  # C6.7.5
    "ADM/PIE": "Office of Administration, Performance, Improvement, and Effectiveness Directorate",  # C6.3.11.2
    "FO/OGC": "Front Office, Office of the General Counsel",  # C6.3.4.1.1
    "CPD": "Country Portfolio Director",  # C6.2.3
    
    # DoD Organizations
    "DoD": "Department of Defense",
    "MILDEP": "Military Department",  # C6.1.1
    "IA": "Implementing Agency",  # C6.1.1
    "ICP": "Inventory Control Point",  # C6.4.3.1
    "DLA": "Defense Logistics Agency",  # C6.3.4.6
    "ILCO": "International Logistics Control Office",  # C6.4.4
    "SCO": "Security Cooperation Organization",  # C6.1.3.1
    "OSD": "Office of the Secretary of Defense",  # C6.4.6.1.1
    
    # Defense Officials
    "USD(P)": "Under Secretary of Defense for Policy",  # C6.4.6.1.1
    "USD(A&S)": "Under Secretary of Defense for Acquisition and Sustainment",  # C6.4.6.1.1
    "ASD(RA)": "Assistant Secretary of Defense for Reserve Affairs",  # C6.4.6.1.2
    "CCDR": "Combatant Commander",  # C6.4.1.1
    "CJCS": "Chairman of the Joint Chiefs of Staff",  # C6.4.1
    
    # State Department
    "State": "Department of State",  # C6.6.1
    "State (PM)": "Bureau of Political-Military Affairs",  # C6.2.3.1
    
    # Case Types
    "LOA": "Letter of Offer and Acceptance",  # C6.1.1
    "FMS": "Foreign Military Sales",  # C6.1.1
    "CLSSA": "Cooperative Logistics Supply Support Arrangement",  # C6.4.3.2
    "FMSO": "Foreign Military Sales Order",  # C6.4.3.2.1
    "FMSO I": "Foreign Military Sales Order I",  # C6.4.3.2.1
    "FMSO II": "Foreign Military Sales Order II",  # C6.4.3.2.2
    
    # Financial Terms
    "FMF": "Foreign Military Financing",  # C6.3.4.1.1
    "MAP": "Military Assistance Program",  # C6.3.4.1.1
    "IMET": "International Military Education and Training",  # C6.6.1.8
    "EDA": "Excess Defense Articles",  # C6.4
    "BPC": "Building Partner Capacity",  # C6.3.4.1.2
    "O&M": "Operations and Maintenance",  # C6.4.10.9.1
    "PA": "Procurement Appropriation",  # C6.4.10.9.1
    "RDT&E": "Research, Development, Test and Evaluation",  # C6.4.10.9.1
    "PC&H": "Packing, Crating, and Handling",  # C6.4.10.9.4
    "VAT": "Value Added Tax",  # Table C6.T7
    
    # Acquisition/Contracting
    "FAR": "Federal Acquisition Regulation",  # C6.3.1
    "DFARS": "Defense FAR Supplement",  # C6.3.1
    "RFP": "Request for Proposal",  # C6.3.11
    "SOW": "Statement of Work",  # C6.3.5.2
    "PWS": "Performance Work Statement",  # C6.3.11.1
    "CICA": "Competition in Contracting Act",  # C6.3.4
    "TAA": "Technical Assistance Agreement",  # C6.3.3
    "CLIN": "Contract Line Item Number",  # Figure C6.F2
    "ARP": "Acquisition Requirements Package",  # Figure C6.F2
    
    # Supply/Logistics
    "MILSTRIP": "Military Standard Requisitioning and Issue Procedures",  # C6.4.3
    "DTS": "Defense Transportation System",  # C6.4
    "F/AD": "Force/Activity Designator",  # C6.4.1
    "UND": "Urgency of Need Designator",  # C6.4.1
    "JMPAB": "Joint Materiel Priority Allocation Board",  # C6.4.1
    "UMMIPS": "Uniform Material Movement and Issue Priority System",  # C6.4.3.2
    "CBS": "Commercial Buying Service",  # C6.4.4
    "TVL": "Tailored Vendor Logistics",  # C6.4.5
    "PROS": "Parts and Repair Ordering System",  # C6.4.4
    "SNAP": "Simplified Non-Standard Acquisition Process",  # C6.4.4
    "NSN": "National Stock Number",  # C6.4.10.6
    "TCN": "Transportation Control Number",  # C6.4.10.6
    "MOS": "Months of Supply",  # C6.7.2.7.1
    
    # Documents/Forms
    "SDR": "Supply Discrepancy Report",  # C6.3.8
    "SF 364": "Standard Form 364",  # C6.4.10
    "EUC": "End Use Certificate",  # C6.3.10
    "EUM": "End Use Monitoring",  # C6.2.4
    "EEUM": "Enhanced End Use Monitoring",  # C6.2.4
    "DoD FMR": "DoD Financial Management Regulation",  # C6.2.4
    "DLM": "Defense Logistics Management",  # C6.4.10
    "DLMS": "Defense Logistics Management Standards",  # C6.4.10
    "JTR": "Joint Travel Regulations",  # C6.5.3
    "CN": "Congressional Notification",  # C6.2.3
    "LOR": "Letter of Request",  # C6.3.4.2
    
    # Programs/Equipment
    "GFE": "Government Furnished Equipment",  # C6.4.10.8
    "GFM": "Government Furnished Materiel",  # C6.4.10.8
    "SME": "Significant Military Equipment",  # C6.4.9
    "MDE": "Major Defense Equipment",  # Table C6.T7
    "MTT": "Mobile Training Team",  # C6.6.1.8
    "LTD": "Language Training Detachment",  # C6.6.1.8
    "R&R": "Repair and Return",  # C6.4.8.2
    
    # Review Types
    "FMR": "Financial Management Review",  # C6.5
    "PMR": "Program Management Review",  # C6.5
    "SAR": "Security Assistance Review",  # Table C6.T5
    "CRR": "Case Reconciliation Review",  # Table C6.T5
    "SAMR": "Security Assistance Management Review",  # Table C6.T6
    
    # Special Programs
    "NATO": "North Atlantic Treaty Organization",  # C6.7.6.3
    "ENJJPT": "Euro-NATO Joint Jet Pilot Training Program",  # C6.7.6.3
    "ECISAP": "Electronic Combat International Security Assistance Program",  # C6.7.6.3
    "EW": "Electronic Warfare",  # C6.7.6.3
    "SOFA": "Status of Forces Agreement",  # mentioned
    
    # Legal/Regulatory
    "AECA": "Arms Export Control Act",  # C6.4.6
    "USG": "United States Government",  # C6.1.1
    "USC": "United States Code",  # C6.3.4
    "CFR": "Code of Federal Regulations",  # C6.3.3
    "DoDI": "Department of Defense Instruction",  # C6.3.10
    "CJCSI": "Chairman of the Joint Chiefs of Staff Instruction",  # C6.4.1
    "CUI": "Controlled Unclassified Information",  # C6.4.1.3
    
    # Codes/Identifiers
    "TA": "Type of Assistance",  # C6.4.3.1
    "SOS": "Source of Supply",  # C6.4.3.1
    "ORC": "Offer Release Code",  # Table C6.T7
    "SCML": "Small Case Management Line",  # C6.8.1
    
    # Amendment/Modification Terms
    "ETP": "Exception to Policy",  # C6.7.5
    "SES": "Senior Executive Service",  # C6.7.5
    "FY": "Fiscal Year",  # C6.7.2.3.1
    
    # Milestone Codes
    "DREACT": "Reactivation Authorized Milestone",  # C6.7.2.5
    "MILREACT": "MILDEP Reactivation",  # C6.7.2.5.1.1
}

# =============================================================================
# CHAPTER 6 MULTI-WORD ENTITIES (Terms that need pattern matching)
# These are compound terms from Chapter 6 that appear as-is in text
# =============================================================================
CHAPTER_6_MULTIWORD_ENTITIES = [
    # Case Implementation (C6.1)
    "Routine Case Implementation",
    "Emergency Implementation",
    "Delayed Case Implementation",
    "case implementation",
    "case execution",
    "implementing instructions",
    "Obligational Authority",
    "financial implementation",
    "initial deposit",
    "case manager",
    "case managers",
    
    # Case Execution (C6.2)
    "case execution",
    "FMS case life cycle",
    "delivery status",
    "timely manner",
    "case files",
    "General FMS Case Files",
    "Execution Records",
    "Disbursement Documentation",
    "audit trail",
    "retention period",
    "case closure",
    
    # Acquisition (C6.3)
    "Compliance with Department of Defense Regulations",
    "Certified Cost or Pricing Data",
    "Incentive Clauses",
    "other than full and open competition",
    "sole source",
    "International Agreement",
    "simplified acquisition threshold",
    "Legal Requirements",
    "Policy Requirements",
    "Timing of Requests",
    "FMS Purchaser Involvement",
    "Source Selection",
    "contract negotiations",
    "Contingent Fees",
    "sales commissions",
    "agent fees",
    "bona fide",
    "Prior Notification",
    "Purchaser Approval Thresholds",
    "Warranties",
    "Supply Discrepancy Report",
    "Offsets",
    "offset arrangements",
    "offset costs",
    "End Use Certificates",
    "Acquisition Planning Activities",
    
    # Logistics (C6.4)
    "Force/Activity Designator",
    "Urgency of Need Designator",
    "Project Codes",
    "Standard Requisitions",
    "Cooperative Logistics Supply Support Arrangements",
    "CLSSA requirements",
    "FMSO I maturity",
    "augmentation stock",
    "Commercial Buying Service",
    "FMS Tailored Vendor Logistics",
    "Diversions and Withdrawals",
    "Operational Readiness Impact",
    "Report to Congress",
    "System Support Buyout",
    "Repair Programs",
    "Direct Exchange",
    "Repair and Return",
    "Returns",
    "Supply Discrepancies",
    "Timeframes for Submission",
    "Supply Discrepancy Report Documentation",
    "Supply Discrepancy Report Responses",
    "Shipment Documentation",
    "Financial Guidelines",
    "Financing Approved Supply Discrepancy Reports",
    
    # Case Reviews (C6.5)
    "General Case Reviews",
    "Reasons for Case Review",
    "Cultural Days",
    "Frequency and Timing",
    "Scope of Reviews",
    "Representation at Case Reviews",
    "Standardized Review Formats",
    "Requirements and Guidelines",
    "Country-Level",
    "Service-Level",
    "Program-Level",
    "Case-Level",
    "Program Management Review",
    "Financial Management Review",
    "Security Assistance Review",
    "Case Reconciliation Review",
    "Security Assistance Management Review",
    
    # Suspension (C6.6)
    "Suspension",
    "suspension of delivery",
    "Brooke Amendment",
    "contract termination",
    "sanctions",
    "Mobile Training Teams",
    "Language Training Detachments",
    
    # Amendments/Modifications (C6.7)
    "Amendments",
    "Modifications",
    "Concurrent Modifications",
    "LOA Amendment",
    "LOA Modification",
    "FMS Case Amendment",
    "FMS Case Modification",
    "change in scope",
    "within-scope changes",
    "scope increase",
    "scope decrease",
    "Restatements",
    "Reactivating Cancelled Offers",
    "Pen and Ink Changes",
    "Minor Changes",
    "Major Changes",
    "Amendment Implementation",
    "Modification Implementation",
    "Amendment and/or Modification Formats",
    "Request for Exceptions to Policy",
    "Exception to Policy",
    "Follow-on Support Services",
    "Financial Information for Amendments",
    "$50,000 Break Point",
    "Amendment Financial Requirements",
    "Monitoring Funds",
    "Price Increases During Case Closure",
    "Purchaser Acknowledgement",
    "Reduction of Value",
    "Minimal-Dollar Value Lines",
    "case value",
    "case line",
    "case notes",
    "case remarks",
    
    # Case Cancellation (C6.8)
    "Purchaser-Requested Case Cancellations",
    "United States Government-Requested Case Cancellations",
    "termination costs",
    "administrative costs",
    "non-refundable amount",
    "FMS administrative surcharge",
    
    # Organizations
    "Defense Security Cooperation Agency",
    "Implementing Agency",
    "Security Cooperation Organization",
    "Country Finance Director",
    "Country Portfolio Director",
    "Office of Business Operations",
    "Office of International Operations",
    "Financial Policy Division",
    "contracting officer",
    "case manager",
    "program office",
    
    # Financial Terms
    "Defense Working Capital Fund",
    "Working Capital Fund",
    "initial deposit",
    "termination liability",
    "FMS Administrative Surcharge",
    "payment schedule",
    "billing cycle",
    "accrued costs",
    "estimated costs",
    
    # Legal References
    "Arms Export Control Act",
    "Federal Acquisition Regulation",
    "Defense FAR Supplement",
    "Competition in Contracting Act",
    "Standard Terms and Conditions",
    "LOA Standard Terms and Conditions",
]

# =============================================================================
# CHAPTER 6 TABLES AND FIGURES (References)
# =============================================================================
CHAPTER_6_REFERENCES = [
    # Tables
    "Table C6.T1", "Table C6.T2", "Table C6.T3", "Table C6.T4",
    "Table C6.T5", "Table C6.T6", "Table C6.T7", "Table C6.T8",
    
    # Figures
    "Figure C6.F1", "Figure C6.F2", "Figure C6.F3",
    "Figure C6.F4", "Figure C6.F5",
    
    # Sections
    "C6.1", "C6.2", "C6.3", "C6.4", "C6.5", "C6.6", "C6.7", "C6.8",
    "C6.1.1", "C6.1.2", "C6.1.3",
    "C6.2.1", "C6.2.2", "C6.2.3", "C6.2.4", "C6.2.5", "C6.2.6",
    "C6.3.1", "C6.3.2", "C6.3.3", "C6.3.4", "C6.3.5", "C6.3.6",
    "C6.3.7", "C6.3.8", "C6.3.9", "C6.3.10", "C6.3.11",
    "C6.4.1", "C6.4.2", "C6.4.3", "C6.4.4", "C6.4.5", "C6.4.6",
    "C6.4.7", "C6.4.8", "C6.4.9", "C6.4.10",
    "C6.5.1", "C6.5.2", "C6.5.3", "C6.5.4", "C6.5.5", "C6.5.6", "C6.5.7", "C6.5.8",
    "C6.6.1", "C6.6.2",
    "C6.7.1", "C6.7.2", "C6.7.3", "C6.7.4", "C6.7.5", "C6.7.6",
    "C6.8.1", "C6.8.2",
    
    # Cross-References
    "Section C5.4.3", "Section C5.4.20",
    "Chapter 7", "Chapter 8", "Chapter 9", "Chapter 10", "Chapter 15", "Chapter 16",
    "Table C5.T13", "Table C9.T2a", "Figure C5.F4", "Figure C9.F7",
    "Appendix 6", "Appendix 7", "Appendix 8",
]

# =============================================================================
# COMBINED ENTITY PATTERNS FOR APP INTEGRATION
# =============================================================================
def get_chapter6_entity_patterns():
    """
    Returns all Chapter 6 entities formatted for samm_entity_patterns
    """
    patterns = []
    
    # Add all acronyms
    for acronym, fullform in CHAPTER_6_ACRONYMS.items():
        patterns.append(acronym)
        patterns.append(fullform)
        # Add lowercase versions
        patterns.append(acronym.lower())
        patterns.append(fullform.lower())
    
    # Add multi-word entities
    for entity in CHAPTER_6_MULTIWORD_ENTITIES:
        patterns.append(entity)
        patterns.append(entity.lower())
    
    # Add references
    patterns.extend(CHAPTER_6_REFERENCES)
    
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
    print("CHAPTER 6 COMPREHENSIVE ENTITY LIST")
    print("FMS Case Implementation and Execution")
    print("Extracted from SAMM Chapter 6 Content")
    print("=" * 80)
    
    print(f"\n📊 ACRONYMS: {len(CHAPTER_6_ACRONYMS)}")
    print(f"📊 MULTI-WORD ENTITIES: {len(CHAPTER_6_MULTIWORD_ENTITIES)}")
    print(f"📊 REFERENCES (Tables/Figures/Sections): {len(CHAPTER_6_REFERENCES)}")
    
    all_patterns = get_chapter6_entity_patterns()
    print(f"📊 TOTAL UNIQUE PATTERNS: {len(all_patterns)}")
    
    print("\n" + "=" * 80)
    print("SAMPLE ACRONYMS (first 20):")
    print("=" * 80)
    for i, (acr, full) in enumerate(list(CHAPTER_6_ACRONYMS.items())[:20]):
        print(f"   {acr}: {full}")
    
    print("\n" + "=" * 80)
    print("SAMPLE MULTI-WORD ENTITIES (first 20):")
    print("=" * 80)
    for entity in CHAPTER_6_MULTIWORD_ENTITIES[:20]:
        print(f"   {entity}")
