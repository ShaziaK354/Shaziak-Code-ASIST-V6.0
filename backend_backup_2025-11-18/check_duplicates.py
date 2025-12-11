"""
Vector DB Duplicate Checker (Read-Only - Safe)
Only checks and reports duplicates, does NOT modify database
"""

import chromadb
import hashlib

# ============================================================================
# CONFIGURATION
# ============================================================================

VECTOR_DB_COLLECTION = "samm_all"  # Your collection name
CHROMA_PERSIST_DIR = "./samm_documents/vector_db" 

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def check_duplicates():
    """Check for duplicate documents in vector DB"""
    
    print("\n" + "="*80)
    print("🔍 VECTOR DB DUPLICATE CHECK (READ-ONLY)")
    print("="*80 + "\n")
    
    try:
        # Connect to ChromaDB
        print("📂 Connecting to ChromaDB...")
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        print(f"✅ Connected to: {CHROMA_PERSIST_DIR}\n")
        
        # Get collection
        collection = client.get_collection(VECTOR_DB_COLLECTION)
        print(f"📊 Collection: {VECTOR_DB_COLLECTION}")
        
        # Get all documents
        print("📥 Fetching all documents...")
        all_docs = collection.get()
        total_docs = len(all_docs['documents'])
        print(f"✅ Loaded {total_docs} documents\n")
        
        print("="*80)
        print("🔍 ANALYZING FOR DUPLICATES...")
        print("="*80 + "\n")
        
        # Find duplicates
        seen = {}
        duplicates = []
        duplicate_details = []
        
        for idx, (doc_id, doc, meta) in enumerate(zip(
            all_docs['ids'],
            all_docs['documents'],
            all_docs['metadatas']
        )):
            # Create hash of document content
            doc_hash = hashlib.md5(doc.encode()).hexdigest()
            
            if doc_hash in seen:
                # Found duplicate!
                original_idx = seen[doc_hash]
                original_meta = all_docs['metadatas'][original_idx]
                
                duplicate_info = {
                    'duplicate_index': idx,
                    'duplicate_id': doc_id,
                    'duplicate_section': meta.get('section_number', 'Unknown'),
                    'duplicate_chapter': meta.get('chapter_number', 'Unknown'),
                    'original_index': original_idx,
                    'original_id': all_docs['ids'][original_idx],
                    'original_section': original_meta.get('section_number', 'Unknown'),
                    'content_preview': doc[:100]
                }
                
                duplicates.append(duplicate_info)
                duplicate_details.append(doc_hash)
            else:
                seen[doc_hash] = idx
        
        # Display results
        print("="*80)
        print("📊 RESULTS")
        print("="*80 + "\n")
        
        print(f"📌 Total documents in database: {total_docs}")
        print(f"✅ Unique documents: {len(seen)}")
        print(f"❌ Duplicate documents: {len(duplicates)}")
        
        if total_docs > 0:
            duplicate_percentage = (len(duplicates) / total_docs) * 100
            print(f"📈 Duplicate percentage: {duplicate_percentage:.1f}%")
        
        print()
        
        # Show duplicate details
        if len(duplicates) > 0:
            print("="*80)
            print("❌ DUPLICATE DETAILS (First 20)")
            print("="*80 + "\n")
            
            for i, dup in enumerate(duplicates[:20], 1):
                print(f"Duplicate #{i}:")
                print(f"  📍 Location: Index {dup['duplicate_index']}")
                print(f"  📄 Section: {dup['duplicate_section']}")
                print(f"  📚 Chapter: {dup['duplicate_chapter']}")
                print(f"  🔗 Duplicate of: Index {dup['original_index']} (Section {dup['original_section']})")
                print(f"  📝 Preview: {dup['content_preview']}...")
                print()
            
            if len(duplicates) > 20:
                print(f"... and {len(duplicates) - 20} more duplicates\n")
            
            # Group by section
            print("="*80)
            print("📊 DUPLICATES BY SECTION")
            print("="*80 + "\n")
            
            section_counts = {}
            for dup in duplicates:
                section = dup['duplicate_section']
                section_counts[section] = section_counts.get(section, 0) + 1
            
            sorted_sections = sorted(section_counts.items(), key=lambda x: x[1], reverse=True)
            
            print(f"Sections with duplicates: {len(sorted_sections)}\n")
            print("Top 10 sections with most duplicates:")
            for section, count in sorted_sections[:10]:
                print(f"  {section}: {count} duplicates")
            
            print()
            
        else:
            print("="*80)
            print("✅ NO DUPLICATES FOUND!")
            print("="*80)
            print("\nYour database is clean! 🎉\n")
        
        # Summary and recommendation
        print("="*80)
        print("💡 RECOMMENDATION")
        print("="*80 + "\n")
        
        if len(duplicates) == 0:
            print("✅ No action needed - database is already clean!")
        elif duplicate_percentage < 10:
            print("⚠️  Low duplicate rate (<10%)")
            print("   → Optional: Run remove_duplicates.py to clean")
            print("   → Or just increase n_results in query_vector_db()")
        elif duplicate_percentage < 30:
            print("⚠️  Moderate duplicate rate (10-30%)")
            print("   → Recommended: Run remove_duplicates.py to clean")
        else:
            print("🚨 High duplicate rate (>30%)")
            print("   → STRONGLY RECOMMENDED: Run remove_duplicates.py")
            print("   → This will significantly improve performance!")
        
        print()
        print("="*80 + "\n")
        
        return duplicates
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return []


if __name__ == '__main__':
    duplicates = check_duplicates()
    
    print("="*80)
    print("🏁 CHECK COMPLETE")
    print("="*80)
    
    if len(duplicates) > 0:
        print(f"\n📝 Next step: Run 'python remove_duplicates.py' to clean database")
    
    print()