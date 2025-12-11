import chromadb
from pprint import pprint

client = chromadb.PersistentClient(path=r"C:\Users\ShaziaKashif\ASIST Project\ontology_converter\vector_db")
col = client.get_collection("samm_all")

# fetch only a few Chapter 9 entries
data = col.get(where={"section_id": {"$contains": "C9."}}, limit=5, include=["metadatas", "documents"])

print("=== Found:", len(data['ids']), "Chapter 9 entries ===")
for i, meta in enumerate(data["metadatas"], start=1):
    print(f"\n--- Metadata {i} ---")
    pprint(meta)
