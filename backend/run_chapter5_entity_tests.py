"""
Entity Extraction Test Runner for SAMM Chapter 5
=================================================

This script tests your Entity Agent against Chapter 5 ground truth entities.
It measures: Precision, Recall, F1 Score, Hallucination Rate, and Confidence.

Chapter 5: Foreign Military Sales (FMS) Case Development

Usage:
    python run_chapter5_entity_tests.py --url http://172.16.200.12:3000 --pattern all
    python run_chapter5_entity_tests.py --url http://172.16.200.12:3000 --pattern pattern_c5_1_lor
    python run_chapter5_entity_tests.py --url http://172.16.200.12:3000 --start 201 --end 210
"""

import requests
import json
import argparse
import time
from datetime import datetime
from typing import Dict, List, Any, Set

# Import Chapter 5 test cases
from chapter5_entity_implementation import (
    TEST_CASES_CHAPTER_5,
    CHAPTER_5_GROUND_TRUTH,
    CHAPTER_5_ACRONYM_PAIRS,
    get_all_chapter5_tests,
    get_chapter5_ground_truth_entities
)

# =============================================================================
# CONFIGURATION
# =============================================================================
DEFAULT_API_URL = "http://172.16.200.12:3000"
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
# METRICS CALCULATION
# =============================================================================
def calculate_metrics(extracted: List[str], expected: List[str]) -> Dict[str, float]:
    """
    Calculate precision, recall, F1, and hallucination rate
    """
    extracted_set = normalize_set(extracted)
    expected_set = normalize_set(expected)
    
    # Get all ground truth entities for hallucination detection
    ground_truth = get_chapter5_ground_truth_entities()
    ground_truth_normalized = {e.lower() for e in ground_truth}
    
    # True positives: correctly extracted
    true_positives = extracted_set & expected_set
    
    # False positives: extracted but not expected
    false_positives = extracted_set - expected_set
    
    # False negatives: expected but not extracted
    false_negatives = expected_set - extracted_set
    
    # Hallucinations: extracted but not in ANY ground truth
    hallucinations = extracted_set - ground_truth_normalized
    
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
    
    if pattern_name not in TEST_CASES_CHAPTER_5:
        print(f"❌ Unknown pattern: {pattern_name}")
        print(f"Available patterns: {list(TEST_CASES_CHAPTER_5.keys())}")
        return None
    
    pattern = TEST_CASES_CHAPTER_5[pattern_name]
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
            status_icon = "✓" if m['precision'] >= 0.9 and m['recall'] >= 0.85 else "○"
            print(f"    {status_icon} P={m['precision']:.2f} R={m['recall']:.2f} F1={m['f1']:.2f} Hall={m['hallucination_rate']:.2f}")
            print(f"    Extracted: {result['extracted']}")
            print(f"    Expected:  {result['expected']}")
            if m['false_negatives']:
                print(f"    ⚠️  Missing: {m['false_negatives']}")
            if m['hallucinations']:
                print(f"    ⚠️  Hallucinated: {m['hallucinations']}")
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
        print(f"   Avg Precision:    {summary['avg_precision']:.2%} {'✓' if summary['avg_precision'] >= 0.90 else '✗'}")
        print(f"   Avg Recall:       {summary['avg_recall']:.2%} {'✓' if summary['avg_recall'] >= 0.85 else '✗'}")
        print(f"   Avg F1 Score:     {summary['avg_f1']:.2%} {'✓' if summary['avg_f1'] >= 0.90 else '✗'}")
        print(f"   Avg Hallucination: {summary['avg_hallucination_rate']:.2%} {'✓' if summary['avg_hallucination_rate'] <= 0.05 else '✗'}")
        
        return {"results": results, "summary": summary}
    
    return {"results": results, "summary": None}

def run_all_tests(api_url: str) -> Dict:
    """Run all Chapter 5 test patterns"""
    
    all_results = {}
    all_summaries = []
    
    for pattern_name in TEST_CASES_CHAPTER_5.keys():
        result = run_pattern_tests(api_url, pattern_name)
        all_results[pattern_name] = result
        if result and result["summary"]:
            all_summaries.append(result["summary"])
    
    # Overall summary
    if all_summaries:
        print(f"\n{'='*80}")
        print("OVERALL CHAPTER 5 ENTITY EXTRACTION METRICS")
        print(f"{'='*80}")
        
        total_tests = sum(s["total_tests"] for s in all_summaries)
        total_successful = sum(s["successful"] for s in all_summaries)
        
        if total_successful > 0:
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

def run_test_range(api_url: str, start_id: int, end_id: int) -> Dict:
    """Run tests within a specific ID range"""
    all_tests = get_all_chapter5_tests()
    selected_tests = [t for t in all_tests if start_id <= t["id"] <= end_id]
    
    if not selected_tests:
        print(f"❌ No tests found in range {start_id}-{end_id}")
        print(f"   Available IDs: {min(t['id'] for t in all_tests)}-{max(t['id'] for t in all_tests)}")
        return None
    
    print(f"\n{'='*80}")
    print(f"Running tests {start_id} to {end_id}")
    print(f"Total tests: {len(selected_tests)}")
    print(f"{'='*80}\n")
    
    results = []
    for test in selected_tests:
        print(f"  Test #{test['id']}: \"{test['query']}\"")
        result = run_single_test(api_url, test)
        results.append(result)
        
        if result["status"] == "success":
            m = result["metrics"]
            status_icon = "✓" if m['precision'] >= 0.9 and m['recall'] >= 0.85 else "○"
            print(f"    {status_icon} P={m['precision']:.2f} R={m['recall']:.2f} F1={m['f1']:.2f} Hall={m['hallucination_rate']:.2f}")
            print(f"    Extracted: {result['extracted']}")
            print(f"    Expected:  {result['expected']}")
        else:
            print(f"    ✗ Error: {result['error']}")
        
        time.sleep(0.5)
    
    return {"results": results}

# =============================================================================
# COMBINED TEST RUNNER (Chapter 4 + Chapter 5)
# =============================================================================
def run_combined_tests(api_url: str) -> Dict:
    """Run both Chapter 4 and Chapter 5 tests together"""
    try:
        from chapter4_entity_implementation import (
            TEST_CASES_CHAPTER_4,
            get_chapter4_ground_truth_entities
        )
        has_chapter4 = True
    except ImportError:
        has_chapter4 = False
        print("⚠️  Chapter 4 implementation not found, running Chapter 5 only")
    
    all_results = {}
    all_summaries = []
    
    # Run Chapter 5 tests
    print("\n" + "="*80)
    print("CHAPTER 5: FMS Case Development")
    print("="*80)
    
    for pattern_name in TEST_CASES_CHAPTER_5.keys():
        result = run_pattern_tests(api_url, pattern_name)
        all_results[f"ch5_{pattern_name}"] = result
        if result and result["summary"]:
            result["summary"]["chapter"] = 5
            all_summaries.append(result["summary"])
    
    # Calculate overall summary
    if all_summaries:
        print(f"\n{'='*80}")
        print("COMBINED CHAPTER 5 ENTITY EXTRACTION METRICS")
        print(f"{'='*80}")
        
        total_tests = sum(s["total_tests"] for s in all_summaries)
        total_successful = sum(s["successful"] for s in all_summaries)
        
        if total_successful > 0:
            overall_precision = sum(s["avg_precision"] * s["successful"] for s in all_summaries) / total_successful
            overall_recall = sum(s["avg_recall"] * s["successful"] for s in all_summaries) / total_successful
            overall_f1 = sum(s["avg_f1"] * s["successful"] for s in all_summaries) / total_successful
            overall_hallucination = sum(s["avg_hallucination_rate"] * s["successful"] for s in all_summaries) / total_successful
            
            print(f"\n📊 Overall Results ({total_successful}/{total_tests} tests):")
            print(f"   PRECISION:         {overall_precision:.2%} (Target: ≥90%)")
            print(f"   RECALL:            {overall_recall:.2%} (Target: ≥85%)")
            print(f"   F1 SCORE:          {overall_f1:.2%} (Target: ≥90%)")
            print(f"   HALLUCINATION RATE: {overall_hallucination:.2%} (Target: ≤5%)")
            
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
    parser = argparse.ArgumentParser(description="Chapter 5 Entity Extraction Test Runner")
    parser.add_argument("--url", default=DEFAULT_API_URL, help="API base URL")
    parser.add_argument("--pattern", default="all", help="Pattern to test (or 'all')")
    parser.add_argument("--start", type=int, help="Start test ID")
    parser.add_argument("--end", type=int, help="End test ID")
    parser.add_argument("--output", default="chapter5_test_results.json", help="Output file")
    parser.add_argument("--list-patterns", action="store_true", help="List available patterns")
    parser.add_argument("--combined", action="store_true", help="Run both Chapter 4 and Chapter 5 tests")
    
    args = parser.parse_args()
    
    if args.list_patterns:
        print("\n📋 Available Chapter 5 Test Patterns:")
        for name, data in TEST_CASES_CHAPTER_5.items():
            print(f"   {name}: {data['description']} ({len(data['tests'])} tests)")
        exit(0)
    
    print(f"🚀 SAMM Chapter 5 Entity Extraction Test Runner")
    print(f"   Chapter: Foreign Military Sales (FMS) Case Development")
    print(f"   API: {args.url}")
    print(f"   Pattern: {args.pattern}")
    print(f"   Time: {datetime.now().isoformat()}")
    
    if args.combined:
        results = run_combined_tests(args.url)
    elif args.start and args.end:
        results = run_test_range(args.url, args.start, args.end)
    elif args.pattern == "all":
        results = run_all_tests(args.url)
    else:
        results = run_pattern_tests(args.url, args.pattern)
    
    # Save results
    if results:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n✅ Results saved to {args.output}")
