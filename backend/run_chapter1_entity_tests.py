"""
Entity Extraction Test Runner for SAMM Chapter 1
=================================================

This script tests your Entity Agent against Chapter 1 ground truth entities.
It measures: Precision, Recall, F1 Score, Hallucination Rate, and Confidence.

Usage:
    python run_chapter1_entity_tests.py --url http://172.16.200.12:3000 --pattern all
    python run_chapter1_entity_tests.py --url http://172.16.200.12:3000 --pattern pattern_1_direct_acronym
    python run_chapter1_entity_tests.py --url http://172.16.200.12:3000 --start 1 --end 10
"""

import requests
import json
import argparse
import time
from datetime import datetime
from typing import Dict, List, Any, Set

# =============================================================================
# CONFIGURATION
# =============================================================================
DEFAULT_API_URL = "http://172.16.200.12:3000"
TEST_ENDPOINT = "/api/test/query"

# =============================================================================
# CHAPTER 1 TEST CASES - Organized by Pattern
# =============================================================================
TEST_CASES = {
    # Pattern 1: Direct Acronym Queries
    "pattern_1_direct_acronym": {
        "description": "Single acronym queries - tests PRECISION",
        "tests": [
            {"id": 1, "query": "What is DSCA?", "expected": ["dsca"]},
            {"id": 2, "query": "What does DFAS do?", "expected": ["dfas"]},
            {"id": 3, "query": "Define FMS", "expected": ["fms"]},
            {"id": 4, "query": "What is SC?", "expected": ["sc"]},
            {"id": 5, "query": "Explain IMET", "expected": ["imet"]},
            {"id": 6, "query": "What is USD(P)?", "expected": ["usd(p)"]},
            {"id": 7, "query": "What is DLA?", "expected": ["dla"]},
            {"id": 8, "query": "What does DCMA do?", "expected": ["dcma"]},
        ]
    },
    
    # Pattern 2: Full Name Queries
    "pattern_2_full_name": {
        "description": "Full name to acronym mapping - tests RECALL",
        "tests": [
            {"id": 9, "query": "What is Security Cooperation?", "expected": ["sc", "security cooperation"]},
            {"id": 10, "query": "Explain Security Assistance", "expected": ["sa", "security assistance"]},
            {"id": 11, "query": "What is Foreign Military Sales?", "expected": ["fms", "foreign military sales"]},
            {"id": 12, "query": "Describe Defense Security Cooperation Agency", "expected": ["dsca", "defense security cooperation agency"]},
            {"id": 13, "query": "What is the Foreign Assistance Act?", "expected": ["faa", "foreign assistance act"]},
        ]
    },
    
    # Pattern 3: Relationship Queries (more complex)
    "pattern_3_relationships": {
        "description": "Queries about entity relationships - tests RECALL & F1",
        "tests": [
            {"id": 14, "query": "Who supervises Security Assistance?", "expected": ["sa", "security assistance", "dos", "department of state"]},
            {"id": 15, "query": "What is the difference between SC and SA?", "expected": ["sc", "sa"]},
            {"id": 16, "query": "Who directs DSCA?", "expected": ["dsca", "usd(p)"]},
            {"id": 17, "query": "What role does DoS play in FMS?", "expected": ["dos", "fms", "department of state"]},
            {"id": 18, "query": "What is the relationship between DoD and State for SA?", "expected": ["dod", "dos", "sa"]},
        ]
    },
    
    # Pattern 4: Multi-Entity Queries
    "pattern_4_multi_entity": {
        "description": "Multiple entities in one query - tests RECALL",
        "tests": [
            {"id": 19, "query": "How do DSCA and DFAS work together?", "expected": ["dsca", "dfas"]},
            {"id": 20, "query": "Compare FMS and DCS", "expected": ["fms", "dcs"]},
            {"id": 21, "query": "What authorities cover SC and SA?", "expected": ["sc", "sa"]},
            {"id": 22, "query": "What do USASAC and SATFA handle?", "expected": ["usasac", "satfa"]},
            {"id": 23, "query": "Explain Title 10 and Title 22", "expected": ["title 10", "title 22"]},
        ]
    },
    
    # Pattern 5: Legal Authority Queries
    "pattern_5_legal_authorities": {
        "description": "Legal framework queries - tests accuracy on legal terms",
        "tests": [
            {"id": 24, "query": "What legal authorities govern SA?", "expected": ["sa", "faa", "aeca"]},
            {"id": 25, "query": "What is Title 10 vs Title 22?", "expected": ["title 10", "title 22"]},
            {"id": 26, "query": "Explain Executive Order 13637", "expected": ["executive order 13637", "e.o. 13637", "eo 13637"]},
            {"id": 27, "query": "What does the AECA authorize?", "expected": ["aeca"]},
            {"id": 28, "query": "How does the FAA affect IMET?", "expected": ["faa", "imet"]},
        ]
    },
    
    # Pattern 6: Role/Responsibility Queries
    "pattern_6_roles": {
        "description": "Role-based queries - tests PRECISION (avoid hallucination)",
        "tests": [
            {"id": 29, "query": "What are DSCA's responsibilities?", "expected": ["dsca"]},
            {"id": 30, "query": "What does the Secretary of State do for SA?", "expected": ["secretary of state", "secstate", "sa"]},
            {"id": 31, "query": "Who is the Implementing Agency for Army?", "expected": ["ia", "implementing agency", "da", "dasa (de&c)"]},
            {"id": 32, "query": "What role does USD(P) play?", "expected": ["usd(p)"]},
            {"id": 33, "query": "What does CJCS do for SC?", "expected": ["cjcs", "sc"]},
        ]
    },
    
    # Pattern 7: Concept Queries
    "pattern_7_concepts": {
        "description": "SAMM concept recognition - tests domain knowledge",
        "tests": [
            {"id": 34, "query": "What is continuous supervision?", "expected": ["continuous supervision"]},
            {"id": 35, "query": "Define general direction in SA context", "expected": ["general direction", "sa"]},
            {"id": 36, "query": "What are defense articles?", "expected": ["defense articles"]},
            {"id": 37, "query": "Explain Building Partner Capacity", "expected": ["bpc", "building partner capacity"]},
            {"id": 38, "query": "What is a campaign plan?", "expected": ["campaign plan"]},
        ]
    },
    
    # Pattern 8: Defense Agency Queries
    "pattern_8_defense_agencies": {
        "description": "Defense agency queries (C1.3.2.6.2)",
        "tests": [
            {"id": 39, "query": "What does DCMA do for SC?", "expected": ["dcma", "sc"]},
            {"id": 40, "query": "Explain DISA's role", "expected": ["disa"]},
            {"id": 41, "query": "What is DLA's responsibility in FMS?", "expected": ["dla", "fms"]},
            {"id": 42, "query": "How does DTRA support SC?", "expected": ["dtra", "sc"]},
            {"id": 43, "query": "What does MDA provide?", "expected": ["mda"]},
            {"id": 44, "query": "Explain NGA's SC activities", "expected": ["nga", "sc"]},
            {"id": 45, "query": "What does NSA do for foreign partners?", "expected": ["nsa"]},
        ]
    },
    
    # Pattern 9: MILDEP Queries
    "pattern_9_mildep": {
        "description": "Military Department queries (C1.3.2.6.1)",
        "tests": [
            {"id": 46, "query": "Who is the Army IA?", "expected": ["ia", "da", "dasa (de&c)"]},
            {"id": 47, "query": "What is NIPO?", "expected": ["nipo"]},
            {"id": 48, "query": "Explain SAF/IA role", "expected": ["saf/ia"]},
            {"id": 49, "query": "What does USASAC handle?", "expected": ["usasac"]},
            {"id": 50, "query": "What is AFSAC?", "expected": ["afsac"]},
        ]
    },
    
    # Pattern 10: Hallucination Tests (should return EMPTY or minimal)
    "pattern_10_hallucination_tests": {
        "description": "Test for NO hallucination - should extract MINIMAL/NO entities",
        "tests": [
            {"id": 51, "query": "What is the weather today?", "expected": []},
            {"id": 52, "query": "Tell me about programs", "expected": []},  # Generic word
            {"id": 53, "query": "What are the activities?", "expected": []},  # Generic
            {"id": 54, "query": "Hello, how are you?", "expected": []},
            {"id": 55, "query": "Explain policy", "expected": []},  # Too generic
        ]
    }
}

# =============================================================================
# HELPER: Normalize entity for comparison
# =============================================================================
def normalize_entity(entity: str) -> str:
    """Normalize entity string for comparison"""
    return entity.lower().strip()

def normalize_set(entities: List[str]) -> Set[str]:
    """Convert list to normalized set"""
    return {normalize_entity(e) for e in entities}

# =============================================================================
# METRICS CALCULATION
# =============================================================================
def calculate_metrics(extracted: List[str], expected: List[str]) -> Dict[str, float]:
    """
    Calculate entity extraction metrics
    
    Returns:
        precision: TP / (TP + FP)
        recall: TP / (TP + FN)
        f1: 2 * (P * R) / (P + R)
        hallucination_rate: FP / total_extracted
    """
    extracted_set = normalize_set(extracted)
    expected_set = normalize_set(expected)
    
    # For expected=[], any extraction is a hallucination
    if len(expected) == 0:
        if len(extracted) == 0:
            return {
                "precision": 1.0,
                "recall": 1.0,
                "f1": 1.0,
                "hallucination_rate": 0.0,
                "true_positives": 0,
                "false_positives": 0,
                "false_negatives": 0
            }
        else:
            return {
                "precision": 0.0,
                "recall": 1.0,  # No expected, so recall is N/A (set to 1.0)
                "f1": 0.0,
                "hallucination_rate": 1.0,
                "true_positives": 0,
                "false_positives": len(extracted),
                "false_negatives": 0
            }
    
    # True Positives: extracted AND expected
    tp = len(extracted_set & expected_set)
    
    # False Positives: extracted but NOT expected
    fp = len(extracted_set - expected_set)
    
    # False Negatives: expected but NOT extracted  
    fn = len(expected_set - extracted_set)
    
    # Precision
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    
    # Recall
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    
    # F1
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    # Hallucination Rate
    hallucination_rate = fp / len(extracted_set) if len(extracted_set) > 0 else 0.0
    
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "hallucination_rate": round(hallucination_rate, 4),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn
    }

# =============================================================================
# TEST RUNNER
# =============================================================================
def run_single_test(api_url: str, test_case: Dict) -> Dict:
    """Run a single test case"""
    
    endpoint = f"{api_url}{TEST_ENDPOINT}"
    
    try:
        start_time = time.time()
        response = requests.post(
            endpoint,
            json={"question": test_case["query"]},
            timeout=60
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            extracted = data.get("entities", [])
            
            # Calculate metrics
            metrics = calculate_metrics(extracted, test_case["expected"])
            
            return {
                "test_id": test_case["id"],
                "query": test_case["query"],
                "expected": test_case["expected"],
                "extracted": extracted,
                "metrics": metrics,
                "response_time": round(elapsed, 2),
                "status": "success",
                "entity_confidence": data.get("entity_confidence", 0),
                "raw_response": data
            }
        else:
            return {
                "test_id": test_case["id"],
                "query": test_case["query"],
                "status": "error",
                "error": f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        return {
            "test_id": test_case["id"],
            "query": test_case["query"],
            "status": "error",
            "error": str(e)
        }

def run_pattern_tests(api_url: str, pattern_name: str) -> Dict:
    """Run all tests for a specific pattern"""
    
    if pattern_name not in TEST_CASES:
        print(f"❌ Unknown pattern: {pattern_name}")
        return None
    
    pattern = TEST_CASES[pattern_name]
    results = []
    
    print(f"\n{'='*80}")
    print(f"Pattern: {pattern_name}")
    print(f"Description: {pattern['description']}")
    print(f"Tests: {len(pattern['tests'])}")
    print(f"{'='*80}\n")
    
    for test in pattern["tests"]:
        print(f"  Test #{test['id']}: \"{test['query']}\"")
        result = run_single_test(api_url, test)
        results.append(result)
        
        if result["status"] == "success":
            m = result["metrics"]
            print(f"    ✓ P={m['precision']:.2f} R={m['recall']:.2f} F1={m['f1']:.2f} Hall={m['hallucination_rate']:.2f}")
            print(f"    Extracted: {result['extracted']}")
            print(f"    Expected:  {result['expected']}")
        else:
            print(f"    ✗ Error: {result['error']}")
        
        time.sleep(0.5)  # Rate limiting
    
    # Calculate aggregate metrics
    successful = [r for r in results if r["status"] == "success"]
    if successful:
        avg_precision = sum(r["metrics"]["precision"] for r in successful) / len(successful)
        avg_recall = sum(r["metrics"]["recall"] for r in successful) / len(successful)
        avg_f1 = sum(r["metrics"]["f1"] for r in successful) / len(successful)
        avg_hallucination = sum(r["metrics"]["hallucination_rate"] for r in successful) / len(successful)
        
        summary = {
            "pattern": pattern_name,
            "total_tests": len(pattern["tests"]),
            "successful": len(successful),
            "failed": len(results) - len(successful),
            "avg_precision": round(avg_precision, 4),
            "avg_recall": round(avg_recall, 4),
            "avg_f1": round(avg_f1, 4),
            "avg_hallucination_rate": round(avg_hallucination, 4)
        }
        
        print(f"\n📊 Pattern Summary:")
        print(f"   Avg Precision:    {summary['avg_precision']:.2%}")
        print(f"   Avg Recall:       {summary['avg_recall']:.2%}")
        print(f"   Avg F1 Score:     {summary['avg_f1']:.2%}")
        print(f"   Avg Hallucination: {summary['avg_hallucination_rate']:.2%}")
        
        return {"results": results, "summary": summary}
    
    return {"results": results, "summary": None}

def run_all_tests(api_url: str) -> Dict:
    """Run all test patterns"""
    
    all_results = {}
    all_summaries = []
    
    for pattern_name in TEST_CASES.keys():
        result = run_pattern_tests(api_url, pattern_name)
        all_results[pattern_name] = result
        if result and result["summary"]:
            all_summaries.append(result["summary"])
    
    # Overall summary
    if all_summaries:
        print(f"\n{'='*80}")
        print("OVERALL CHAPTER 1 ENTITY EXTRACTION METRICS")
        print(f"{'='*80}")
        
        total_tests = sum(s["total_tests"] for s in all_summaries)
        total_successful = sum(s["successful"] for s in all_summaries)
        
        overall_precision = sum(s["avg_precision"] * s["successful"] for s in all_summaries) / total_successful
        overall_recall = sum(s["avg_recall"] * s["successful"] for s in all_summaries) / total_successful
        overall_f1 = sum(s["avg_f1"] * s["successful"] for s in all_summaries) / total_successful
        overall_hallucination = sum(s["avg_hallucination_rate"] * s["successful"] for s in all_summaries) / total_successful
        
        print(f"\n📊 Overall Results ({total_successful}/{total_tests} tests passed):")
        print(f"   PRECISION:         {overall_precision:.2%} (Target: ≥90%)")
        print(f"   RECALL:            {overall_recall:.2%} (Target: ≥85%)")
        print(f"   F1 SCORE:          {overall_f1:.2%} (Target: ≥90%)")
        print(f"   HALLUCINATION RATE: {overall_hallucination:.2%} (Target: ≤5%)")
        
        # Pass/Fail status
        print(f"\n✅ Metric Status:")
        print(f"   Precision:    {'PASS ✓' if overall_precision >= 0.90 else 'FAIL ✗'}")
        print(f"   Recall:       {'PASS ✓' if overall_recall >= 0.85 else 'FAIL ✗'}")
        print(f"   F1 Score:     {'PASS ✓' if overall_f1 >= 0.90 else 'FAIL ✗'}")
        print(f"   Hallucination: {'PASS ✓' if overall_hallucination <= 0.05 else 'FAIL ✗'}")
    
    return all_results

# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chapter 1 Entity Extraction Test Runner")
    parser.add_argument("--url", default=DEFAULT_API_URL, help="API base URL")
    parser.add_argument("--pattern", default="all", help="Pattern to test (or 'all')")
    parser.add_argument("--start", type=int, help="Start test ID")
    parser.add_argument("--end", type=int, help="End test ID")
    parser.add_argument("--output", default="chapter1_test_results.json", help="Output file")
    
    args = parser.parse_args()
    
    print(f"🚀 SAMM Chapter 1 Entity Extraction Test Runner")
    print(f"   API: {args.url}")
    print(f"   Pattern: {args.pattern}")
    print(f"   Time: {datetime.now().isoformat()}")
    
    if args.pattern == "all":
        results = run_all_tests(args.url)
    else:
        results = run_pattern_tests(args.url, args.pattern)
    
    # Save results
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved to {args.output}")
