"""
VECTOR DB DATA QUALITY DIAGNOSTIC
==================================
Analyzes Vector DB to find:
1. Total document/chunk count
2. Chapter distribution
3. Missing topics/entities
4. Search quality for problem questions

Run this to identify data merge issues.
"""

import os
import json
from collections import Counter, defaultdict
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

# Key topics that SHOULD be in Vector DB
EXPECTED_TOPICS = {
    "chapter_1": {
        "name": "Security Cooperation Overview",
        "key_entities": [
            "Security Cooperation", "SC",
            "Security Assistance", "SA", 
            "Secretary of State", "SECSTATE",
            "Secretary of Defense", "SECDEF",
            "DSCA", "Defense Security Cooperation Agency",
            "DFAS", "Defense Finance and Accounting Service",
            "USD(P)", "Under Secretary of Defense for Policy",
            "FAA", "Foreign Assistance Act",
            "AECA", "Arms Export Control Act",
            "ITAR", "International Traffic in Arms Regulations",
            "USML", "United States Munitions List",
            "PM/DDTC", "Directorate of Defense Trade Controls",
            "EO 13637", "Executive Order 13637",
            "Title 10", "Title 22",
        ],
        "key_phrases": [
            "continuous supervision",
            "general direction",
            "program scope",
            "country eligibility",
            "defense articles",
            "military education and training",
        ]
    }
}

# Problem queries to test
TEST_QUERIES = [
    {
        "query": "Secretary of State SA approval authority",
        "expected_content": ["continuous supervision", "general direction", "program scope"],
        "expected_citations": ["C1.2", "C1.3.1", "C1.3.2.1"]
    },
    {
        "query": "ITAR International Traffic in Arms Regulations",
        "expected_content": ["USML", "defense articles", "PM/DDTC", "Department of State"],
        "expected_citations": ["C1.2", "C1.3.2.3"]
    },
    {
        "query": "DSCA role Security Cooperation",
        "expected_content": ["directs", "administers", "guidance", "DoD Components"],
        "expected_citations": ["C1.3.2.2"]
    }
]

# =============================================================================
# AZURE SEARCH CLIENT
# =============================================================================

def get_search_client():
    """Initialize Azure Cognitive Search client"""
    try:
        from azure.search.documents import SearchClient
        from azure.core.credentials import AzureKeyCredential
        
        endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        key = os.getenv("AZURE_SEARCH_KEY") 
        index = os.getenv("AZURE_SEARCH_INDEX", "samm-index")
        
        if not endpoint or not key:
            print("❌ Missing AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_KEY in .env")
            return None
        
        client = SearchClient(
            endpoint=endpoint,
            index_name=index,
            credential=AzureKeyCredential(key)
        )
        return client
    except ImportError:
        print("❌ Azure SDK not installed. Run: pip install azure-search-documents")
        return None
    except Exception as e:
        print(f"❌ Error connecting to Azure Search: {e}")
        return None

# =============================================================================
# DIAGNOSTIC FUNCTIONS
# =============================================================================

def get_total_document_count(client) -> int:
    """Get total number of documents in index"""
    try:
        results = client.search(search_text="*", top=0, include_total_count=True)
        return results.get_count()
    except Exception as e:
        print(f"Error getting count: {e}")
        return -1

def get_all_documents_sample(client, sample_size=500) -> list:
    """Get a sample of documents to analyze"""
    try:
        results = client.search(search_text="*", top=sample_size)
        return list(results)
    except Exception as e:
        print(f"Error getting documents: {e}")
        return []

def analyze_chapter_distribution(documents: list) -> dict:
    """Analyze which chapters are represented"""
    chapter_counts = Counter()
    section_counts = Counter()
    
    for doc in documents:
        # Try different field names for chapter info
        chapter = (doc.get("chapter") or 
                   doc.get("metadata", {}).get("chapter") or
                   doc.get("chapter_num") or
                   "Unknown")
        
        section = (doc.get("section") or
                   doc.get("metadata", {}).get("section") or
                   doc.get("section_id") or
                   "Unknown")
        
        chapter_counts[str(chapter)] += 1
        section_counts[str(section)] += 1
    
    return {
        "chapters": dict(chapter_counts),
        "sections": dict(section_counts),
        "total_analyzed": len(documents)
    }

def search_for_topic(client, query: str, top: int = 10) -> list:
    """Search for a specific topic"""
    try:
        results = client.search(search_text=query, top=top)
        return list(results)
    except Exception as e:
        print(f"Error searching for '{query}': {e}")
        return []

def analyze_search_results(results: list, expected_content: list) -> dict:
    """Analyze if search results contain expected content"""
    found_content = []
    missing_content = []
    
    # Combine all result text
    all_text = ""
    for r in results:
        content = r.get("content") or r.get("chunk") or r.get("text") or ""
        all_text += " " + content.lower()
    
    for expected in expected_content:
        if expected.lower() in all_text:
            found_content.append(expected)
        else:
            missing_content.append(expected)
    
    return {
        "found": found_content,
        "missing": missing_content,
        "coverage": len(found_content) / len(expected_content) * 100 if expected_content else 0
    }

def check_specific_entity(client, entity: str) -> dict:
    """Check if a specific entity exists in the index"""
    results = search_for_topic(client, entity, top=5)
    
    if not results:
        return {"exists": False, "count": 0, "samples": []}
    
    samples = []
    for r in results[:3]:
        content = r.get("content") or r.get("chunk") or r.get("text") or ""
        samples.append(content[:200] + "..." if len(content) > 200 else content)
    
    return {
        "exists": True,
        "count": len(results),
        "samples": samples
    }

def get_document_fields(documents: list) -> list:
    """Get all field names present in documents"""
    fields = set()
    for doc in documents[:10]:  # Sample first 10
        fields.update(doc.keys())
    return list(fields)

# =============================================================================
# MAIN DIAGNOSTIC
# =============================================================================

def run_diagnostic():
    """Run full Vector DB diagnostic"""
    
    print("=" * 80)
    print("VECTOR DB DATA QUALITY DIAGNOSTIC")
    print("=" * 80)
    
    # Connect to Azure Search
    print("\n📡 Connecting to Azure Search...")
    client = get_search_client()
    
    if not client:
        print("\n⚠️ Cannot connect to Azure Search.")
        print("Please check your .env file has:")
        print("  AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net")
        print("  AZURE_SEARCH_KEY=your-api-key")
        print("  AZURE_SEARCH_INDEX=samm-index")
        return
    
    print("✅ Connected!")
    
    # 1. Total Document Count
    print("\n" + "=" * 60)
    print("1️⃣ DOCUMENT COUNT")
    print("=" * 60)
    
    total_count = get_total_document_count(client)
    print(f"\n   Total documents in index: {total_count}")
    
    if total_count < 100:
        print("   ⚠️ WARNING: Very few documents! Expected 500+ for full SAMM")
    elif total_count < 300:
        print("   ⚠️ WARNING: Fewer documents than expected. Some chapters may be missing.")
    else:
        print("   ✅ Document count looks reasonable")
    
    # 2. Get Sample Documents
    print("\n" + "=" * 60)
    print("2️⃣ DOCUMENT STRUCTURE")
    print("=" * 60)
    
    sample_docs = get_all_documents_sample(client, 200)
    
    if sample_docs:
        fields = get_document_fields(sample_docs)
        print(f"\n   Available fields: {fields}")
        
        # Show sample document
        print(f"\n   Sample document structure:")
        sample = sample_docs[0]
        for key, value in sample.items():
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            print(f"     {key}: {value}")
    
    # 3. Chapter Distribution
    print("\n" + "=" * 60)
    print("3️⃣ CHAPTER DISTRIBUTION")
    print("=" * 60)
    
    distribution = analyze_chapter_distribution(sample_docs)
    
    print(f"\n   Chapters found (from {distribution['total_analyzed']} docs):")
    for chapter, count in sorted(distribution["chapters"].items()):
        pct = count / distribution['total_analyzed'] * 100
        bar = "█" * int(pct / 5)
        print(f"     Chapter {chapter}: {count:3d} docs ({pct:5.1f}%) {bar}")
    
    # Check for missing chapters
    expected_chapters = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
    found_chapters = set(distribution["chapters"].keys())
    
    # Normalize chapter names for comparison
    found_normalized = set()
    for ch in found_chapters:
        # Extract number from chapter string
        import re
        nums = re.findall(r'\d+', str(ch))
        if nums:
            found_normalized.add(nums[0])
    
    missing_chapters = set(expected_chapters) - found_normalized
    if missing_chapters:
        print(f"\n   ⚠️ Potentially missing chapters: {sorted(missing_chapters)}")
    
    # 4. Key Entity Search
    print("\n" + "=" * 60)
    print("4️⃣ KEY ENTITY COVERAGE")
    print("=" * 60)
    
    key_entities = [
        "Secretary of State",
        "SECSTATE",
        "continuous supervision",
        "general direction",
        "DSCA",
        "DFAS",
        "ITAR",
        "PM/DDTC",
        "USML",
        "EO 13637",
        "FAA Foreign Assistance Act",
        "AECA Arms Export Control Act",
    ]
    
    print("\n   Checking key entities...")
    entity_results = {}
    
    for entity in key_entities:
        result = check_specific_entity(client, entity)
        status = "✅" if result["exists"] else "❌"
        print(f"   {status} '{entity}': {result['count']} results")
        entity_results[entity] = result
    
    # 5. Problem Query Analysis
    print("\n" + "=" * 60)
    print("5️⃣ PROBLEM QUERY ANALYSIS")
    print("=" * 60)
    
    for i, test in enumerate(TEST_QUERIES, 1):
        print(f"\n   Query {i}: '{test['query']}'")
        print(f"   Expected citations: {test['expected_citations']}")
        
        results = search_for_topic(client, test["query"], top=10)
        print(f"   Results found: {len(results)}")
        
        if results:
            analysis = analyze_search_results(results, test["expected_content"])
            print(f"   Content coverage: {analysis['coverage']:.1f}%")
            print(f"   ✅ Found: {analysis['found']}")
            print(f"   ❌ Missing: {analysis['missing']}")
            
            # Show top result preview
            top_result = results[0]
            content = top_result.get("content") or top_result.get("chunk") or ""
            chapter = top_result.get("chapter") or top_result.get("metadata", {}).get("chapter") or "?"
            print(f"\n   Top result (Chapter {chapter}):")
            print(f"   {content[:300]}...")
        else:
            print("   ❌ NO RESULTS FOUND!")
    
    # 6. Summary
    print("\n" + "=" * 80)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 80)
    
    issues = []
    
    if total_count < 200:
        issues.append(f"LOW DOCUMENT COUNT: Only {total_count} documents (expected 500+)")
    
    missing_entities = [e for e, r in entity_results.items() if not r["exists"]]
    if missing_entities:
        issues.append(f"MISSING ENTITIES: {missing_entities}")
    
    if "Unknown" in distribution["chapters"] and distribution["chapters"]["Unknown"] > 50:
        issues.append(f"CHAPTER METADATA ISSUE: {distribution['chapters']['Unknown']} docs have unknown chapter")
    
    if issues:
        print("\n🔴 ISSUES FOUND:")
        for issue in issues:
            print(f"   • {issue}")
        
        print("\n🔧 RECOMMENDED ACTIONS:")
        print("   1. Re-check the data merge process")
        print("   2. Verify all SAMM chapters were included")
        print("   3. Check if chunk metadata (chapter, section) is preserved")
        print("   4. Consider re-indexing with proper metadata")
    else:
        print("\n✅ No major issues found!")
        print("   The Vector DB appears to have good coverage.")
        print("   Issue may be with retrieval logic or answer generation.")
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)
    
    return {
        "total_count": total_count,
        "distribution": distribution,
        "entity_results": entity_results,
        "issues": issues
    }


if __name__ == "__main__":
    run_diagnostic()
