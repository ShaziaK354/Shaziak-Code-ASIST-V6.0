"""
CHROMADB COMPARISON DIAGNOSTIC
==============================
Compares:
1. chroma_db_combined (merged - app uses this)
2. chroma_db_combined_1 (chapter-wise originals)

Finds what's missing in the merge!
"""

import os
import sys
from collections import Counter

print("=" * 70)
print("CHROMADB COMPARISON DIAGNOSTIC")
print("=" * 70)

# =============================================================================
# PATHS
# =============================================================================

BASE_PATH = r"C:\Users\ShaziaKashif\ASIST Project\ASIST2.1\ASIST_V2.1\backend\Chromadb"

MERGED_DB_PATH = os.path.join(BASE_PATH, "chroma_db_combined")
CHAPTER_DB_PATH = os.path.join(BASE_PATH, "chroma_db_combined_1")

# Also try relative paths
if not os.path.exists(MERGED_DB_PATH):
    MERGED_DB_PATH = "./Chromadb/chroma_db_combined"
    CHAPTER_DB_PATH = "./Chromadb/chroma_db_combined_1"

print(f"\n📂 Paths:")
print(f"   Merged DB: {MERGED_DB_PATH}")
print(f"   Chapter DB: {CHAPTER_DB_PATH}")

# =============================================================================
# CONNECT TO CHROMADB
# =============================================================================

try:
    import chromadb
except ImportError:
    print("❌ ChromaDB not installed. Run: pip install chromadb")
    sys.exit(1)

# =============================================================================
# 1. ANALYZE MERGED DATABASE (what app uses)
# =============================================================================

print("\n" + "=" * 70)
print("1️⃣ MERGED DATABASE (chroma_db_combined)")
print("=" * 70)

if os.path.exists(MERGED_DB_PATH):
    try:
        merged_client = chromadb.PersistentClient(path=MERGED_DB_PATH)
        merged_collections = merged_client.list_collections()
        
        print(f"\n   ✅ Connected!")
        print(f"   Collections: {len(merged_collections)}")
        
        merged_total = 0
        merged_data = {}
        
        for coll in merged_collections:
            count = coll.count()
            merged_total += count
            merged_data[coll.name] = count
            print(f"   • {coll.name}: {count} documents")
        
        print(f"\n   📊 TOTAL in merged DB: {merged_total} documents")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        merged_total = 0
else:
    print(f"   ❌ Path not found!")
    merged_total = 0

# =============================================================================
# 2. ANALYZE CHAPTER DATABASE (original data)
# =============================================================================

print("\n" + "=" * 70)
print("2️⃣ CHAPTER DATABASE (chroma_db_combined_1)")
print("=" * 70)

if os.path.exists(CHAPTER_DB_PATH):
    try:
        chapter_client = chromadb.PersistentClient(path=CHAPTER_DB_PATH)
        chapter_collections = chapter_client.list_collections()
        
        print(f"\n   ✅ Connected!")
        print(f"   Collections: {len(chapter_collections)}")
        
        chapter_total = 0
        chapter_data = {}
        
        for coll in sorted(chapter_collections, key=lambda x: x.name):
            count = coll.count()
            chapter_total += count
            chapter_data[coll.name] = count
            print(f"   • {coll.name}: {count} documents")
        
        print(f"\n   📊 TOTAL in chapter DB: {chapter_total} documents")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        chapter_total = 0
else:
    print(f"   ❌ Path not found!")
    chapter_total = 0

# =============================================================================
# 3. COMPARISON
# =============================================================================

print("\n" + "=" * 70)
print("3️⃣ COMPARISON")
print("=" * 70)

print(f"""
   📊 DOCUMENT COUNT COMPARISON:
   ─────────────────────────────
   Merged DB (app uses):  {merged_total:5d} documents
   Chapter DB (original): {chapter_total:5d} documents
   ─────────────────────────────
   Difference:            {chapter_total - merged_total:5d} documents
""")

if chapter_total > merged_total:
    missing = chapter_total - merged_total
    pct_missing = (missing / chapter_total) * 100 if chapter_total > 0 else 0
    print(f"   ⚠️ WARNING: {missing} documents ({pct_missing:.1f}%) are MISSING from merged DB!")
elif merged_total > chapter_total:
    print(f"   ℹ️ Merged DB has more documents (possibly duplicates or additional data)")
else:
    print(f"   ✅ Document counts match!")

# =============================================================================
# 4. DETAILED CONTENT COMPARISON
# =============================================================================

print("\n" + "=" * 70)
print("4️⃣ KEY ENTITY SEARCH COMPARISON")
print("=" * 70)

key_entities = [
    "Secretary of State",
    "continuous supervision",
    "general direction",
    "ITAR",
    "PM/DDTC",
    "USML",
    "DSCA",
    "FAA Foreign Assistance Act",
    "AECA",
]

print("\n   Comparing entity coverage...")
print(f"\n   {'Entity':<30} {'Merged':<10} {'Chapter':<10} {'Status'}")
print("   " + "-" * 60)

for entity in key_entities:
    merged_count = 0
    chapter_count = 0
    
    # Search in merged DB
    if merged_total > 0:
        try:
            for coll in merged_collections:
                results = coll.query(query_texts=[entity], n_results=10)
                if results and results.get("documents"):
                    for doc_list in results["documents"]:
                        for doc in doc_list:
                            if entity.lower() in doc.lower():
                                merged_count += 1
        except:
            pass
    
    # Search in chapter DB
    if chapter_total > 0:
        try:
            for coll in chapter_collections:
                results = coll.query(query_texts=[entity], n_results=10)
                if results and results.get("documents"):
                    for doc_list in results["documents"]:
                        for doc in doc_list:
                            if entity.lower() in doc.lower():
                                chapter_count += 1
        except:
            pass
    
    # Status
    if merged_count == 0 and chapter_count > 0:
        status = "❌ MISSING in merged!"
    elif merged_count < chapter_count:
        status = "⚠️ Less in merged"
    elif merged_count > 0:
        status = "✅"
    else:
        status = "❓ Not found in either"
    
    print(f"   {entity:<30} {merged_count:<10} {chapter_count:<10} {status}")

# =============================================================================
# 5. SAMPLE CONTENT FROM CHAPTER DB
# =============================================================================

print("\n" + "=" * 70)
print("5️⃣ SAMPLE CONTENT FROM CHAPTER DB")
print("=" * 70)

if chapter_total > 0:
    print("\n   Showing sample from each chapter collection...")
    
    for coll in sorted(chapter_collections, key=lambda x: x.name)[:5]:
        try:
            sample = coll.get(limit=1, include=["documents", "metadatas"])
            if sample and sample.get("documents"):
                doc = sample["documents"][0][:150]
                meta = sample.get("metadatas", [{}])[0]
                print(f"\n   📄 {coll.name}:")
                print(f"      Metadata: {meta}")
                print(f"      Content: {doc}...")
        except Exception as e:
            print(f"\n   📄 {coll.name}: Error - {e}")

# =============================================================================
# 6. SUMMARY & RECOMMENDATIONS
# =============================================================================

print("\n" + "=" * 70)
print("📊 SUMMARY & RECOMMENDATIONS")
print("=" * 70)

if chapter_total > merged_total:
    print(f"""
🔴 PROBLEM IDENTIFIED:
   The merged database is MISSING {chapter_total - merged_total} documents!
   
   Merged DB:  {merged_total} docs
   Chapter DB: {chapter_total} docs (original)

🔧 SOLUTIONS:

   Option 1: RE-MERGE the databases
   ─────────────────────────────────
   Run your merge script again to combine all chapters into one collection.
   Make sure all 10 chapter folders are included.

   Option 2: USE CHAPTER DB DIRECTLY
   ─────────────────────────────────
   Update app.py to point to chroma_db_combined_1 instead:
   
   VECTOR_DB_PATH = "...\\Chromadb\\chroma_db_combined_1"
   
   And query all collections instead of just one.

   Option 3: VERIFY MERGE SCRIPT
   ─────────────────────────────────
   Check your merge script - it may have:
   - Skipped some chapters
   - Had an error during merge
   - Used wrong paths
""")
elif merged_total == 0:
    print("""
🔴 PROBLEM: Merged database is EMPTY!
   
   Please re-run your data merge script.
""")
else:
    print("""
✅ Document counts look similar.
   
   Issue may be with:
   - Search/retrieval logic
   - Embedding quality
   - Chunk size/overlap
""")

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
