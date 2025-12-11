"""
ChromaDB Individual vs Combined Comparison
==========================================
Yeh script:
1. Individual chapter DBs check karegi
2. Combined DB check karegi  
3. Compare karegi ke sab chunks merge huay ya nahi

Usage: python check_individual_chapters.py
"""

import chromadb
import os
import sys
from collections import defaultdict

# ============================================
# CONFIGURATION - Apne paths yahan set karein
# ============================================

# Base Chromadb folder
CHROMADB_BASE = r"C:\Users\ShaziaKashif\ASIST Project\ASIST2.1\ASIST_V2.1\backend\Chromadb"

# Individual chapter DB paths (adjust as needed)
INDIVIDUAL_DBS = {
    "Chapter 1": os.path.join(CHROMADB_BASE, "chroma_db_ch1"),
    "Chapter 4": os.path.join(CHROMADB_BASE, "chroma_db_ch4"),
    "Chapter 5": os.path.join(CHROMADB_BASE, "chroma_db_ch5"),
    "Chapter 6": os.path.join(CHROMADB_BASE, "chroma_db_ch6"),
    "Chapter 7": os.path.join(CHROMADB_BASE, "chroma_db_ch7"),
    "Chapter 9": os.path.join(CHROMADB_BASE, "chroma_db_ch9"),
}

# Combined DB path
COMBINED_DB = os.path.join(CHROMADB_BASE, "chroma_db_combined")
COMBINED_DB_1 = os.path.join(CHROMADB_BASE, "chroma_db_combined_1")


def get_db_stats(db_path: str) -> dict:
    """Get detailed stats from a ChromaDB"""
    stats = {
        "exists": False,
        "collections": [],
        "total_chunks": 0,
        "chapter_counts": defaultdict(int),
        "metadata_keys": set(),
        "sample_ids": [],
        "error": None
    }
    
    if not os.path.exists(db_path):
        stats["error"] = "Path does not exist"
        return stats
    
    stats["exists"] = True
    
    try:
        client = chromadb.PersistentClient(path=db_path)
        collections = client.list_collections()
        
        for coll_info in collections:
            coll = client.get_collection(coll_info.name)
            count = coll.count()
            
            stats["collections"].append({
                "name": coll_info.name,
                "count": count
            })
            stats["total_chunks"] += count
            
            # Get all data to analyze
            if count > 0:
                all_data = coll.get(include=["metadatas"])
                
                # Store sample IDs for comparison
                stats["sample_ids"].extend(all_data['ids'][:10])
                
                for metadata in all_data['metadatas']:
                    if metadata:
                        stats["metadata_keys"].update(metadata.keys())
                        
                        # Count by chapter
                        chapter = metadata.get('chapter', metadata.get('Chapter', 'Unknown'))
                        stats["chapter_counts"][str(chapter)] += 1
        
        stats["metadata_keys"] = list(stats["metadata_keys"])
        
    except Exception as e:
        stats["error"] = str(e)
    
    return stats


def print_db_report(name: str, stats: dict):
    """Print formatted report for a DB"""
    print(f"\n{'='*60}")
    print(f"📁 {name}")
    print(f"{'='*60}")
    
    if stats["error"]:
        print(f"   ❌ Error: {stats['error']}")
        return
    
    if not stats["exists"]:
        print(f"   ⚠️  Path does not exist")
        return
    
    print(f"   📚 Collections: {len(stats['collections'])}")
    for coll in stats["collections"]:
        print(f"      • {coll['name']}: {coll['count']} chunks")
    
    print(f"\n   📊 Total Chunks: {stats['total_chunks']}")
    
    if stats["chapter_counts"]:
        print(f"\n   📑 Chapter Breakdown:")
        for ch in sorted(stats["chapter_counts"].keys()):
            print(f"      • {ch}: {stats['chapter_counts'][ch]} chunks")
    
    if stats["metadata_keys"]:
        print(f"\n   🏷️  Metadata Keys: {stats['metadata_keys']}")


def main():
    print("\n" + "#"*70)
    print("🔍 ChromaDB INDIVIDUAL vs COMBINED Comparison")
    print("#"*70)
    
    # First, list what's in the Chromadb folder
    print(f"\n📂 Scanning: {CHROMADB_BASE}")
    print("-"*60)
    
    if os.path.exists(CHROMADB_BASE):
        items = os.listdir(CHROMADB_BASE)
        print("Found folders/files:")
        for item in sorted(items):
            item_path = os.path.join(CHROMADB_BASE, item)
            if os.path.isdir(item_path):
                # Check if it looks like a ChromaDB
                has_sqlite = os.path.exists(os.path.join(item_path, "chroma.sqlite3"))
                db_marker = "✅ ChromaDB" if has_sqlite else "📁 Folder"
                print(f"   {db_marker}: {item}")
            else:
                print(f"   📄 File: {item}")
    else:
        print(f"❌ Base path not found: {CHROMADB_BASE}")
        print("\n⚠️  Please update CHROMADB_BASE in this script!")
        return
    
    # Collect all stats
    all_stats = {}
    individual_total = 0
    
    # Check individual DBs
    print("\n" + "="*70)
    print("📖 INDIVIDUAL CHAPTER DATABASES")
    print("="*70)
    
    for name, path in INDIVIDUAL_DBS.items():
        stats = get_db_stats(path)
        all_stats[name] = stats
        if stats["exists"] and not stats["error"]:
            individual_total += stats["total_chunks"]
        print_db_report(name, stats)
    
    # Check combined DBs
    print("\n" + "="*70)
    print("📚 COMBINED DATABASES")
    print("="*70)
    
    combined_stats = get_db_stats(COMBINED_DB)
    all_stats["Combined (chroma_db_combined)"] = combined_stats
    print_db_report("Combined (chroma_db_combined)", combined_stats)
    
    combined1_stats = get_db_stats(COMBINED_DB_1)
    all_stats["Combined_1 (chroma_db_combined_1)"] = combined1_stats
    print_db_report("Combined_1 (chroma_db_combined_1)", combined1_stats)
    
    # COMPARISON SUMMARY
    print("\n" + "#"*70)
    print("📊 COMPARISON SUMMARY")
    print("#"*70)
    
    print(f"\n{'Database':<40} {'Chunks':<15} {'Status'}")
    print("-"*70)
    
    for name, stats in all_stats.items():
        if stats["exists"] and not stats["error"]:
            chunks = stats["total_chunks"]
            status = "✅" if chunks > 0 else "⚠️ Empty"
        elif stats["error"]:
            chunks = "-"
            status = f"❌ {stats['error'][:20]}"
        else:
            chunks = "-"
            status = "⚠️ Not found"
        
        print(f"{name:<40} {str(chunks):<15} {status}")
    
    # Calculate expected vs actual
    print("\n" + "-"*70)
    print(f"📈 Individual chapters total: {individual_total} chunks")
    
    if combined_stats["exists"] and not combined_stats["error"]:
        combined_total = combined_stats["total_chunks"]
        print(f"📈 Combined DB total: {combined_total} chunks")
        
        diff = individual_total - combined_total
        if diff > 0:
            print(f"\n⚠️  MISSING: {diff} chunks not in combined DB!")
        elif diff < 0:
            print(f"\n🔍 Combined has {abs(diff)} MORE chunks than individual sum")
        else:
            print(f"\n✅ MATCH: All chunks accounted for!")
    
    if combined1_stats["exists"] and not combined1_stats["error"]:
        combined1_total = combined1_stats["total_chunks"]
        print(f"📈 Combined_1 DB total: {combined1_total} chunks")
        
        diff = individual_total - combined1_total
        if diff > 0:
            print(f"\n⚠️  MISSING in Combined_1: {diff} chunks!")
        elif diff < 0:
            print(f"\n🔍 Combined_1 has {abs(diff)} MORE chunks than individual sum")
    
    # Chapter-wise comparison
    print("\n" + "-"*70)
    print("📑 Chapter-wise in Combined DB:")
    
    if combined_stats["exists"] and combined_stats["chapter_counts"]:
        for ch in sorted(combined_stats["chapter_counts"].keys()):
            print(f"   • {ch}: {combined_stats['chapter_counts'][ch]} chunks")
    
    print("\n" + "#"*70)
    print("✅ Analysis Complete!")
    print("#"*70)
    print("\n💡 TIP: Agar individual DBs nahi mil rahay, to paths update karein script mein")
    print("   INDIVIDUAL_DBS dictionary mein apne actual paths add karein\n")


if __name__ == "__main__":
    main()
