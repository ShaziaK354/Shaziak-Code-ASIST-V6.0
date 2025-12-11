import chromadb
import json
import os
from pathlib import Path

# Fresh ChromaDB with PersistentClient
client = chromadb.PersistentClient(path="./chroma_db_combined")

print("=" * 60)
print("🚀 SAMM COMBINED DATABASE CREATOR")
print("=" * 60)

# Define all chapter files
chapter_files = {
    "Chapter 1": "chunks_chromadb_chap1.json",
    "Chapter 4": "chunks_chromadb_chap4_updated.json", 
    "Chapter 5": "chunks_chromadb_chap5_updated.json",
    "Chapter 6": "chunks_chromadb_chap6_updated.json",
    "Chapter 7": "chunks_chromadb_chap7.json",
    "Chapter 9": "chunks_chromadb_chap9.json"
}

# Delete old collection if exists
try:
    client.delete_collection("samm_all_chapters")
    print("✅ Old collection deleted")
except:
    print("ℹ️  No old collection found")

# Create new combined collection
collection = client.create_collection("samm_all_chapters")
print("✅ New collection 'samm_all_chapters' created\n")

# Track statistics
total_chunks = 0
chapter_stats = {}

# Load and combine all chapters
for chapter_name, filename in chapter_files.items():
    try:
        # Try to load file
        if os.path.exists(filename):
            filepath = filename
        else:
            print(f"⚠️  {chapter_name} file not found: {filename}")
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Add chunks to collection
        num_chunks = len(data["documents"])
        collection.add(
            documents=data["documents"],
            metadatas=data["metadatas"],
            ids=data["ids"]
        )
        
        # Update statistics
        chapter_stats[chapter_name] = num_chunks
        total_chunks += num_chunks
        
        print(f"✅ {chapter_name}: {num_chunks} chunks added")
        
    except FileNotFoundError:
        print(f"⚠️  {chapter_name} file not found: {filename}")
    except Exception as e:
        print(f"❌ Error loading {chapter_name}: {str(e)}")

print("\n" + "=" * 60)
print("📊 FINAL STATISTICS")
print("=" * 60)

for chapter, count in chapter_stats.items():
    print(f"  {chapter}: {count} chunks")

print(f"\n✅ Total chunks in combined database: {total_chunks}")
print(f"✅ Database location: {os.path.abspath('./chroma_db_combined')}")

# List created files
print(f"\n📁 Files in chroma_db_combined:")
for item in os.listdir('./chroma_db_combined'):
    print(f"  - {item}")

# Test queries for each chapter
print("\n" + "=" * 60)
print("🔍 TESTING DATABASE")
print("=" * 60)

test_queries = [
    {"chapter": 1, "section_id": "C1.1.1"},
    {"chapter": 4, "section_id": "C4.1.1"},
    {"chapter": 5, "section_id": "C5.1.1"},
    {"chapter": 6, "section_id": "C6.1"},
    {"chapter": 7, "section_id": "C7.1.1"},
    {"chapter": 9, "section_id": "C9.1.1"}
]

for query in test_queries:
    try:
        results = collection.get(where={"section_id": query["section_id"]})
        if results['metadatas']:
            print(f"✅ Chapter {query['chapter']}: {results['metadatas'][0]['section_title']}")
        else:
            print(f"⚠️  Chapter {query['chapter']}: No data found")
    except Exception as e:
        print(f"⚠️  Chapter {query['chapter']}: {str(e)}")

print("\n" + "=" * 60)
print("✅ COMBINED DATABASE READY!")
print("=" * 60)
print(f"\nYou can now query all {total_chunks} chunks from {len(chapter_stats)} chapters")
print("Collection name: 'samm_all_chapters'")
print("Database path: ./chroma_db_combined")
