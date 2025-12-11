"""
Q15 RETRIEVAL DEBUG TOOL
=========================
Debugging why "Secretary of State" chunks exist but aren't retrieved for Q15

Q15: "What does the Secretary of State approve regarding SA?"
Expected: continuous supervision, general direction, program scope, FAA, AECA
"""

import os
import sys

print("=" * 70)
print("Q15 RETRIEVAL DEBUG")
print("=" * 70)

VECTOR_DB_PATH = r"C:\Users\ShaziaKashif\ASIST Project\ASIST2.1\ASIST_V2.1\backend\Chromadb\chroma_db_combined"
COLLECTION_NAME = "samm_all_chapters"

# =============================================================================
# CONNECT TO CHROMADB
# =============================================================================

try:
    import chromadb
    
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)
    print(f"✅ Connected! Total docs: {collection.count()}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# =============================================================================
# 1. FIND ALL "SECRETARY OF STATE" DOCUMENTS
# =============================================================================

print("\n" + "=" * 70)
print("1️⃣ ALL DOCUMENTS WITH 'Secretary of State'")
print("=" * 70)

# Get ALL documents
all_docs = collection.get(limit=200, include=["documents", "metadatas"])
documents = all_docs.get("documents", [])
metadatas = all_docs.get("metadatas", [])

# Find docs with "Secretary of State"
sos_docs = []
for i, (doc, meta) in enumerate(zip(documents, metadatas)):
    if "secretary of state" in doc.lower():
        sos_docs.append({
            "index": i,
            "content": doc,
            "metadata": meta,
            "section_id": meta.get("section_id", "?") if meta else "?"
        })

print(f"\n   Found {len(sos_docs)} documents with 'Secretary of State'")

for i, doc_info in enumerate(sos_docs, 1):
    print(f"\n   📄 Document {i} [{doc_info['section_id']}]:")
    print(f"   Metadata: {doc_info['metadata']}")
    print(f"   Content ({len(doc_info['content'])} chars):")
    print(f"   {'-'*60}")
    print(f"   {doc_info['content'][:500]}...")
    print(f"   {'-'*60}")
    
    # Check for key phrases
    content_lower = doc_info['content'].lower()
    has_continuous = "continuous supervision" in content_lower
    has_general = "general direction" in content_lower
    has_approve = "approve" in content_lower
    has_program = "program" in content_lower
    
    print(f"   Key phrases: continuous_supervision={has_continuous}, general_direction={has_general}, approve={has_approve}")

# =============================================================================
# 2. SIMULATE Q15 QUERY - What does ChromaDB return?
# =============================================================================

print("\n" + "=" * 70)
print("2️⃣ SIMULATING Q15 QUERY - What ChromaDB Returns")
print("=" * 70)

q15_queries = [
    "What does the Secretary of State approve regarding SA?",
    "Secretary of State Security Assistance",
    "Secretary of State approve SA",
    "SECSTATE authority Security Assistance",
    "continuous supervision general direction SA",
]

for query in q15_queries:
    print(f"\n   🔍 Query: '{query}'")
    
    results = collection.query(
        query_texts=[query],
        n_results=5,
        include=["documents", "metadatas", "distances"]
    )
    
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    
    print(f"   Results: {len(docs)}")
    
    # Check if any result has "Secretary of State"
    sos_found = False
    for j, (doc, meta, dist) in enumerate(zip(docs, metas, distances), 1):
        has_sos = "secretary of state" in doc.lower()
        section = meta.get("section_id", "?") if meta else "?"
        
        marker = "✅ HAS SoS" if has_sos else ""
        print(f"      {j}. [{section}] dist={dist:.3f} {marker}")
        print(f"         {doc[:100]}...")
        
        if has_sos:
            sos_found = True
    
    if not sos_found:
        print(f"   ❌ NO 'Secretary of State' in top 5 results!")

# =============================================================================
# 3. CHECK EMBEDDING SIMILARITY
# =============================================================================

print("\n" + "=" * 70)
print("3️⃣ DIRECT SEARCH FOR KEY CONTENT")
print("=" * 70)

# Search for the EXACT content we want
key_searches = [
    "continuous supervision and general direction",
    "Secretary of State responsible SA programs",
    "SECSTATE determines program scope",
    "FAA AECA authority",
]

for search in key_searches:
    print(f"\n   🔍 Search: '{search}'")
    
    results = collection.query(
        query_texts=[search],
        n_results=3,
        include=["documents", "distances"]
    )
    
    docs = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    
    for j, (doc, dist) in enumerate(zip(docs, distances), 1):
        # Check if search terms are in result
        search_lower = search.lower()
        doc_lower = doc.lower()
        
        terms_found = sum(1 for term in search_lower.split() if term in doc_lower)
        total_terms = len(search_lower.split())
        
        print(f"      {j}. dist={dist:.3f} terms={terms_found}/{total_terms}")
        print(f"         {doc[:120]}...")

# =============================================================================
# 4. THE ACTUAL CONTENT WE NEED
# =============================================================================

print("\n" + "=" * 70)
print("4️⃣ CONTENT THAT SHOULD BE RETRIEVED FOR Q15")
print("=" * 70)

print("""
   According to SAMM Chapter 1, for Q15 we need content about:
   
   1. Secretary of State's role in SA:
      - "continuous supervision and general direction of SA programs"
      - "determines whether and when there will be a program"
      - "determines program scope"
      
   2. Legal basis:
      - FAA (Foreign Assistance Act)
      - AECA (Arms Export Control Act)  
      - EO 13637
      
   3. Section: C1.2 or C1.3
""")

# Find if this content exists
print("\n   Searching for this specific content...")

specific_search = "Secretary of State continuous supervision general direction SA programs"
results = collection.query(
    query_texts=[specific_search],
    n_results=10,
    include=["documents", "metadatas", "distances"]
)

docs = results.get("documents", [[]])[0]
metas = results.get("metadatas", [[]])[0]
distances = results.get("distances", [[]])[0]

print(f"\n   Top 10 results for comprehensive search:")
for j, (doc, meta, dist) in enumerate(zip(docs, metas, distances), 1):
    section = meta.get("section_id", "?") if meta else "?"
    has_key_content = any(phrase in doc.lower() for phrase in 
                          ["continuous supervision", "general direction", "secretary of state"])
    
    marker = "⭐" if has_key_content else ""
    print(f"\n   {j}. [{section}] distance={dist:.3f} {marker}")
    print(f"      {doc[:200]}...")

# =============================================================================
# 5. ROOT CAUSE ANALYSIS
# =============================================================================

print("\n" + "=" * 70)
print("📊 ROOT CAUSE ANALYSIS")
print("=" * 70)

print(f"""
🔍 FINDINGS:

   1. Documents with "Secretary of State": {len(sos_docs)}
   
   2. These documents ARE in the database ✅
   
   3. POTENTIAL ISSUES:

      A. EMBEDDING MISMATCH:
         - Query: "What does Secretary of State approve regarding SA?"
         - May not semantically match the chunk about "supervision and direction"
         
      B. DISTANCE THRESHOLD:
         - Relevant chunks may have high distance scores
         - App may be filtering them out
         
      C. TOP-K LIMIT:
         - Only retrieving top 5 results
         - Secretary of State chunks may be ranked 6th, 7th, etc.

🔧 POTENTIAL FIXES:

   1. Increase n_results from 5 to 10 or 15
   
   2. Lower distance threshold (allow more distant matches)
   
   3. Add keyword boosting for entity names
   
   4. Use hybrid search (keyword + semantic)
""")

print("\n" + "=" * 70)
print("DEBUG COMPLETE")
print("=" * 70)
