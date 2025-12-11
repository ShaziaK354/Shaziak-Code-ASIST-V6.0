"""
VECTOR DB DATA QUALITY DIAGNOSTIC
==================================
Uses your .env variables:
- AZURE_AI_SEARCH_ENDPOINT
- AZURE_AI_SEARCH_INDEX  
- AZURE_AI_SEARCH_API_KEY
"""

import os
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# YOUR .ENV VARIABLE NAMES
# =============================================================================

ENDPOINT = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
INDEX = os.getenv("AZURE_AI_SEARCH_INDEX")
API_KEY = os.getenv("AZURE_AI_SEARCH_API_KEY")

print("=" * 70)
print("VECTOR DB DATA QUALITY DIAGNOSTIC")
print("=" * 70)

print(f"\n📋 Credentials:")
print(f"   Endpoint: {ENDPOINT[:50] if ENDPOINT else 'NOT SET'}...")
print(f"   Index: {INDEX if INDEX else 'NOT SET'}")
print(f"   API Key: {'*****' + API_KEY[-4:] if API_KEY else 'NOT SET'}")

if not all([ENDPOINT, INDEX, API_KEY]):
    print("\n❌ Missing credentials! Check .env file.")
    exit(1)

# =============================================================================
# CONNECT TO AZURE AI SEARCH
# =============================================================================

print("\n🔄 Connecting to Azure AI Search...")

try:
    from azure.search.documents import SearchClient
    from azure.core.credentials import AzureKeyCredential
    
    client = SearchClient(
        endpoint=ENDPOINT,
        index_name=INDEX,
        credential=AzureKeyCredential(API_KEY)
    )
    
    # Test connection
    results = client.search(search_text="*", top=1, include_total_count=True)
    total_count = results.get_count()
    print(f"✅ Connected! Total documents: {total_count}")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)

# =============================================================================
# 1. DOCUMENT COUNT & STRUCTURE
# =============================================================================

print("\n" + "=" * 70)
print("1️⃣ DOCUMENT COUNT & STRUCTURE")
print("=" * 70)

print(f"\n   Total documents in index: {total_count}")

if total_count < 200:
    print("   ⚠️ WARNING: Very few docs - data merge likely incomplete!")
elif total_count < 400:
    print("   ⚠️ WARNING: Fewer than expected. Check all chapters included.")
else:
    print("   ✅ Document count looks good")

# Get sample documents
results = client.search(search_text="*", top=200)
docs = list(results)

print(f"\n   Sampled {len(docs)} documents for analysis")

if docs:
    fields = list(docs[0].keys())
    print(f"   Document fields: {fields}")

# =============================================================================
# 2. CHAPTER DISTRIBUTION
# =============================================================================

print("\n" + "=" * 70)
print("2️⃣ CHAPTER DISTRIBUTION")
print("=" * 70)

chapters = Counter()

for doc in docs:
    # Try multiple field names
    ch = (doc.get("chapter") or 
          doc.get("Chapter") or
          (doc.get("metadata", {}).get("chapter") if isinstance(doc.get("metadata"), dict) else None) or
          "Unknown")
    chapters[str(ch)] += 1

print(f"\n   Chapter breakdown:")
for ch, cnt in sorted(chapters.items(), key=lambda x: (x[0] == "Unknown", x[0])):
    pct = cnt / len(docs) * 100
    bar = "█" * int(pct / 3)
    print(f"   Chapter {ch:>10}: {cnt:3d} docs ({pct:5.1f}%) {bar}")

if "Unknown" in chapters and chapters["Unknown"] > len(docs) * 0.3:
    print(f"\n   ⚠️ WARNING: {chapters['Unknown']} docs have no chapter metadata!")

# =============================================================================
# 3. KEY ENTITY COVERAGE
# =============================================================================

print("\n" + "=" * 70)
print("3️⃣ KEY ENTITY COVERAGE")
print("=" * 70)

key_entities = [
    "Secretary of State",
    "SECSTATE", 
    "continuous supervision",
    "general direction",
    "program scope",
    "DSCA",
    "DFAS",
    "ITAR",
    "PM/DDTC",
    "USML",
    "United States Munitions List",
    "FAA",
    "AECA",
    "EO 13637",
]

print(f"\n   Checking {len(key_entities)} key entities...")

entity_results = {}
for entity in key_entities:
    try:
        results = client.search(search_text=entity, top=5)
        count = len(list(results))
        status = "✅" if count > 0 else "❌"
        print(f"   {status} '{entity}': {count} results")
        entity_results[entity] = count
    except Exception as e:
        print(f"   ❌ '{entity}': Error - {e}")
        entity_results[entity] = 0

# =============================================================================
# 4. PROBLEM QUERY ANALYSIS (Q15 & Q11)
# =============================================================================

print("\n" + "=" * 70)
print("4️⃣ PROBLEM QUERY ANALYSIS (Q15 & Q11)")
print("=" * 70)

problem_queries = [
    {
        "name": "Q15 - Secretary of State SA",
        "query": "Secretary of State Security Assistance approval authority",
        "expected": ["continuous supervision", "general direction", "program scope", "FAA", "AECA"]
    },
    {
        "name": "Q11 - ITAR",
        "query": "ITAR International Traffic in Arms Regulations manages",
        "expected": ["USML", "PM/DDTC", "defense articles", "Department of State"]
    }
]

for pq in problem_queries:
    print(f"\n📝 {pq['name']}")
    print(f"   Query: '{pq['query']}'")
    
    try:
        results = client.search(search_text=pq["query"], top=10)
        results_list = list(results)
        print(f"   Results found: {len(results_list)}")
        
        if results_list:
            # Combine all content
            all_content = ""
            for r in results_list:
                content = r.get("content") or r.get("chunk") or r.get("text") or ""
                all_content += " " + content.lower()
            
            # Check expected content
            found = [e for e in pq["expected"] if e.lower() in all_content]
            missing = [e for e in pq["expected"] if e.lower() not in all_content]
            
            coverage = len(found) / len(pq["expected"]) * 100
            print(f"   Coverage: {coverage:.0f}%")
            print(f"   ✅ Found: {found}")
            print(f"   ❌ Missing: {missing}")
            
            # Show top 3 results
            print(f"\n   Top results:")
            for i, r in enumerate(results_list[:3], 1):
                content = r.get("content") or r.get("chunk") or r.get("text") or ""
                chapter = r.get("chapter") or r.get("Chapter") or "?"
                score = r.get("@search.score", 0)
                print(f"   {i}. [Ch {chapter}] (score: {score:.2f})")
                print(f"      {content[:150]}...")
        else:
            print("   ❌ NO RESULTS FOUND!")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

# =============================================================================
# 5. SUMMARY
# =============================================================================

print("\n" + "=" * 70)
print("📊 DIAGNOSTIC SUMMARY")
print("=" * 70)

missing_entities = [e for e, c in entity_results.items() if c == 0]

print(f"""
📈 STATISTICS:
   Total Documents: {total_count}
   Chapters Found: {len([c for c in chapters.keys() if c != "Unknown"])}
   Unknown Chapter Docs: {chapters.get("Unknown", 0)}
   Missing Entities: {len(missing_entities)}
""")

issues = []

if total_count < 300:
    issues.append("LOW DOCUMENT COUNT - Data merge may be incomplete")
    
if chapters.get("Unknown", 0) > 50:
    issues.append("MISSING CHAPTER METADATA - Chunks don't have chapter info")

if missing_entities:
    issues.append(f"MISSING ENTITIES: {missing_entities}")

if issues:
    print("🔴 ISSUES FOUND:")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")
    
    print("""
🔧 RECOMMENDED ACTIONS:
   1. Check original SAMM PDF/chapters - are all included?
   2. Verify chunk metadata during indexing (chapter, section)
   3. Re-index with proper metadata if needed
   4. Check chunking strategy - chunks may be too large/small
""")
else:
    print("✅ No major issues found!")

print("=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
