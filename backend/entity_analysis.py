import re
from collections import Counter

doc_text = """[paste chapter text]"""

# ============================================
# HYBRID METHOD: Auto + Manual
# ============================================

# METHOD 1: Pattern-Based Auto-Discovery
def auto_extract_entities(text):
    """Extract entities using government document patterns"""
    
    patterns = {
        # Acronyms (2-6 capital letters)
        'acronyms': r'\b[A-Z]{2,6}\b',
        
        # Secretary positions
        'secretaries': r'Secretary of [A-Z][a-zA-Z\s]+(?=[\.,\s])',
        
        # Under Secretary positions
        'under_secs': r'Under Secretary of Defense for [^.,;]{5,60}(?:\([A-Z\(\)]+\))?',
        
        # Departments
        'departments': r'Department of (?:the )?[A-Z][a-zA-Z\s]+(?=[\.,\s])',
        
        # Offices
        'offices': r'Office of (?:the )?[^.,;]{10,60}(?:\([A-Z\(\)]+\))?',
        
        # Directors
        'directors': r'Director(?:,)? [A-Z][a-zA-Z\s]+',
        
        # Agencies ending in 'Agency'
        'agencies': r'[A-Z][a-zA-Z\s]+ Agency(?:\s\([A-Z]+\))?',
        
        # Commands
        'commands': r'[A-Z][a-zA-Z\s]+ Command(?:s)?(?:\s\([A-Z]+\))?',
        
        # Chiefs/Chairmen
        'chiefs': r'(?:Chairman|Chief) of (?:the )?[^.,;]{10,60}',
    }
    
    entities = set()
    for category, pattern in patterns.items():
        matches = re.findall(pattern, text)
        # Clean up matches
        cleaned = [m.strip() for m in matches if len(m.strip()) > 2]
        entities.update(cleaned)
    
    return entities

# METHOD 2: Known Entities (Domain Knowledge)
def get_known_entities():
    """Manually curated list of common entities"""
    return {
        # Core Government
        'President', 'Congress', 'Senate', 'House',
        
        # DoD Leadership
        'Secretary of Defense', 'SECDEF',
        'Deputy Secretary of Defense',
        
        # State Department
        'Department of State', 'State',
        'Secretary of State', 'SECSTATE',
        
        # DoD Organization
        'DoD', 'Department of Defense',
        'DSCA', 'Defense Security Cooperation Agency',
        
        # Under Secretaries (USDs)
        'USD(P)', 'Under Secretary of Defense for Policy',
        'USD(A&S)', 'Under Secretary of Defense for Acquisition and Sustainment',
        'USD(R&E)', 'Under Secretary of Defense for Research and Engineering',
        'USD(C)', 'Under Secretary of Defense, Comptroller',
        'USD(P&R)', 'Under Secretary of Defense for Personnel and Readiness',
        
        # Military Structure
        'CCMDs', 'Combatant Commands', 'Combatant Commanders',
        'CJCS', 'Chairman of the Joint Chiefs of Staff',
        'Joint Staff', 'Joint Chiefs of Staff',
        'MILDEPs', 'Military Departments',
        'SCOs', 'Security Cooperation Organizations',
        
        # Implementing
        'IAs', 'Implementing Agencies', 'Implementing Agency',
        
        # Defense Agencies
        'DIA', 'Defense Intelligence Agency',
        'NSA', 'National Security Agency',
        'NGA', 'National Geospatial-Intelligence Agency',
        'MDA', 'Missile Defense Agency',
        'DTRA', 'Defense Threat Reduction Agency',
        'DCMA', 'Defense Contract Management Agency',
        'DISA', 'Defense Information Systems Agency',
        'DLA', 'Defense Logistics Agency',
        'DCAA', 'Defense Contract Audit Agency',
        'DFAS', 'Defense Finance and Accounting Service',
        
        # Military Services
        'Department of the Army', 'Army',
        'Department of the Navy', 'Navy',
        'Department of the Air Force', 'Air Force',
        
        # Other Government
        'OMB', 'Office of Management and Budget',
        'DOC', 'Department of Commerce',
    }

# METHOD 3: HYBRID - Combine Both
def hybrid_entity_extraction(text):
    """Best of both: auto-discovery + known entities"""
    
    # Get known entities
    entities = get_known_entities()
    
    # Add auto-discovered entities
    auto_entities = auto_extract_entities(text)
    entities.update(auto_entities)
    
    # Filter out common non-entities
    stop_words = {
        'U.S.', 'US', 'The', 'A', 'An', 'In', 'Of', 'For', 'And', 'Or',
        'SA', 'SC', 'PM', 'AM',  # Too common/ambiguous
    }
    
    entities = {e for e in entities if e not in stop_words}
    
    return sorted(entities)

# ============================================
# EXECUTE HYBRID EXTRACTION
# ============================================

print(" Extracting entities using HYBRID approach...")
print("   (Pattern matching + Manual curation)")
print()

all_entities = hybrid_entity_extraction(doc_text)

print(f" Found {len(all_entities)} potential entities")
print(" Counting frequencies...\n")

# Count frequency for each entity
entity_counts = {}
for entity in all_entities:
    # Use word boundary and case-insensitive
    pattern = rf'\b{re.escape(entity)}\b'
    matches = re.findall(pattern, doc_text, re.IGNORECASE)
    if matches:  # Only include if found in text
        entity_counts[entity] = len(matches)

# Sort by frequency (descending)
sorted_entities = sorted(entity_counts.items(), 
                         key=lambda x: x[1], 
                         reverse=True)

# ============================================
# DISPLAY RESULTS
# ============================================

print("=" * 70)
print("ENTITY FREQUENCY ANALYSIS (Hybrid Method)")
print("=" * 70)
print(f"\n{'Rank':<6} {'Entity':<45} {'Count':<10}")
print("-" * 70)

# Show top 20
TOP_N = 20
for rank, (entity, count) in enumerate(sorted_entities[:TOP_N], 1):
    print(f"{rank:<6} {entity:<45} {count:<10}")

print("\n" + "=" * 70)
print(f" Total entities found: {len(entity_counts)}")
print(f" Top Priority: {sorted_entities[0][0]} ({sorted_entities[0][1]} mentions)")
print(f" Showing top {min(TOP_N, len(sorted_entities))} of {len(sorted_entities)}")
print("=" * 70)

# Save all results to file for reference
with open('entity_frequency_analysis.txt', 'w') as f:
    f.write("COMPLETE ENTITY FREQUENCY ANALYSIS\n")
    f.write("=" * 70 + "\n\n")
    for rank, (entity, count) in enumerate(sorted_entities, 1):
        f.write(f"{rank}. {entity}: {count}\n")

print("\n Full results saved to: entity_frequency_analysis.txt")