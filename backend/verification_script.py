# verification_script.py
"""
SAMM Data Verification Script
Run this to understand what's actually in your database before fixing
"""

import chromadb
import os
from pathlib import Path

# Your configurations (from app.py)
VECTOR_DB_PATH = "C:\\Users\\ShaziaKashif\\ASIST Project\\Project Docs\\Input\\samm_documents\\vector_db"
VECTOR_DB_COLLECTION = "samm_all"

def verify_samm_data():
    """Complete verification of SAMM data"""
    
    print("\n" + "="*100)
    print("🔬 SAMM DATA VERIFICATION - Understanding Your Database")
    print("="*100)
    
    try:
        # Connect to Vector DB
        print("\n📡 Connecting to Vector Database...")
        client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        collection = client.get_collection(VECTOR_DB_COLLECTION)
        print("✅ Connected successfully!")
        
    except Exception as e:
        print(f"❌ ERROR: Could not connect to Vector DB")
        print(f"Error details: {e}")
        print(f"\n🔧 CHECK:")
        print(f"   1. Is this path correct? {VECTOR_DB_PATH}")
        print(f"   2. Does the collection '{VECTOR_DB_COLLECTION}' exist?")
        return None
    
    verification_results = {}
    
    # =========================================================================
    # TEST 1: DSCA Definition in C1.3.2.2
    # =========================================================================
    print("\n" + "="*100)
    print("📋 TEST 1: What does database say about DSCA in Section C1.3.2.2?")
    print("="*100)
    
    try:
        results = collection.query(
            query_texts=["DSCA Defense Security Cooperation Agency C1.3.2.2"],
            n_results=3
        )
        
        print("\n📖 DATABASE CONTENT (Top 3 results):")
        for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            section = meta.get('section_number', 'Unknown')
            chapter = meta.get('chapter_number', 'Unknown')
            print(f"\n[{i+1}] Chapter {chapter}, Section {section}:")
            print(f"    {doc[:300]}...")
            print("-" * 100)
        
        print("\n🔴 HARDCODED VERSION (From your code - Line 583 in Image 4):")
        print("C1.3.2.2 DSCA: Defense Security Cooperation Agency directs, administers,")
        print("and provides guidance to DoD Components for the execution...")
        
        # Ask user to compare
        print("\n" + "="*100)
        match = input("❓ Does the DATABASE content MATCH the HARDCODED version? (yes/no): ").strip().lower()
        verification_results['dsca_c1322_matches'] = (match == 'yes')
        
    except Exception as e:
        print(f"❌ ERROR in Test 1: {e}")
        verification_results['dsca_c1322_matches'] = False
    
    # =========================================================================
    # TEST 2: Is DSCA mentioned in Navy FMS sections?
    # =========================================================================
    print("\n" + "="*100)
    print("📋 TEST 2: Is DSCA mentioned in Navy FMS sections?")
    print("="*100)
    
    try:
        results = collection.query(
            query_texts=["Navy FMS Foreign Military Sales authority DSCA"],
            n_results=5
        )
        
        dsca_count = 0
        print("\n📖 NAVY FMS SECTIONS (Top 5 results):")
        
        for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            section = meta.get('section_number', 'Unknown')
            chapter = meta.get('chapter_number', 'Unknown')
            
            # Check if DSCA is mentioned
            has_dsca = ('DSCA' in doc.upper() or 
                       'DEFENSE SECURITY COOPERATION AGENCY' in doc.upper())
            
            if has_dsca:
                dsca_count += 1
            
            print(f"\n[{i+1}] Chapter {chapter}, Section {section}:")
            print(f"     Contains DSCA: {'✅ YES' if has_dsca else '❌ NO'}")
            print(f"     Content: {doc[:200]}...")
            print("-" * 100)
        
        verification_results['dsca_in_navy_fms'] = (dsca_count > 0)
        verification_results['dsca_navy_fms_count'] = dsca_count
        
        print(f"\n📊 SUMMARY: DSCA found in {dsca_count} out of 5 Navy FMS sections")
        
        print("\n🔴 HARDCODED ANSWER (From your code - Line 2037 in Image 2):")
        print("**Authority Holder:** Defense Security Cooperation Agency (DSCA)")
        print("**Scope of Authority:** DSCA directs, administers, and provides guidance...")
        
    except Exception as e:
        print(f"❌ ERROR in Test 2: {e}")
        verification_results['dsca_in_navy_fms'] = False
    
    # =========================================================================
    # TEST 3: Which chapters contain each entity?
    # =========================================================================
    print("\n" + "="*100)
    print("📋 TEST 3: Entity Distribution Across Chapters")
    print("="*100)
    
    entities_to_check = ["DSCA", "DFAS", "Department of State", "LOA", "FMS"]
    
    for entity in entities_to_check:
        try:
            print(f"\n🔍 Searching for: {entity}")
            
            results = collection.query(
                query_texts=[entity],
                n_results=10
            )
            
            chapters = set()
            sections = []
            
            for meta in results['metadatas'][0]:
                chapter = meta.get('chapter_number', 'Unknown')
                section = meta.get('section_number', 'Unknown')
                chapters.add(chapter)
                sections.append(section)
            
            chapters_list = sorted([c for c in chapters if c != 'Unknown'])
            
            print(f"   Found in Chapters: {chapters_list}")
            print(f"   Found in Sections: {', '.join(list(set(sections))[:5])}")
            
            verification_results[f'{entity}_chapters'] = chapters_list
            
        except Exception as e:
            print(f"   ❌ ERROR searching {entity}: {e}")
            verification_results[f'{entity}_chapters'] = []
    
    # =========================================================================
    # SUMMARY & RECOMMENDATIONS
    # =========================================================================
    print("\n" + "="*100)
    print("📊 VERIFICATION SUMMARY & FIX RECOMMENDATIONS")
    print("="*100)
    
    print("\n🔍 VERIFICATION RESULTS:")
    print(f"   1. DSCA C1.3.2.2 matches hardcoded: {verification_results.get('dsca_c1322_matches', False)}")
    print(f"   2. DSCA in Navy FMS sections: {verification_results.get('dsca_in_navy_fms', False)} ({verification_results.get('dsca_navy_fms_count', 0)} sections)")
    print(f"   3. Entity distribution recorded: ✅")
    
    print("\n🎯 FIX RECOMMENDATIONS:\n")
    
    # Recommendation 1
    if verification_results.get('dsca_c1322_matches'):
        print("✅ [1] DSCA definition in C1.3.2.2 matches")
        print("    → ACTION: Remove hardcoded static text (Line 572-590)")
        print("    → REASON: Let vector DB return this naturally")
    else:
        print("⚠️  [1] DSCA definition MISMATCH or not found")
        print("    → ACTION: Review database content vs hardcoded version")
        print("    → REASON: Need to determine which is correct")
    
    # Recommendation 2
    if verification_results.get('dsca_in_navy_fms'):
        print("\n✅ [2] DSCA IS mentioned in Navy FMS sections")
        print("    → ACTION: Remove hardcoded answer template (Line 2037-2048)")
        print("    → REASON: Let vector DB return DSCA info from actual sections")
    else:
        print("\n❌ [2] DSCA NOT mentioned in Navy FMS sections")
        print("    → ACTION: DELETE hardcoded Navy FMS answer completely")
        print("    → REASON: It's injecting false information")
    
    # Recommendation 3
    print("\n✅ [3] Entity distribution recorded")
    print("    → ACTION: Remove DSCA examples from prompts (Line 1535, 2248)")
    print("    → REASON: Don't bias entity extraction toward DSCA")
    
    # Recommendation 4
    print("\n❌ [4] ALL HARDCODED CONTENT")
    print("    → ACTION: Disable static SAMM_TEXT_CONTENT (Line 572-590)")
    print("    → REASON: Use vector DB as single source of truth")
    
    print("\n" + "="*100)
    print("✅ VERIFICATION COMPLETE!")
    print("="*100)
    
    # Save results
    import json
    output_file = "verification_results.json"
    with open(output_file, 'w') as f:
        json.dump(verification_results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    print(f"\n📤 Next steps:")
    print(f"   1. Share the console output with me")
    print(f"   2. Share the {output_file} file")
    print(f"   3. I'll give you exact fixes based on YOUR data")
    
    return verification_results

# Run the verification
if __name__ == "__main__":
    print("\n🚀 Starting SAMM Data Verification...")
    print("This will help us understand your database before applying fixes\n")
    
    results = verify_samm_data()
    
    if results:
        print("\n✨ Verification successful!")
        print("Share the output above with me for personalized fix recommendations")
    else:
        print("\n❌ Verification failed - check database connection")