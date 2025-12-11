"""
CHAPTER 9 APP ADDITIONS
========================

Add these to your app_5_0_E1_5_2.py file in the ACRONYM_PAIRS dictionary
after the Chapter 4 section (around line 3129).

Copy the section below and paste it in the ACRONYM_PAIRS dictionary.
"""

# =============================================================================
# CHAPTER 9 ACRONYMS - Financial Policies and Procedures
# Add this after the Chapter 4 section in ACRONYM_PAIRS
# =============================================================================

CHAPTER_9_ACRONYM_ADDITIONS = """
        # =================================================================
        # CHAPTER 9 ACRONYMS - Financial Policies and Procedures
        # =================================================================
        # Financial Management Terms
        "fms trust fund": "foreign military sales trust fund",
        "fms admin": "fms administrative surcharge",
        "fms administrative surcharge": "fms administrative surcharge",
        "fms administrative surcharge account": "fms administrative surcharge account",
        "nc": "nonrecurring cost",
        "ncr": "nonrecurring cost recoupment",
        "sdaf": "special defense acquisition fund",
        "ucr": "unfunded civilian retirement",
        "merhc": "medicare-eligible retiree health care",
        "tla-c9": "travel and living allowance",
        
        # Payment & Billing Terms
        "du": "dependable undertaking",
        "raps": "risk assessed payment schedules",
        "caps": "credit assured payment schedules",
        "bloc": "bank letter of credit",
        "sblc": "standby letter of credit",
        "sba-billing": "special billing arrangement",
        "sbl": "special bill letter",
        "tcv": "total case value",
        "dd 645": "billing statement form",
        "dd form 645": "billing statement form",
        "cwa": "cash with acceptance",
        
        # Pricing Components
        "ipc": "indirect pricing component",
        "pcc": "primary category code",
        "lsc": "logistics support charge",
        "psc": "program support charge",
        "pc&h": "packing crating and handling",
        
        # Management Lines
        "pml": "program management line",
        "scml": "small case management line",
        "generic code r6b": "program management line code",
        "generic code r6c": "small case support code",
        "generic code l8a": "case management line code",
        
        # Manpower
        "mtds": "manpower travel data sheets",
        "fte-c9": "full-time equivalent",
        "wy": "work year",
        
        # Financial Systems
        "fmscs": "fms credit system",
        "mcr": "monthly case report",
        "sf 1081": "voucher and schedule of withdrawals and credits",
        "of 1017-g": "journal voucher form",
        
        # DSCA Financial Offices
        "obo/fpre": "financial policy and regional execution directorate",
        "obo/fpre/fp": "financial policy division",
        "cfm": "country financial management division",
        "dbo-c9": "directorate of business operations",
        
        # NATO Organizations (C9)
        "nspa": "nato support and procurement agency",
        "nspo": "nato support organization",
        "shape": "supreme headquarters allied powers europe",
        "nsip": "nato security investment program",
        "nicsma": "nato integrated communication system management agency",
        "epg": "european participating governments",
        "mfp": "major force program",
        
        # Tuition Rates
        "rate a": "full cost tuition rate",
        "rate b": "tuition rate b",
        "rate c": "incremental tuition rate",
        "rate d": "tuition rate d",
        "rate e": "tuition rate e",
        
        # Waivers
        "qai": "quality assurance and inspection",
        "cas waiver": "contract administration services waiver",
        "nc waiver": "nonrecurring cost waiver",
        
        # Legal References
        "22 usc 2761": "aeca section 21",
        "22 usc 2762": "aeca section 22",
        "22 usc 2763": "aeca section 23",
        "22 usc 2795": "aeca section 51",
        
        # Other C9 Terms
        "npor": "non-program of record",
        "above-the-line": "direct case charges",
        "below-the-line": "accessorial charges",
"""

# =============================================================================
# CHAPTER 9 GROUND TRUTH ADDITIONS
# Add to relevant ground truth dictionaries if using Chapter-specific ground truth
# =============================================================================

CHAPTER_9_ORGANIZATIONS = {
    # DSCA Financial Offices
    "OBO/FPRE", "Financial Policy & Regional Execution Directorate",
    "OBO/FPRE/FP", "Financial Policy Division",
    "CFD", "Country Finance Director",
    "CFM", "Country Financial Management Division",
    "DBO", "Directorate of Business Operations",
    
    # Financial
    "DFAS-IN", "Defense Finance and Accounting Services - Indianapolis",
    "FFB", "Federal Financing Bank",
    "FRB", "Federal Reserve Bank",
    
    # NATO
    "NSPA", "NATO Support and Procurement Agency",
    "NSPO", "NATO Support Organization",
    "SHAPE", "Supreme Headquarters Allied Powers Europe",
    "NICSMA", "NATO Integrated Communication System Management Agency",
}

CHAPTER_9_FINANCIAL_TERMS = {
    # Funds
    "FMS Trust Fund", "Foreign Military Sales Trust Fund",
    "FMS Administrative Surcharge", "FMS Admin",
    "SDAF", "Special Defense Acquisition Fund",
    
    # Pricing
    "NC", "Nonrecurring Cost",
    "NCR", "Nonrecurring Cost Recoupment",
    "IPC", "Indirect Pricing Component",
    "PCC", "Primary Category Code",
    "PE", "Price Element",
    "LSC", "Logistics Support Charge",
    "PSC", "Program Support Charge",
    "CAS", "Contract Administration Services",
    "PC&H", "Packing Crating and Handling",
    "DTC", "Delivery Term Code",
    
    # Management Lines
    "PML", "Program Management Line",
    "SCML", "Small Case Management Line",
}

CHAPTER_9_PAYMENT_TERMS = {
    # Terms of Sale
    "DU", "Dependable Undertaking",
    "CWA", "Cash with Acceptance",
    "Cash Flow Financing",
    "RAPS", "Risk Assessed Payment Schedules",
    "CAPS", "Credit Assured Payment Schedules",
    
    # Financing
    "BLOC", "Bank Letter of Credit",
    "LC", "Letter of Credit",
    "SBLC", "Standby Letter of Credit",
    "SBA", "Special Billing Arrangement",
    "SBL", "Special Bill Letter",
    "TCV", "Total Case Value",
    
    # Billing
    "DD 645", "DD Form 645", "Billing Statement",
}

# =============================================================================
# INSTRUCTIONS FOR INTEGRATION
# =============================================================================
"""
HOW TO ADD CHAPTER 9 TO YOUR APP:

1. Open app_5_0_E1_5_2.py

2. Find the ACRONYM_PAIRS dictionary (around line 2476)

3. After the Chapter 4 section (around line 3129), paste the 
   CHAPTER_9_ACRONYM_ADDITIONS content

4. Save the file

5. Test with:
   python run_chapter9_entity_tests.py --url http://172.16.200.12:3000 --pattern all

EXPECTED TEST RESULTS:
- Total Tests: 90 (18 patterns × 5 tests each)
- Target Precision: ≥90%
- Target Recall: ≥85%
- Target F1: ≥90%
- Target Hallucination Rate: ≤5%

TEST ID RANGE: 901-990
"""

if __name__ == "__main__":
    print("=" * 80)
    print("CHAPTER 9 APP ADDITIONS")
    print("Financial Policies and Procedures")
    print("=" * 80)
    
    print("\n📋 Files to use:")
    print("   1. chapter9_entity_implementation.py - Ground truth and test cases")
    print("   2. run_chapter9_entity_tests.py - Test runner")
    print("   3. This file - Acronym additions for app.py")
    
    print("\n📊 Chapter 9 Coverage:")
    print("   - C9.1: Purpose - Financial Policies")
    print("   - C9.2: Financial Management Legal Provisions")
    print("   - C9.3: General Financial Policies")
    print("   - C9.4: Specific Line Item Pricing Information")
    print("   - C9.5: Foreign Military Sales Charges")
    print("   - C9.6: Pricing Waivers")
    print("   - C9.7: Methods Of Financing")
    print("   - C9.8: Terms Of Sale")
    print("   - C9.9: Payment Schedules")
    print("   - C9.10: Billing")
    print("   - C9.11: FMS Payments From Purchasers")
    print("   - C9.12: Disbursement")
    print("   - C9.13: Performance Reporting")
    print("   - C9.14: Financial Reviews")
    print("   - C9.15: FMS Trust Fund Admin Surcharge Account")
    print("   - C9.16: CAS Cost Clearing Account")
    print("   - C9.17: Transportation Cost Clearing Account")
    print("   - C9.18: Program Support Charge")
    
    print("\n🔧 Key Acronyms Added:")
    acronyms = [
        "FMS Trust Fund", "NC", "NCR", "SDAF", "DU", "RAPS", "CAPS",
        "BLOC", "SBLC", "SBA", "SBL", "TCV", "IPC", "PCC", "LSC",
        "PSC", "PML", "SCML", "MTDS", "WY", "FTE", "DD 645",
        "NSPA", "NSPO", "SHAPE", "NSIP", "EPG", "MFP",
        "Rate A", "Rate C", "QAI", "CAS Waiver", "NC Waiver"
    ]
    for i, acr in enumerate(acronyms, 1):
        print(f"   {i:2}. {acr}")
    
    print(f"\n   Total new acronyms: ~75")
