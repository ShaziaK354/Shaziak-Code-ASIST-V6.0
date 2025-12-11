"""
SAMM RAG Test Script - Ready to Run with Your app.py
====================================================

This script tests your existing RAG system using your app.py functions.
Just run: python test_samm.py

Requirements:
1. Your app.py must be in the same directory OR imported
2. Ollama must be running
3. Your environment variables must be set (.env file)
"""

import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Tuple
from dataclasses import dataclass

# Add your app directory to path if needed
# sys.path.append('/path/to/your/app/directory')

# Import from your app.py
try:
    # Import using importlib for filenames with dots
    import importlib.util
    spec = importlib.util.spec_from_file_location("app", "app_3.1.1.py")
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    
    orchestrator = app_module.orchestrator
    process_samm_query = app_module.process_samm_query
    print("✓ Successfully imported from app_2.1.41.py")
except ImportError as e:
    print(f"✗ Error importing from app: {e}")
    print("\nMake sure:")
    print("1. app_2_1_41.py is in the same directory")
    print("2. OR update the import statement above")
    print("3. All dependencies are installed")
    sys.exit(1)

# =============================================================================
# TEST QUESTIONS (from SAMM Chapter 1)
# =============================================================================

@dataclass
class TestQuestion:
    id: str
    question: str
    expected_keywords: List[str]
    expected_section: str
    category: str

TEST_QUESTIONS = [
    TestQuestion(
        id="Q1",
        question="What is DSCA responsible for?",
        expected_keywords=["directs", "administers", "provides guidance", "DoD Components", "SC programs"],
        expected_section="C1.3.2.2",
        category="Organizations"
    ),
    TestQuestion(
        id="Q2",
        question="Who administers Security Assistance programs?",
        expected_keywords=["Secretary of State", "continuous supervision", "general direction"],
        expected_section="C1.1.2.2",
        category="Authority"
    ),
    TestQuestion(
        id="Q3",
        question="What is the difference between Security Cooperation and Security Assistance?",
        expected_keywords=["subset", "Title 10", "Title 22", "broader"],
        expected_section="C1.1.2",
        category="Distinctions"
    ),
    TestQuestion(
        id="Q4",
        question="What is Security Cooperation?",
        expected_keywords=["DoD activities", "international partners", "strategic objectives"],
        expected_section="C1.1.1",
        category="Definitions"
    ),
    TestQuestion(
        id="Q5",
        question="What is Security Assistance?",
        expected_keywords=["Title 22", "defense articles", "training", "Secretary of State"],
        expected_section="C1.1.2.2",
        category="Definitions"
    ),
    TestQuestion(
        id="Q6",
        question="What does DFAS do?",
        expected_keywords=["accounting", "billing", "disbursing", "collecting", "SC programs"],
        expected_section="C1.3.2.8",
        category="Organizations"
    ),
    TestQuestion(
        id="Q7",
        question="Which organization manages FMS cases for the Navy?",
        expected_keywords=["NIPO", "Navy International Programs Office"],
        expected_section="C1.3.2.6.1.2",
        category="Organizations"
    ),
    TestQuestion(
        id="Q8",
        question="What are the primary legislative authorities for Security Assistance?",
        expected_keywords=["FAA", "AECA", "Foreign Assistance Act", "Arms Export Control Act"],
        expected_section="C1.2.1",
        category="Legal Authorities"
    ),
    TestQuestion(
        id="Q9",
        question="What is the role of the Department of State in Security Assistance?",
        expected_keywords=["continuous supervision", "general direction", "oversight"],
        expected_section="C1.3.1",
        category="Authority"
    ),
    TestQuestion(
        id="Q10",
        question="What is an Implementing Agency?",
        expected_keywords=["MILDEP", "defense agency", "execution", "SC programs"],
        expected_section="C1.3.2.6",
        category="Definitions"
    )
]

# =============================================================================
# SCORING FUNCTIONS
# =============================================================================

def score_answer(question: TestQuestion, answer: str, metadata: Dict) -> Dict:
    """Score an answer against expected criteria"""
    score = 0
    max_score = 5
    feedback = []
    
    # 1. Check for expected keywords (0-3 points)
    found_keywords = sum(1 for kw in question.expected_keywords if kw.lower() in answer.lower())
    keyword_ratio = found_keywords / len(question.expected_keywords)
    
    if keyword_ratio >= 0.8:
        score += 3
        feedback.append(f"✓ Excellent keyword coverage ({found_keywords}/{len(question.expected_keywords)})")
    elif keyword_ratio >= 0.5:
        score += 2
        feedback.append(f"~ Partial keyword coverage ({found_keywords}/{len(question.expected_keywords)})")
    elif keyword_ratio >= 0.3:
        score += 1
        feedback.append(f"⚠ Limited keyword coverage ({found_keywords}/{len(question.expected_keywords)})")
    else:
        feedback.append(f"✗ Poor keyword coverage ({found_keywords}/{len(question.expected_keywords)})")
    
    # 2. Check for section citation (0-1 point)
    section_base = question.expected_section.split('.')[0:3]  # e.g., C1.3.2
    section_pattern = '.'.join(section_base)
    
    if question.expected_section in answer or section_pattern in answer:
        score += 1
        feedback.append("✓ Correct section cited")
    else:
        feedback.append("✗ Missing or incorrect section citation")
    
    # 3. Check answer quality (0-1 point)
    word_count = len(answer.split())
    if 50 <= word_count <= 300:
        score += 1
        feedback.append(f"✓ Good length ({word_count} words)")
    elif word_count < 50:
        feedback.append(f"⚠ Too short ({word_count} words)")
    else:
        feedback.append(f"⚠ Too long ({word_count} words)")
    
    return {
        'score': score,
        'max_score': max_score,
        'percentage': round((score / max_score) * 100, 1),
        'feedback': ' | '.join(feedback),
        'keywords_found': found_keywords,
        'keywords_total': len(question.expected_keywords),
        'word_count': word_count
    }

# =============================================================================
# TEST RUNNER
# =============================================================================

def run_tests():
    """Run all test questions and generate report"""
    
    print("\n" + "="*80)
    print("SAMM RAG SYSTEM TEST")
    print("="*80)
    print(f"Testing {len(TEST_QUESTIONS)} questions...")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = []
    total_score = 0
    total_max_score = 0
    
    for i, test_q in enumerate(TEST_QUESTIONS, 1):
        print(f"[{i}/{len(TEST_QUESTIONS)}] Testing {test_q.id}: {test_q.question}")
        
        try:
            # Call your RAG system
            result = process_samm_query(
                query=test_q.question,
                chat_history=[],
                documents_context=[],
                user_profile={"authorization_level": "top_secret"}
            )
            
            # Extract answer and metadata
            answer = result.get('answer', '')
            metadata = result.get('metadata', {})
            
            # Score the answer
            score_result = score_answer(test_q, answer, metadata)
            
            # Store result
            test_result = {
                'question': test_q,
                'answer': answer,
                'metadata': metadata,
                'score': score_result,
                'success': True
            }
            results.append(test_result)
            
            # Update totals
            total_score += score_result['score']
            total_max_score += score_result['max_score']
            
            # Print immediate feedback
            print(f"  Score: {score_result['score']}/{score_result['max_score']} ({score_result['percentage']}%)")
            print(f"  {score_result['feedback']}\n")
            
        except Exception as e:
            print(f"  ✗ ERROR: {str(e)}\n")
            results.append({
                'question': test_q,
                'answer': None,
                'metadata': {},
                'score': {'score': 0, 'max_score': 5, 'percentage': 0, 'feedback': f'Error: {str(e)}'},
                'success': False
            })
            total_max_score += 5
    
    # Calculate overall statistics
    overall_percentage = round((total_score / total_max_score) * 100, 1) if total_max_score > 0 else 0
    
    # Generate report
    print_report(results, total_score, total_max_score, overall_percentage)
    
    # Save detailed results
    save_results(results, total_score, total_max_score, overall_percentage)
    
    return results

def print_report(results: List[Dict], total_score: int, total_max_score: int, overall_percentage: float):
    """Print test report"""
    
    print("\n" + "="*80)
    print("TEST REPORT")
    print("="*80)
    print(f"Overall Score: {total_score}/{total_max_score} ({overall_percentage}%)")
    
    # Grade
    if overall_percentage >= 90:
        grade = "A - Excellent"
    elif overall_percentage >= 80:
        grade = "B - Good (Production Ready)"
    elif overall_percentage >= 70:
        grade = "C - Needs Improvement"
    elif overall_percentage >= 60:
        grade = "D - Poor"
    else:
        grade = "F - Failing"
    
    print(f"Grade: {grade}")
    
    # Category breakdown
    print("\n" + "-"*80)
    print("SCORES BY CATEGORY")
    print("-"*80)
    
    categories = {}
    for result in results:
        cat = result['question'].category
        if cat not in categories:
            categories[cat] = {'score': 0, 'max': 0}
        categories[cat]['score'] += result['score']['score']
        categories[cat]['max'] += result['score']['max_score']
    
    for cat, scores in sorted(categories.items()):
        pct = round((scores['score'] / scores['max']) * 100, 1) if scores['max'] > 0 else 0
        print(f"{cat:.<40} {scores['score']}/{scores['max']} ({pct}%)")
    
    # Failed questions
    print("\n" + "-"*80)
    print("FAILED QUESTIONS (Score < 3)")
    print("-"*80)
    
    failed = [r for r in results if r['success'] and r['score']['score'] < 3]
    
    if failed:
        for result in failed:
            q = result['question']
            print(f"\n{q.id}: {q.question}")
            print(f"Score: {result['score']['score']}/{result['score']['max_score']}")
            print(f"Feedback: {result['score']['feedback']}")
            print(f"Missing keywords: {[kw for kw in q.expected_keywords if kw.lower() not in result['answer'].lower()]}")
    else:
        print("✓ All questions passed!")
    
    # Errors
    errors = [r for r in results if not r['success']]
    if errors:
        print("\n" + "-"*80)
        print("ERRORS")
        print("-"*80)
        for result in errors:
            print(f"\n{result['question'].id}: {result['question'].question}")
            print(f"Error: {result['score']['feedback']}")
    
    print("\n" + "="*80)

def save_results(results: List[Dict], total_score: int, total_max_score: int, overall_percentage: float):
    """Save results to JSON file"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"samm_test_results_{timestamp}.json"
    
    output = {
        'summary': {
            'total_score': total_score,
            'total_max_score': total_max_score,
            'percentage': overall_percentage,
            'total_questions': len(results),
            'passed': sum(1 for r in results if r['success'] and r['score']['score'] >= 3),
            'failed': sum(1 for r in results if r['success'] and r['score']['score'] < 3),
            'errors': sum(1 for r in results if not r['success']),
            'timestamp': datetime.now().isoformat()
        },
        'results': [
            {
                'question_id': r['question'].id,
                'question': r['question'].question,
                'category': r['question'].category,
                'expected_section': r['question'].expected_section,
                'answer': r['answer'],
                'score': r['score']['score'],
                'max_score': r['score']['max_score'],
                'percentage': r['score']['percentage'],
                'feedback': r['score']['feedback'],
                'success': r['success'],
                'metadata': {
                    'intent': r['metadata'].get('intent', 'unknown'),
                    'entities_found': r['metadata'].get('entities_found', 0),
                    'execution_time': r['metadata'].get('execution_time_seconds', 0)
                }
            }
            for r in results
        ]
    }
    
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Detailed results saved to: {filename}")

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("SAMM RAG SYSTEM TEST RUNNER")
    print("="*80)
    print("This script will test your RAG system with 10 SAMM Chapter 1 questions")
    print("and provide a detailed performance report.")
    print("\nPress Enter to start testing...")
    input()
    
    try:
        results = run_tests()
        
        print("\n" + "="*80)
        print("✓ Testing complete!")
        print("="*80)
        
        # Quick summary
        total_score = sum(r['score']['score'] for r in results if r['success'])
        total_max = sum(r['score']['max_score'] for r in results)
        pct = round((total_score / total_max) * 100, 1) if total_max > 0 else 0
        
        print(f"\nYour RAG system scored: {total_score}/{total_max} ({pct}%)")
        
        if pct >= 80:
            print("✓ PASS - Your system is production ready!")
        else:
            print("⚠ NEEDS IMPROVEMENT - Review the failed questions above")
            print("\nNext steps:")
            print("1. Look at the 'FAILED QUESTIONS' section above")
            print("2. Check which keywords are missing")
            print("3. Verify your Cosmos DB has the right data")
            print("4. Check your vector database chunks")
        
    except KeyboardInterrupt:
        print("\n\n✗ Testing interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
