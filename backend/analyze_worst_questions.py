"""
SAMM Metrics - Root Cause Analysis Tool
========================================
Detailed analysis of worst performing questions

Analyzes:
1. What the question asks
2. What ground truth expects
3. What system returned
4. Why metrics failed
5. Root cause identification
"""

import requests
import json
import time
from datetime import datetime

API_URL = "http://127.0.0.1:3000/api/test/query"

# =============================================================================
# WORST PERFORMING QUESTIONS WITH GROUND TRUTH
# =============================================================================

ANALYSIS_QUESTIONS = {
    "Q15": {
        "question": "What does the Secretary of State approve regarding SA?",
        "ground_truth": {
            "expected_answer": """The Secretary of State (SECSTATE) is responsible for:
1. Continuous supervision and general direction of SA programs
2. Determining whether and when there will be a program for a country
3. Determining program scope (what types of articles, training, services)
4. Making country eligibility determinations
5. Approving individual FMS cases above certain thresholds

Legal Basis: Foreign Assistance Act (FAA), Arms Export Control Act (AECA), 
Executive Order 13637""",
            "expected_entities": ["Secretary of State", "SECSTATE", "SA", "Security Assistance"],
            "expected_citations": ["C1.2", "C1.3.1", "C1.3.2.1"],
            "expected_intent": "authority",
            "key_facts": [
                "continuous supervision",
                "general direction", 
                "program scope",
                "country eligibility",
                "FAA",
                "AECA",
                "EO 13637"
            ]
        },
        "test_result": {
            "completeness": 25.0,
            "groundedness": 11.11,
            "citation_accuracy": 0.0,
            "quality_score": 78.0
        }
    },
    
    "Q11": {
        "question": "What is ITAR and who manages it?",
        "ground_truth": {
            "expected_answer": """ITAR (International Traffic in Arms Regulations) is:
- The set of regulations that control the export and import of defense articles 
  and services on the United States Munitions List (USML)
- Implements the Arms Export Control Act (AECA)

Manager/Administrator:
- Directorate of Defense Trade Controls (PM/DDTC)
- Part of the Department of State (DOS)
- Also known as PM/DDTC within State Department

The USML designates which items are controlled under ITAR.""",
            "expected_entities": ["ITAR", "International Traffic in Arms Regulations", 
                                  "PM/DDTC", "DDTC", "Department of State", "USML"],
            "expected_citations": ["C1.2", "C1.3.2.3"],
            "expected_intent": "definition",  # or "compliance"
            "key_facts": [
                "International Traffic in Arms Regulations",
                "defense articles",
                "USML",
                "United States Munitions List",
                "PM/DDTC",
                "Directorate of Defense Trade Controls",
                "Department of State",
                "AECA"
            ]
        },
        "test_result": {
            "completeness": 33.33,
            "groundedness": 22.22,
            "citation_accuracy": 60.0,
            "quality_score": 75.5
        }
    }
}

# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

def call_api(question: str) -> dict:
    """Call the test API endpoint"""
    try:
        response = requests.post(
            API_URL,
            json={"question": question},
            timeout=200
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def analyze_completeness(answer: str, key_facts: list) -> dict:
    """Analyze which key facts are present/missing"""
    answer_lower = answer.lower()
    
    found = []
    missing = []
    
    for fact in key_facts:
        if fact.lower() in answer_lower:
            found.append(fact)
        else:
            missing.append(fact)
    
    return {
        "found": found,
        "missing": missing,
        "found_count": len(found),
        "total_count": len(key_facts),
        "percentage": round(len(found) / len(key_facts) * 100, 1) if key_facts else 0
    }

def analyze_groundedness(answer: str, expected: str) -> dict:
    """Analyze how well answer is grounded in expected content"""
    answer_words = set(answer.lower().split())
    expected_words = set(expected.lower().split())
    
    # Remove common words
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                  'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                  'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                  'of', 'to', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                  'and', 'or', 'but', 'if', 'then', 'than', 'that', 'this'}
    
    answer_words = answer_words - stop_words
    expected_words = expected_words - stop_words
    
    overlap = answer_words.intersection(expected_words)
    
    return {
        "overlap_words": list(overlap)[:20],
        "answer_unique": list(answer_words - expected_words)[:10],
        "expected_missing": list(expected_words - answer_words)[:10],
        "overlap_percentage": round(len(overlap) / len(expected_words) * 100, 1) if expected_words else 0
    }

def analyze_citations(citations: list, expected: list) -> dict:
    """Analyze citation accuracy"""
    citations_normalized = [c.upper().replace(" ", "") for c in citations]
    expected_normalized = [c.upper().replace(" ", "") for c in expected]
    
    matched = []
    extra = []
    missing = []
    
    for c in citations_normalized:
        if any(e in c or c in e for e in expected_normalized):
            matched.append(c)
        else:
            extra.append(c)
    
    for e in expected_normalized:
        if not any(e in c or c in e for c in citations_normalized):
            missing.append(e)
    
    return {
        "matched": matched,
        "extra_citations": extra,
        "missing_citations": missing,
        "accuracy": round(len(matched) / len(expected) * 100, 1) if expected else 0
    }

def identify_root_causes(analysis: dict) -> list:
    """Identify root causes of failure"""
    root_causes = []
    
    # Check completeness issues
    if analysis["completeness"]["percentage"] < 50:
        missing = analysis["completeness"]["missing"]
        if len(missing) > 3:
            root_causes.append({
                "category": "COMPLETENESS",
                "severity": "HIGH",
                "issue": f"Missing {len(missing)} key facts",
                "details": f"Missing: {', '.join(missing[:5])}...",
                "fix": "Vector DB may not have relevant chunks OR answer generation prompt needs adjustment"
            })
    
    # Check groundedness issues
    if analysis["groundedness"]["overlap_percentage"] < 40:
        root_causes.append({
            "category": "GROUNDEDNESS", 
            "severity": "HIGH",
            "issue": "Answer not well grounded in expected content",
            "details": f"Only {analysis['groundedness']['overlap_percentage']}% word overlap",
            "fix": "Model may be hallucinating OR expected answer format differs from model output"
        })
    
    # Check citation issues
    if analysis["citations"]["accuracy"] < 50:
        if len(analysis["citations"]["missing_citations"]) > 0:
            root_causes.append({
                "category": "CITATION",
                "severity": "MEDIUM",
                "issue": "Missing expected citations",
                "details": f"Missing: {analysis['citations']['missing_citations']}",
                "fix": "Citation extraction logic may need adjustment OR Vector DB chunks missing metadata"
            })
    
    # Check entity extraction
    if "entities" in analysis and analysis["entities"]["missing"]:
        root_causes.append({
            "category": "ENTITY",
            "severity": "MEDIUM", 
            "issue": "Missing expected entities",
            "details": f"Missing: {analysis['entities']['missing']}",
            "fix": "Entity extraction patterns may need expansion"
        })
    
    # Check intent
    if "intent" in analysis and not analysis["intent"]["correct"]:
        root_causes.append({
            "category": "INTENT",
            "severity": "HIGH",
            "issue": f"Wrong intent detected: {analysis['intent']['detected']} vs expected {analysis['intent']['expected']}",
            "details": "Intent classification affected answer generation",
            "fix": "Add pattern for this question type OR adjust intent keywords"
        })
    
    return root_causes

# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def run_detailed_analysis():
    """Run detailed analysis on worst performing questions"""
    
    print("=" * 80)
    print("SAMM METRICS - ROOT CAUSE ANALYSIS")
    print("Analyzing Worst Performing Questions")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    for q_id, q_data in ANALYSIS_QUESTIONS.items():
        print(f"\n{'='*80}")
        print(f"  📋 ANALYZING {q_id}")
        print(f"{'='*80}")
        
        question = q_data["question"]
        ground_truth = q_data["ground_truth"]
        test_result = q_data["test_result"]
        
        print(f"\n📝 QUESTION: {question}")
        print(f"\n📊 PREVIOUS TEST SCORES:")
        print(f"   Completeness:  {test_result['completeness']:.1f}%")
        print(f"   Groundedness:  {test_result['groundedness']:.1f}%")
        print(f"   Citation:      {test_result['citation_accuracy']:.1f}%")
        print(f"   Quality:       {test_result['quality_score']:.1f}%")
        
        # Call API
        print(f"\n🔄 Calling API...")
        start_time = time.time()
        response = call_api(question)
        elapsed = time.time() - start_time
        print(f"   Response time: {elapsed:.2f}s")
        
        if "error" in response:
            print(f"   ❌ ERROR: {response['error']}")
            continue
        
        # Extract response data
        answer = response.get("answer", "")
        entities = response.get("entities", [])
        intent = response.get("intent", "unknown")
        intent_conf = response.get("intent_confidence", 0)
        citations = response.get("citations", [])
        
        print(f"\n📤 SYSTEM RESPONSE:")
        print(f"   Intent: {intent} (conf: {intent_conf:.2f})")
        print(f"   Entities: {entities}")
        print(f"   Citations: {citations}")
        print(f"\n   Answer ({len(answer)} chars):")
        print(f"   {'-'*60}")
        # Print answer with indentation
        for line in answer[:800].split('\n'):
            print(f"   {line}")
        if len(answer) > 800:
            print(f"   ... [truncated, {len(answer)-800} more chars]")
        print(f"   {'-'*60}")
        
        print(f"\n📋 EXPECTED (Ground Truth):")
        print(f"   Intent: {ground_truth['expected_intent']}")
        print(f"   Entities: {ground_truth['expected_entities']}")
        print(f"   Citations: {ground_truth['expected_citations']}")
        print(f"   Key Facts: {ground_truth['key_facts']}")
        
        # Run analysis
        print(f"\n🔍 DETAILED ANALYSIS:")
        
        # 1. Completeness Analysis
        completeness = analyze_completeness(answer, ground_truth["key_facts"])
        print(f"\n   1️⃣ COMPLETENESS ANALYSIS:")
        print(f"      Found {completeness['found_count']}/{completeness['total_count']} key facts ({completeness['percentage']}%)")
        print(f"      ✅ Found: {completeness['found']}")
        print(f"      ❌ Missing: {completeness['missing']}")
        
        # 2. Groundedness Analysis
        groundedness = analyze_groundedness(answer, ground_truth["expected_answer"])
        print(f"\n   2️⃣ GROUNDEDNESS ANALYSIS:")
        print(f"      Word overlap: {groundedness['overlap_percentage']}%")
        print(f"      Common words: {groundedness['overlap_words'][:10]}")
        print(f"      Answer has extra: {groundedness['answer_unique'][:5]}")
        print(f"      Expected missing: {groundedness['expected_missing'][:5]}")
        
        # 3. Citation Analysis
        citation_analysis = analyze_citations(citations, ground_truth["expected_citations"])
        print(f"\n   3️⃣ CITATION ANALYSIS:")
        print(f"      Accuracy: {citation_analysis['accuracy']}%")
        print(f"      ✅ Matched: {citation_analysis['matched']}")
        print(f"      ❌ Missing: {citation_analysis['missing_citations']}")
        print(f"      ➕ Extra: {citation_analysis['extra_citations']}")
        
        # 4. Intent Analysis
        intent_correct = intent.lower() == ground_truth["expected_intent"].lower()
        print(f"\n   4️⃣ INTENT ANALYSIS:")
        print(f"      Expected: {ground_truth['expected_intent']}")
        print(f"      Detected: {intent}")
        print(f"      Status: {'✅ CORRECT' if intent_correct else '❌ WRONG'}")
        
        # 5. Entity Analysis
        expected_entities_lower = [e.lower() for e in ground_truth["expected_entities"]]
        found_entities = [e for e in entities if e.lower() in expected_entities_lower]
        missing_entities = [e for e in ground_truth["expected_entities"] 
                          if e.lower() not in [x.lower() for x in entities]]
        
        print(f"\n   5️⃣ ENTITY ANALYSIS:")
        print(f"      Expected: {ground_truth['expected_entities']}")
        print(f"      Found: {entities}")
        print(f"      ✅ Matched: {found_entities}")
        print(f"      ❌ Missing: {missing_entities}")
        
        # Compile analysis
        analysis = {
            "completeness": completeness,
            "groundedness": groundedness,
            "citations": citation_analysis,
            "intent": {
                "expected": ground_truth["expected_intent"],
                "detected": intent,
                "correct": intent_correct
            },
            "entities": {
                "found": found_entities,
                "missing": missing_entities
            }
        }
        
        # Identify root causes
        root_causes = identify_root_causes(analysis)
        
        print(f"\n{'='*60}")
        print(f"   🔴 ROOT CAUSES IDENTIFIED:")
        print(f"{'='*60}")
        
        if not root_causes:
            print(f"   ✅ No major root causes found - metrics calculation may be too strict")
        else:
            for i, cause in enumerate(root_causes, 1):
                print(f"\n   [{cause['severity']}] {cause['category']}:")
                print(f"   Issue: {cause['issue']}")
                print(f"   Details: {cause['details']}")
                print(f"   Fix: {cause['fix']}")
        
        results[q_id] = {
            "question": question,
            "response": response,
            "analysis": analysis,
            "root_causes": root_causes
        }
    
    # Summary
    print(f"\n\n{'='*80}")
    print("📊 SUMMARY - ROOT CAUSES ACROSS ALL QUESTIONS")
    print("="*80)
    
    all_causes = []
    for q_id, data in results.items():
        for cause in data["root_causes"]:
            cause["question"] = q_id
            all_causes.append(cause)
    
    # Group by category
    by_category = {}
    for cause in all_causes:
        cat = cause["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(cause)
    
    print("\nIssues by Category:")
    for cat, causes in sorted(by_category.items()):
        print(f"\n  {cat}: {len(causes)} issues")
        for c in causes:
            print(f"    - [{c['severity']}] {c['question']}: {c['issue']}")
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    
    return results


if __name__ == "__main__":
    run_detailed_analysis()
