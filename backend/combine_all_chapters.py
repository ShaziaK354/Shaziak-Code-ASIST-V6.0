"""
Combine All Chapters into samm_all_chapters (Separate Folder)
"""

import chromadb
import sys
import os

# Source: Individual chapters
SOURCE_DB = r"C:\Users\ShaziaKashif\ASIST Project\ASIST2.1\ASIST_V2.1\backend\Chromadb\new_chromadb"

# Destination: Clean folder with ONLY samm_all_chapters (for GitHub)
DEST_DB = r"C:\Users\ShaziaKashif\ASIST Project\ASIST2.1\ASIST_V2.1\backend\Chromadb\samm_all_chapters_db"

FINAL_COLLECTION = "samm_all_chapters"

print("\n" + "="*60)
print("🔗 Combining All Chapters into samm_all_chapters")
print("="*60)

print(f"\n📂 Source: {SOURCE_DB}")
print(f"📂 Destination: {DEST_DB}")

# Load embedding model
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("✅ Embedding model loaded")
except:
    print("❌ SentenceTransformers required")
    sys.exit(1)

# Connect to source ChromaDB
source_client = chromadb.PersistentClient(path=SOURCE_DB)

# List all chapter collections
chapter_collections = ["chapter_1", "chapter_4", "chapter_5", "chapter_6", "chapter_7", "chapter_9"]

print(f"\n📚 Source collections:")
all_data = []

for coll_name in chapter_collections:
    try:
        coll = source_client.get_collection(coll_name)
        count = coll.count()
        print(f"   • {coll_name}: {count} chunks")
        
        # Get all data from this collection
        data = coll.get(include=["documents", "metadatas"])
        
        for i in range(len(data['ids'])):
            all_data.append({
                'id': data['ids'][i],
                'document': data['documents'][i],
                'metadata': data['metadatas'][i]
            })
    except Exception as e:
        print(f"   ⚠️ {coll_name}: {e}")

print(f"\n📊 Total chunks to combine: {len(all_data)}")

# Create destination folder
os.makedirs(DEST_DB, exist_ok=True)
print(f"\n📁 Created destination folder")

# Connect to destination ChromaDB
dest_client = chromadb.PersistentClient(path=DEST_DB)

# Delete existing combined collection if exists
try:
    dest_client.delete_collection(FINAL_COLLECTION)
    print(f"🗑️ Deleted old '{FINAL_COLLECTION}'")
except:
    pass

# Create new combined collection
combined = dest_client.create_collection(
    name=FINAL_COLLECTION,
    metadata={"description": "SAMM All Chapters Combined - Chapters 1, 4, 5, 6, 7, 9"}
)

# Prepare data
ids = [d['id'] for d in all_data]
docs = [d['document'] for d in all_data]
metas = [d['metadata'] for d in all_data]

# Generate embeddings
print(f"\n🔄 Generating embeddings for {len(docs)} chunks...")
print("   (This may take 1-2 minutes)")

batch_size = 100
embeddings = []

for i in range(0, len(docs), batch_size):
    batch = docs[i:i+batch_size]
    batch_emb = model.encode(batch, show_progress_bar=False).tolist()
    embeddings.extend(batch_emb)
    print(f"   Processed {min(i+batch_size, len(docs))}/{len(docs)}")

# Add to combined collection
print(f"\n💾 Saving to '{FINAL_COLLECTION}'...")

# Add in batches
for i in range(0, len(ids), batch_size):
    end = min(i + batch_size, len(ids))
    combined.add(
        ids=ids[i:end],
        documents=docs[i:end],
        metadatas=metas[i:end],
        embeddings=embeddings[i:end]
    )

# Verify
final_count = combined.count()

print("\n" + "="*60)
print("✅ SUCCESS!")
print("="*60)

print(f"\n📊 Final Collection: {FINAL_COLLECTION}")
print(f"   Total chunks: {final_count}")

# Chapter breakdown
print(f"\n📚 Chunks by chapter:")
chapter_counts = {}
all_metas = combined.get(include=["metadatas"])
for meta in all_metas['metadatas']:
    ch = meta.get('chapter', 'unknown')
    chapter_counts[ch] = chapter_counts.get(ch, 0) + 1

for ch in sorted(chapter_counts.keys()):
    print(f"   • Chapter {ch}: {chapter_counts[ch]} chunks")

# Test query
print(f"\n🧪 Test: 'What is Security Cooperation?'")
results = combined.query(query_texts=["What is Security Cooperation?"], n_results=3)
for i, meta in enumerate(results['metadatas'][0]):
    print(f"   {i+1}. Ch{meta.get('chapter')} - {meta['section_id']}: {meta['section_title'][:35]}...")

# Show folder structure
print(f"\n📁 Folder Structure:")
print(f"   Chromadb/")
print(f"   ├── new_chromadb/          (individual chapters - keep for reference)")
print(f"   │   ├── chapter_1")
print(f"   │   ├── chapter_4")
print(f"   │   ├── chapter_5")
print(f"   │   ├── chapter_6")
print(f"   │   ├── chapter_7")
print(f"   │   └── chapter_9")
print(f"   │")
print(f"   └── samm_all_chapters_db/  ⬅️ UPLOAD THIS TO GITHUB")
print(f"       └── samm_all_chapters ({final_count} chunks)")

print(f"\n💡 Update your app:")
print(f'   VECTOR_DB_PATH = r"{DEST_DB}"')
print(f'   VECTOR_DB_COLLECTION = "{FINAL_COLLECTION}"')
