"""
CHROMADB MERGED DB ANALYSIS
============================
Analyzes what's actually IN the merged database (196 docs)
"""

import os
import sys
from collections import Counter

print("=" * 70)
print("CHROMADB MERGED DB ANALYSIS")
print("=" * 70)

# =============================================================================
# PATH
# =============================================================================

MERGED_DB_PATH = r"C:\Users\ShaziaKashif\ASIST Project\ASIST2.1\ASIST_V2.1\backend\Chromadb\chroma_db_combined"
COLLECTION_NAME = "samm_all_chapters"

if not os.path.exists(MERGED_DB_PATH):
    MERGED_DB_PATH = "./Chromadb/chroma_db_combined"

print(f"\n📂 Path: {MERGED_DB_PATH}")

# =============================================================================
# CONNECT
# =============================================================================

try:
    import chromadb
except ImportError:
    print("❌ ChromaDB not installed")
    sys.exit(1)

try:
    client = chromadb.PersistentClient(path=MERGED_DB_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)
    total_count = collection.count()
    print(f"✅ Connected! Total documents: {total_count}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# =============================================================================
# GET ALL DOCUMENTS
# =============================================================================

print("\n" + "=" * 70)
print("1️⃣ FETCHING ALL DOCUMENTS")
print("=" * 70)

all_docs = collection.get(
    limit=total_count,
    include=["documents", "metadatas"]
)

documents = all_docs.get("documents", [])
metadatas = all_docs.get("metadatas", [])

print(f"\n   Retrieved {len(documents)} documents")

# =============================================================================
# ANALYZE METADATA
# =============================================================================

print("\n" + "=" * 70)
print("2️⃣ METADATA ANALYSIS")
print("=" * 70)

# Check what metadata fields exist
all_keys = set()
for meta in metadatas:
    if meta:
        all_keys.update(meta.keys())

print(f"\n   Metadata fields available: {list(all_keys)}")

# Count by different metadata fields
chapters = Counter()
sources = Counter()
sections = Counter()

for meta in metadatas:
    if meta:
        # Try different chapter field names
        ch = meta.get("chapter") or meta.get("Chapter") or meta.get("chapter_num") or "Unknown"
        chapters[str(ch)] += 1
        
        src = meta.get("source") or meta.get("Source") or meta.get("filename") or "Unknown"
        # Truncate long source names
        sources[str(src)[:50]] += 1
        
        sec = meta.get("section") or meta.get("Section") or "Unknown"
        sections[str(sec)[:30]] += 1
    else:
        chapters["No Metadata"] += 1

print(f"\n   📊 Chapter Distribution:")
for ch, cnt in sorted(chapters.items(), key=lambda x: -x[1]):
    pct = cnt / len(documents) * 100
    bar = "█" * int(pct / 3)
    print(f"      {ch}: {cnt} docs ({pct:.1f}%) {bar}")

print(f"\n   📊 Source Distribution (top 10):")
for src, cnt in sources.most_common(10):
    print(f"      {src}: {cnt} docs")

# =============================================================================
# CONTENT ANALYSIS
# =============================================================================

print("\n" + "=" * 70)
print("3️⃣ CONTENT ANALYSIS")
print("=" * 70)

# Combine all content for analysis
all_content = " ".join(documents).lower()
total_chars = len(all_content)

print(f"\n   Total content: {total_chars:,} characters")
print(f"   Average per doc: {total_chars // len(documents):,} characters")

# Check for key entities in ALL content
key_entities = [
    ("Secretary of State", "Q15 - Authority"),
    ("SECSTATE", "Q15 - Authority"),
    ("continuous supervision", "Q15 - Key phrase"),
    ("general direction", "Q15 - Key phrase"),
    ("program scope", "Q15 - Key phrase"),
    ("DSCA", "General"),
    ("DFAS", "General"),
    ("ITAR", "Q11 - Compliance"),
    ("PM/DDTC", "Q11 - Manager"),
    ("DDTC", "Q11 - Manager"),
    ("USML", "Q11 - Related"),
    ("United States Munitions List", "Q11 - Related"),
    ("FAA", "Legal Authority"),
    ("Foreign Assistance Act", "Legal Authority"),
    ("AECA", "Legal Authority"),
    ("Arms Export Control Act", "Legal Authority"),
    ("EO 13637", "Legal Authority"),
    ("Executive Order 13637", "Legal Authority"),
    ("Title 10", "Funding"),
    ("Title 22", "Funding"),
]

print(f"\n   📊 Key Entity Presence in ALL Content:")
print(f"   {'Entity':<35} {'Found':<8} {'Relevance'}")
print("   " + "-" * 60)

found_entities = []
missing_entities = []

for entity, relevance in key_entities:
    count = all_content.count(entity.lower())
    status = "✅" if count > 0 else "❌"
    print(f"   {entity:<35} {status} {count:<5} {relevance}")
    
    if count > 0:
        found_entities.append(entity)
    else:
        missing_entities.append((entity, relevance))

# =============================================================================
# SAMPLE DOCUMENTS WITH SECRETARY OF STATE
# =============================================================================

print("\n" + "=" * 70)
print("4️⃣ SEARCHING FOR 'Secretary of State' CONTENT")
print("=" * 70)

sos_docs = []
for i, (doc, meta) in enumerate(zip(documents, metadatas)):
    if "secretary of state" in doc.lower():
        sos_docs.append((i, doc, meta))

print(f"\n   Found {len(sos_docs)} documents mentioning 'Secretary of State'")

if sos_docs:
    print("\n   Sample content:")
    for idx, doc, meta in sos_docs[:3]:
        print(f"\n   Doc {idx}:")
        print(f"   Metadata: {meta}")
        print(f"   Content: {doc[:300]}...")
else:
    print("\n   ❌ NO documents contain 'Secretary of State'!")
    print("   This explains why Q15 fails!")

# =============================================================================
# SEARCHING FOR ITAR CONTENT
# =============================================================================

print("\n" + "=" * 70)
print("5️⃣ SEARCHING FOR 'ITAR' CONTENT")
print("=" * 70)

itar_docs = []
for i, (doc, meta) in enumerate(zip(documents, metadatas)):
    if "itar" in doc.lower():
        itar_docs.append((i, doc, meta))

print(f"\n   Found {len(itar_docs)} documents mentioning 'ITAR'")

if itar_docs:
    print("\n   Sample content:")
    for idx, doc, meta in itar_docs[:3]:
        print(f"\n   Doc {idx}:")
        print(f"   Metadata: {meta}")
        print(f"   Content: {doc[:300]}...")
else:
    print("\n   ❌ NO documents contain 'ITAR'!")
    print("   This explains why Q11 has issues!")

# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "=" * 70)
print("📊 SUMMARY")
print("=" * 70)

print(f"""
📈 DATABASE STATS:
   Total Documents: {total_count}
   Chapters Found: {len([c for c in chapters if c not in ['Unknown', 'No Metadata']])}
   Total Characters: {total_chars:,}

🔍 ENTITY COVERAGE:
   ✅ Found: {len(found_entities)} entities
   ❌ Missing: {len(missing_entities)} entities
""")

if missing_entities:
    print("   Missing entities:")
    for entity, relevance in missing_entities[:10]:
        print(f"      • {entity} ({relevance})")

print(f"""
🔴 ROOT CAUSE ANALYSIS:
""")

if len(sos_docs) == 0:
    print("   1. 'Secretary of State' content is MISSING from database!")
    print("      → Q15 cannot find relevant information")

if len(itar_docs) == 0:
    print("   2. 'ITAR' content is MISSING from database!")
    print("      → Q11 cannot find relevant information")

if total_count < 300:
    print(f"   3. Only {total_count} documents - likely incomplete data merge!")
    print("      → Expected 500+ docs for full SAMM coverage")

print(f"""
🔧 SOLUTION:
   The merged database is INCOMPLETE.
   Need to re-merge all chapter data OR use original chapter databases.
   
   Check: How was chroma_db_combined created?
   Missing: Secretary of State, ITAR, and other key content
""")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
