"""
╔════════════════════════════════════════════════════════════════════════════╗
║  VERSION: v2.2                                                             ║
║  FILE: app_5_0_E1_3_v2.py                                                  ║
║  DATE: 2025-12-03                                                          ║
║  PREVIOUS: app_5_0_E1_3.py (v2.1)                                          ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  CHANGES:                                                                  ║
║  • BUG FIX: DEPSECDEF → SECDEF substring match bug                         ║
║  • SOLUTION: EXACT MATCH only (no substring matching)                      ║
║  • ADDED: 14 missing entity variations to ACRONYM_PAIRS                    ║
║  • TOTAL: 59 entity variations (was 45)                                    ║
║                                                                            ║
║  APPLY TO: app_5_0_E1_3.py                                                 ║
║  CREATES: app_5_0_E1_3_v2.py                                               ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

INSTRUCTIONS:
=============
1. Copy app_5_0_E1_3.py → app_5_0_E1_3_v2.py (backup)
2. In app_5_0_E1_3_v2.py:
   - Replace ACRONYM_PAIRS (lines ~2476-2548) with SECTION 1 below
   - Replace normalize_entities function (lines ~3112-3180) with SECTION 2 below
   - Delete fullform_to_acronym lines (search: "fullform_to_acronym")
3. Save and restart backend
4. Run tests

"""

# =============================================================================
# SECTION 1: COMPLETE ACRONYM_PAIRS (Replace lines ~2476-2548)
# =============================================================================

ACRONYM_PAIRS_CODE = '''
    # E1.3: ACRONYM PAIRS - Complete with ALL variations
    # EXACT MATCH ONLY - No substring matching!
    # Version: v2.2 (2025-12-03)
    # Total: 59 entity variations
    ACRONYM_PAIRS = {
        # =====================================================================
        # ORGANIZATIONS
        # =====================================================================
        "dsca": "defense security cooperation agency",
        "defense security cooperation agency": "defense security cooperation agency",
        "director dsca": "director dsca",
        
        "dfas": "defense finance and accounting service",
        "defense finance and accounting service": "defense finance and accounting service",
        
        "dod": "department of defense",
        "department of defense": "department of defense",
        
        "dos": "department of state",
        "department of state": "department of state",
        "state": "department of state",
        "state department": "department of state",
        
        "secdef": "secretary of defense",
        "secretary of defense": "secretary of defense",
        
        "depsecdef": "deputy secretary of defense",
        "deputy secretary of defense": "deputy secretary of defense",
        
        "secstate": "secretary of state",
        "secretary of state": "secretary of state",
        
        "dcma": "defense contract management agency",
        "defense contract management agency": "defense contract management agency",
        
        "disa": "defense information systems agency",
        "defense information systems agency": "defense information systems agency",
        
        "dla": "defense logistics agency",
        "defense logistics agency": "defense logistics agency",
        
        "dtra": "defense threat reduction agency",
        "mda": "missile defense agency",
        "nga": "national geospatial-intelligence agency",
        "nsa": "national security agency",
        "usasac": "u.s. army security assistance command",
        "nipo": "navy international programs office",
        
        # Combatant Commands
        "ccmd": "combatant command",
        "ccmds": "combatant commands",
        "combatant command": "combatant command",
        "combatant commands": "combatant commands",
        "cocom": "combatant command",
        "gcc": "geographic combatant command",
        
        # Combatant Commanders
        "ccdr": "combatant commander",
        "ccdrs": "combatant commanders",
        "combatant commander": "combatant commander",
        "combatant commanders": "combatant commanders",
        
        # Joint Chiefs
        "cjcs": "chairman of the joint chiefs of staff",
        "chairman of the joint chiefs of staff": "chairman of the joint chiefs of staff",
        "jcs": "joint chiefs of staff",
        "joint chiefs of staff": "joint chiefs of staff",
        "joint chiefs": "joint chiefs of staff",
        
        # Implementing Agencies
        "ia": "implementing agency",
        "implementing agency": "implementing agency",
        "ias": "implementing agencies",
        "implementing agencies": "implementing agencies",
        
        # Military Departments
        "mildep": "military department",
        "mildeps": "military departments",
        "military department": "military department",
        "military departments": "military departments",
        "army": "army",
        "navy": "navy",
        "air force": "air force",
        
        # Under Secretaries
        "usd(p)": "under secretary of defense for policy",
        "under secretary of defense for policy": "under secretary of defense for policy",
        "usd(a&s)": "under secretary of defense for acquisition and sustainment",
        "under secretary of defense for acquisition and sustainment": "under secretary of defense for acquisition and sustainment",
        "usd(c)": "under secretary of defense (comptroller)",
        "usd(p&r)": "under secretary of defense for personnel and readiness",
        
        # =====================================================================
        # PROGRAMS
        # =====================================================================
        "sc": "security cooperation",
        "security cooperation": "security cooperation",
        
        "sa": "security assistance",
        "security assistance": "security assistance",
        
        "fms": "foreign military sales",
        "foreign military sales": "foreign military sales",
        
        "fmf": "foreign military financing",
        "foreign military financing": "foreign military financing",
        
        "imet": "international military education and training",
        "international military education and training": "international military education and training",
        
        "dcs": "direct commercial sales",
        "bpc": "building partner capacity",
        "building partner capacity": "building partner capacity",
        
        "eda": "excess defense articles",
        
        # =====================================================================
        # AUTHORITIES / LEGAL
        # =====================================================================
        "faa": "foreign assistance act",
        "foreign assistance act": "foreign assistance act",
        "section 503": "faa section 503",
        "faa section 503": "faa section 503",
        
        "aeca": "arms export control act",
        "arms export control act": "arms export control act",
        
        "ndaa": "national defense authorization act",
        
        # DoD Directives
        "dodd": "department of defense directive",
        "dodd 5105.65": "dod directive 5105.65",
        "dod directive 5105.65": "dod directive 5105.65",
        "dodd 5132.03": "dod directive 5132.03",
        "dod directive 5132.03": "dod directive 5132.03",
        
        # Executive Orders
        "eo": "executive order",
        "e.o.": "executive order",
        "e.o. 13637": "executive order 13637",
        "eo 13637": "executive order 13637",
        "executive order 13637": "executive order 13637",
        
        # =====================================================================
        # OTHER
        # =====================================================================
        "gef": "guidance for the employment of the force",
        "guidance for the employment of the force": "guidance for the employment of the force",
        "guidance for employment of the force": "guidance for the employment of the force",
    }
'''

# =============================================================================
# SECTION 2: CLEAN normalize_entities FUNCTION (Replace lines ~3112-3180)
# =============================================================================

NORMALIZE_FUNCTION_CODE = '''
    def normalize_entities(self, entities: List[str]) -> set:
        """
        E1.3 v2: Normalize entities using EXACT MATCH ONLY
        
        Version: v2.2 (2025-12-03)
        Fix: Removed substring matching to prevent DEPSECDEF → SECDEF bug
        
        Rules:
        1. Filter out generic words
        2. EXACT MATCH: acronym OR full form → canonical form
        3. No substring matching (prevents bugs)
        
        Example:
            Input:  ['DFAS', 'Defense Finance and Accounting Service', 'programs']
            Output: {'defense finance and accounting service'}  (merged + filtered)
        """
        normalized = set()
        
        for entity in entities:
            entity_lower = entity.lower().strip()
            
            # Skip empty
            if not entity_lower:
                continue
            
            # Skip generic words
            if entity_lower in self.GENERIC_WORDS:
                print(f"[EntityMetrics E1.3] Filtered generic word: '{entity}'")
                continue
            
            # EXACT MATCH: Is it directly in ACRONYM_PAIRS?
            if entity_lower in self.ACRONYM_PAIRS:
                # Get canonical form
                canonical = self.ACRONYM_PAIRS[entity_lower]
                normalized.add(canonical)
                if entity_lower != canonical:
                    print(f"[EntityMetrics E1.3] Normalized '{entity}' → '{canonical}'")
                continue
            
            # NO MATCH: Keep as-is (lowercased)
            normalized.add(entity_lower)
        
        return normalized
'''

# =============================================================================
# SECTION 3: LINES TO DELETE (Search and remove these)
# =============================================================================

LINES_TO_DELETE = '''
# DELETE any line containing "fullform_to_acronym"
# Example lines to find and delete:

self.fullform_to_acronym = {v: k for k, v in self.ACRONYM_PAIRS.items()}

# And any usage like:
if entity_lower in self.fullform_to_acronym:
    acronym = self.fullform_to_acronym[entity_lower]
'''

# =============================================================================
# PRINT INSTRUCTIONS
# =============================================================================

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║  E1.3 v2 PATCH - APPLY INSTRUCTIONS                                        ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  STEP 1: Create backup                                                     ║
║          Copy app_5_0_E1_3.py → app_5_0_E1_3_v2.py                         ║
║                                                                            ║
║  STEP 2: Edit app_5_0_E1_3_v2.py                                           ║
║          a) Find ACRONYM_PAIRS = { (line ~2476)                            ║
║          b) Select entire dictionary to closing }                          ║
║          c) Replace with SECTION 1 code above                              ║
║                                                                            ║
║  STEP 3: Replace normalize_entities function                               ║
║          a) Find "def normalize_entities" (line ~3112)                     ║
║          b) Select entire function                                         ║
║          c) Replace with SECTION 2 code above                              ║
║                                                                            ║
║  STEP 4: Delete fullform_to_acronym                                        ║
║          a) Search for "fullform_to_acronym"                               ║
║          b) Delete all lines containing it                                 ║
║                                                                            ║
║  STEP 5: Save file (Ctrl+S)                                                ║
║                                                                            ║
║  STEP 6: Restart backend with NEW file                                     ║
║          python app_5_0_E1_3_v2.py                                         ║
║                                                                            ║
║  STEP 7: Run tests                                                         ║
║          python run_entity_tests.py --url http://127.0.0.1:3000 \\         ║
║                 --start 1 --end 100                                        ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("\n" + "="*80)
    print("SECTION 1: ACRONYM_PAIRS (Copy this)")
    print("="*80)
    print(ACRONYM_PAIRS_CODE)
    
    print("\n" + "="*80)
    print("SECTION 2: normalize_entities function (Copy this)")
    print("="*80)
    print(NORMALIZE_FUNCTION_CODE)
    
    print("\n" + "="*80)
    print("SECTION 3: DELETE these patterns")
    print("="*80)
    print(LINES_TO_DELETE)
