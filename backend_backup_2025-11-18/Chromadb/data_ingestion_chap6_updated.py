import chromadb
import json
import os

# Fresh ChromaDB with PersistentClient
client = chromadb.PersistentClient(path="./chroma_db")

# Load data
with open('chunks_chromadb_chap6_updated.json', 'r') as f:
    data = json.load(f)

# Delete old collection if exists
try:
    client.delete_collection("samm_chapter6")
except:
    pass

# Create collection
collection = client.create_collection("samm_chapter6")

# Add chunks
collection.add(
    documents=data["documents"],
    metadatas=data["metadatas"],
    ids=data["ids"]
)

print(f"✅ ChromaDB created successfully!")
print(f"✅ Total chunks: {collection.count()}")
print(f"✅ Location: {os.path.abspath('./chroma_db')}")

# List created files
print(f"\n📁 Files in chroma_db:")
for item in os.listdir('./chroma_db'):
    print(f"  - {item}")

# Test query
print(f"\n🔍 Test query:")
results = collection.get(where={"section_id": "C6.1"})
print(f"✅ Query successful: {results['metadatas'][0]['section_title']}")
