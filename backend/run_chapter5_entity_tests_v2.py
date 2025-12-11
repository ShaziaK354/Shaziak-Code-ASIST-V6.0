"""
Entity Extraction Test Runner for SAMM Chapter 5 - CORRECTED v2
================================================================

FIXES:
1. Acronym expansions are NOT hallucinations
2. Expected entities only include what's in the query
3. Proper handling of hierarchical acronyms (IOPS/GEX/CWD → IOPS, IOPS/GEX, etc.)

Usage:
    python run_chapter5_entity_tests_v2.py --url http://127.0.0.1:3000 --pattern all
    python run_chapter5_entity_tests_v2.py --url http://127.0.0.1:3000 --pattern pattern_c5_1_lor
"""

import requests
import json
import argparse
import time
from datetime import datetime
from typing import Dict, List, Any, Set

# Import CORRECTED Chapter 5 test cases
from chapter5_entity_implementation_v2 import (
    TEST_CASES_CHAPTER_5,
    CHAPTER_5_GROUND_TRUTH,
    CHAPTER_5_ACRONYM_PAIRS,
    VALID_EXPANSIONS,
    get_all_chapter5_tests,
    get_chapter5_ground_truth_entities
)

# =============================================================================
# CONFIGURATION
# =============================================================================
DEFAULT_API_URL = "http://127.0.0.1:3000"
TEST_ENDPOINT = "/api/test/query"

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
# VALID EXPANSION CHECK
# =============================================================================
def is_valid_expansion(entity: str, query: str) -> bool:
    """
    Check if an extracted entity is a valid expansion of an acronym in the query.
    If so, it's NOT a hallucination.
    """
    entity_lower = entity.lower()
    query_lower = query.lower()
    
    # Check against known valid expansions
    for acronym, expansion in VALID_EXPANSIONS.items():
        if acronym.lower() in query_lower:
            if entity_lower == expansion.lower():
                return True
    
    # Check against acronym pairs (bidirectional)
    for acronym, fullform in CHAPTER_5_ACRONYM_PAIRS.items():
        # If acronym is in query, its expansion is valid
        if acronym.lower() in query_lower:
            if entity_lower == fullform.lower():
                return True
        # If fullform is in query, its acronym is valid
        if fullform.lower() in query_lower:
            if entity_lower == acronym.lower():
                return True
    
    # Check for hierarchical acronym expansions (IOPS/GEX/CWD → IOPS, IOPS/GEX)
    hierarchical_acronyms = {
        "iops/gex/cwd": ["iops", "iops/gex", "international operations", 
                        "international operations global execution directorate",
                        "case writing and development division"],
        "iops/gex": ["iops", "international operations",
                    "international operations global execution directorate"],
        "obo/fpre/frc": ["obo", "obo/fpre", "office of business operations",
                        "financial policy and regional execution directorate",
                        "financial reporting and compliance division"],
        "obo/fpre": ["obo", "office of business operations",
                    "financial policy and regional execution directorate"],
        "iops/wpn": ["iops", "international operations", "weapons directorate"],
        "iops/wpns": ["iops", "international operations", "weapons directorate"],
        "iops/rex": ["iops", "international operations", "regional execution directorate"],
    }
    
    for parent, children in hierarchical_acronyms.items():
        if parent in query_lower:
            if entity_lower in children:
                return True
    
    return False

def is_in_query(entity: str, query: str) -> bool:
    """Check if entity appears in the query"""
    return entity.lower() in query.lower()

# =============================================================================
# METRICS CALCULATION - CORRECTED
# =============================================================================
def calculate_metrics(extracted: List[str], expected: List[str], query: str) -> Dict[str, float]:
    """
    Calculate precision, recall, F1, and hallucination rate
    
    KEY FIXES:
    1. Expansions of query acronyms are NOT hallucinations
    2. Only entities NOT in query AND NOT valid expansions are hallucinations
    """
    extracted_set = normalize_set(extracted)
    expected_set = normalize_set(expected)
    
    # Get all ground truth entities
    ground_truth = get_chapter5_ground_truth_entities()
    ground_truth_normalized = {e.lower() for e in ground_truth}
    
    # Also add all valid expansions to ground truth
    for acronym, expansion in VALID_EXPANSIONS.items():
        ground_truth_normalized.add(acronym.lower())
        ground_truth_normalized.add(expansion.lower())
    for acronym, expansion in CHAPTER_5_ACRONYM_PAIRS.items():
        ground_truth_normalized.add(acronym.lower())
        ground_truth_normalized.add(expansion.lower())
    
    # True positives: correctly extracted
    true_positives = extracted_set & expected_set
    
    # False positives: extracted but not expected (but may be valid expansions)
    false_positives = extracted_set - expected_set
    
    # False negatives: expected but not extracted
    false_negatives = expected_set - extracted_set
    
    # HALLUCINATIONS: Must meet ALL criteria:
    # 1. Not in expected set
    # 2. Not a valid expansion of something in the query
    # 3. Not in ground truth
    hallucinations = set()
    for entity in extracted_set:
        if entity in expected_set:
            continue  # It's expected, not hallucination
        if is_valid_expansion(entity, query):
            continue  # It's a valid expansion, not hallucination
        if is_in_query(entity, query):
            continue  # It's literally in the query, not hallucination
        if entity not in ground_truth_normalized:
            hallucinations.add(entity)
    
    tp = len(true_positives)
    fp = len(false_positives)
    fn = len(false_negatives)
    total_extracted = len(extracted_set) if extracted_set else 1
    
    # Calculate metrics
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    hallucination_rate = len(hallucinations) / total_extracted if total_extracted > 0 else 0.0
    
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "hallucination_rate": round(hallucination_rate, 4),
        "true_positives": list(true_positives),
        "false_positives": list(false_positives),
        "false_negatives": list(false_negatives),
        "hallucinations": list(hallucinations)
    }

# =============================================================================
# TEST RUNNER
# =============================================================================
def run_single_test(api_url: str, test_case: Dict) -> Dict:
    """Run a single test case against the API"""
    endpoint = f"{api_url}{TEST_ENDPOINT}"
    
    payload = {
        "query": test_case["query"],
        "testMode": True,
        "returnEntitiesOnly": True
    }
    
    try:
        response = requests.post(endpoint, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            extracted = data.get("entities", [])
            
            # Calculate metrics with query for expansion checking
            metrics = calculate_metrics(
                extracted, 
                test_case["expected"],
                test_case["query"]
            )
            
            return {
                "test_id": test_case["id"],
                "query": test_case["query"],
                "extracted": extracted,
                "expected": test_case["expected"],
                "metrics": metrics,
                "status": "success"
            }
        else:
            return {
                "test_id": test_case["id"],
                "query": test_case["query"],
                "status": "error",
                "error": f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            "test_id": test_case["id"],
            "query": test_case["query"],
            "status": "error",
            "error": str(e)
        }

def run_pattern_tests(api_url: str, pattern_name: str) -> List[Dict]:
    """Run all tests for a specific pattern"""
    if pattern_name not in TEST_CASES_CHAPTER_5:
        print(f"❌ Pattern not found: {pattern_name}")
        return []
    
    pattern = TEST_CASES_CHAPTER_5[pattern_name]
    results = []
    
    print(f"\n{'='*80}")
    print(f"Pattern: {pattern_name}")
    print(f"Description: {pattern['description']}")
    print(f"Tests: {len(pattern['tests'])}")
    print(f"{'='*80}\n")
    
    for test in pattern["tests"]:
        result = run_single_test(api_url, test)
        results.append(result)
        
        # Print result
        if result["status"] == "success":
            m = result["metrics"]
            status = "✓" if m["f1"] >= 0.9 else "○"
            print(f"  Test #{result['test_id']}: \"{result['query']}\"")
            print(f"    {status} P={m['precision']:.2f} R={m['recall']:.2f} F1={m['f1']:.2f} Hall={m['hallucination_rate']:.2f}")
            print(f"    Extracted: {result['extracted']}")
            print(f"    Expected:  {result['expected']}")
            
            if m["false_negatives"]:
                print(f"    ⚠️  Missing: {m['false_negatives']}")
            if m["hallucinations"]:
                print(f"    ⚠️  Hallucinated: {m['hallucinations']}")
        else:
            print(f"  Test #{result['test_id']}: ❌ {result.get('error', 'Unknown error')}")
        
        time.sleep(0.5)  # Rate limiting
    
    # Pattern summary
    successful = [r for r in results if r["status"] == "success"]
    if successful:
        avg_p = sum(r["metrics"]["precision"] for r in successful) / len(successful)
        avg_r = sum(r["metrics"]["recall"] for r in successful) / len(successful)
        avg_f1 = sum(r["metrics"]["f1"] for r in successful) / len(successful)
        avg_hall = sum(r["metrics"]["hallucination_rate"] for r in successful) / len(successful)
        
        print(f"\n📊 Pattern Summary:")
        print(f"   Avg Precision:    {avg_p*100:.2f}% {'✓' if avg_p >= 0.9 else '✗'}")
        print(f"   Avg Recall:       {avg_r*100:.2f}% {'✓' if avg_r >= 0.85 else '✗'}")
        print(f"   Avg F1 Score:     {avg_f1*100:.2f}% {'✓' if avg_f1 >= 0.9 else '✗'}")
        print(f"   Avg Hallucination: {avg_hall*100:.2f}% {'✓' if avg_hall <= 0.05 else '✗'}")
    
    return results

def run_all_tests(api_url: str) -> Dict:
    """Run all Chapter 5 tests"""
    all_results = []
    
    for pattern_name in TEST_CASES_CHAPTER_5:
        results = run_pattern_tests(api_url, pattern_name)
        all_results.extend(results)
    
    return calculate_overall_metrics(all_results)

def calculate_overall_metrics(results: List[Dict]) -> Dict:
    """Calculate overall metrics from all test results"""
    successful = [r for r in results if r["status"] == "success"]
    
    if not successful:
        return {"error": "No successful tests"}
    
    total_precision = sum(r["metrics"]["precision"] for r in successful)
    total_recall = sum(r["metrics"]["recall"] for r in successful)
    total_f1 = sum(r["metrics"]["f1"] for r in successful)
    total_hall = sum(r["metrics"]["hallucination_rate"] for r in successful)
    count = len(successful)
    
    overall = {
        "total_tests": len(results),
        "successful_tests": count,
        "avg_precision": round(total_precision / count, 4),
        "avg_recall": round(total_recall / count, 4),
        "avg_f1": round(total_f1 / count, 4),
        "avg_hallucination_rate": round(total_hall / count, 4),
        "results": results
    }
    
    # Print overall summary
    print(f"\n{'='*80}")
    print("OVERALL CHAPTER 5 ENTITY EXTRACTION METRICS")
    print(f"{'='*80}")
    print(f"\n📊 Overall Results ({count}/{len(results)} tests passed):")
    print(f"   PRECISION:         {overall['avg_precision']*100:.2f}% (Target: ≥90%)")
    print(f"   RECALL:            {overall['avg_recall']*100:.2f}% (Target: ≥85%)")
    print(f"   F1 SCORE:          {overall['avg_f1']*100:.2f}% (Target: ≥90%)")
    print(f"   HALLUCINATION RATE: {overall['avg_hallucination_rate']*100:.2f}% (Target: ≤5%)")
    
    print(f"\n✅ Metric Status:")
    print(f"   Precision:    {'PASS ✓' if overall['avg_precision'] >= 0.9 else 'FAIL ✗'}")
    print(f"   Recall:       {'PASS ✓' if overall['avg_recall'] >= 0.85 else 'FAIL ✗'}")
    print(f"   F1 Score:     {'PASS ✓' if overall['avg_f1'] >= 0.9 else 'FAIL ✗'}")
    print(f"   Hallucination: {'PASS ✓' if overall['avg_hallucination_rate'] <= 0.05 else 'FAIL ✗'}")
    
    return overall

# =============================================================================
# MAIN
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="Run Chapter 5 Entity Extraction Tests")
    parser.add_argument("--url", default=DEFAULT_API_URL, help="API base URL")
    parser.add_argument("--pattern", default="all", help="Pattern to test (or 'all')")
    parser.add_argument("--start", type=int, help="Start test ID")
    parser.add_argument("--end", type=int, help="End test ID")
    
    args = parser.parse_args()
    
    print(f"""
{'='*80}
SAMM Chapter 5 Entity Extraction Test Runner - CORRECTED v2
   Chapter: Foreign Military Sales (FMS) Case Development
   API: {args.url}
   Pattern: {args.pattern}
   Time: {datetime.now().isoformat()}
{'='*80}
""")
    
    if args.pattern == "all":
        overall = run_all_tests(args.url)
    else:
        results = run_pattern_tests(args.url, args.pattern)
        overall = calculate_overall_metrics(results)
    
    # Save results
    output_file = "chapter5_test_results_v2.json"
    with open(output_file, "w") as f:
        json.dump(overall, f, indent=2)
    print(f"\n✅ Results saved to {output_file}")

if __name__ == "__main__":
    main()
