import chromadb

#path = r"C:\Users\ShaziaKashif\ASIST Project\ASIST2.1\ASIST_V2.1\backend\Chromadb\chroma_db_combined"
path = r"C:\Users\ShaziaKashif\ASIST Project\ASIST2.1\ASIST_V2.1\backend\Chromadb\chroma_db_combined_1"

client = chromadb.PersistentClient(path=path)
collections = client.list_collections()

print(f"Total Collections: {len(collections)}")
print("-" * 60)

for col in collections:
    print(f"\nCollection: {col.name}")
    print(f"  Documents: {col.count()}")
    
    # Sample dekho
    if col.count() > 0:
        sample = col.peek(limit=1)
        if sample['documents']:
            print(f"  Sample: {sample['documents'][0][:150]}...")