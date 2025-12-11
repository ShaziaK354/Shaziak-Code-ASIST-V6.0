"""
TIMEOUT QUESTION DIAGNOSTIC v1.0
Analyzes WHY specific questions are timing out

Tests the 3 failed questions step by step
"""

import requests
import json
import time
from datetime import datetime

API_URL = "http://127.0.0.1:3000"

# The 3 questions that timed out
TIMEOUT_QUESTIONS = [
    {
        "id": "Q5",
        "question": "What is DSCA's role in Security Cooperation?",
        "expected_entities": ["DSCA", "Defense Security Cooperation Agency"],
        "type": "organization"
    },
    {
        "id": "Q6", 
        "question": "What does DFAS do for Security Cooperation programs?",
        "expected_entities": ["DFAS", "Defense Finance and Accounting Service"],
        "type": "organization"
    },
    {
        "id": "Q7",
        "question": "What is the role of the Under Secretary of Defense for Policy in SC?",
        "expected_entities": ["USD(P)", "Under Secretary of Defense for Policy"],
        "type": "organization"
    }
]

# Compare with a FAST question
FAST_QUESTION = {
    "id": "Q1",
    "question": "What is Security Cooperation?",
    "expected_entities": ["Security Cooperation", "SC"],
    "type": "definition"
}

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)

def analyze_question(q_data, timeout=300):
    """Analyze a single question in detail"""
    
    print(f"\n📋 {q_data['id']}: {q_data['question'][:50]}...")
    print(f"   Type: {q_data['type']}")
    print(f"   Expected entities: {q_data['expected_entities']}")
    print("-"*60)
    
    url = f"{API_URL}/api/test/query"
    payload = {"question": q_data["question"]}
    
    start = time.time()
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        total_time = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            
            # Timing breakdown
            timings = data.get("timings", {})
            intent_time = timings.get("intent", 0)
            entity_time = timings.get("entity", 0)
            answer_time = timings.get("answer", 0)
            
            print(f"\n   ⏱️ TIMING BREAKDOWN:")
            print(f"      Intent:    {intent_time:>6.2f}s  ({intent_time/total_time*100:>5.1f}%)")
            print(f"      Entity:    {entity_time:>6.2f}s  ({entity_time/total_time*100:>5.1f}%)")
            print(f"      Answer:    {answer_time:>6.2f}s  ({answer_time/total_time*100:>5.1f}%)")
            print(f"      TOTAL:     {total_time:>6.2f}s")
            
            # Data sizes
            answer = data.get("answer", "")
            entities = data.get("entities", [])
            
            print(f"\n   📊 DATA SIZES:")
            print(f"      Entities found: {len(entities)} → {entities}")
            print(f"      Answer length: {len(answer)} chars")
            
            # Check data sources
            sources = data.get("data_sources", {})
            if sources:
                print(f"      Vector results: {sources.get('vector_db', 'N/A')}")
                print(f"      Cosmos results: {sources.get('cosmos_gremlin', 'N/A')}")
            
            # Quality
            print(f"\n   ✅ RESULT:")
            print(f"      Quality Score: {data.get('quality_score', 'N/A')}")
            print(f"      Citations: {data.get('citations_found', [])}")
            print(f"      Answer preview: {answer[:150]}...")
            
            return {
                "status": "success",
                "total_time": total_time,
                "intent_time": intent_time,
                "entity_time": entity_time,
                "answer_time": answer_time,
                "entities": entities,
                "answer_length": len(answer)
            }
            
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            return {"status": "error", "code": response.status_code}
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        print(f"   ❌ TIMEOUT after {elapsed:.2f}s!")
        print(f"   ⚠️ Question took longer than {timeout}s")
        return {"status": "timeout", "elapsed": elapsed}
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {"status": "error", "message": str(e)}

def main():
    print("\n" + "#"*70)
    print("#" + " "*15 + "TIMEOUT QUESTION DIAGNOSTIC" + " "*16 + "#")
    print("#" + " "*10 + "Analyzing WHY certain questions timeout" + " "*11 + "#")
    print("#"*70)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # First test a FAST question as baseline
    print_section("1️⃣ BASELINE - FAST QUESTION (Q1: Definition)")
    results["baseline"] = analyze_question(FAST_QUESTION, timeout=180)
    
    # Now test each timeout question
    print_section("2️⃣ TIMEOUT QUESTIONS (Organization/Role)")
    
    for q in TIMEOUT_QUESTIONS:
        print(f"\n{'─'*70}")
        results[q["id"]] = analyze_question(q, timeout=300)  # 5 min timeout
        
        # Ask if user wants to continue
        if results[q["id"]]["status"] == "timeout":
            print(f"\n   ⚠️ {q['id']} timed out. Server might need restart.")
    
    # Summary
    print_section("3️⃣ COMPARISON SUMMARY")
    
    print("\n   📊 TIMING COMPARISON:")
    print("   " + "-"*60)
    print(f"   {'Question':<8} {'Type':<12} {'Intent':<8} {'Entity':<8} {'Answer':<10} {'Total':<10}")
    print("   " + "-"*60)
    
    for qid, data in results.items():
        if data["status"] == "success":
            q_type = "definition" if qid == "baseline" else "org/role"
            print(f"   {qid:<8} {q_type:<12} {data['intent_time']:<8.2f} {data['entity_time']:<8.2f} {data['answer_time']:<10.2f} {data['total_time']:<10.2f}")
        else:
            print(f"   {qid:<8} {'─':<12} {'─':<8} {'─':<8} {'─':<10} {data.get('status', 'FAILED'):<10}")
    
    print("   " + "-"*60)
    
    # Analysis
    print_section("4️⃣ ROOT CAUSE ANALYSIS")
    
    baseline = results.get("baseline", {})
    if baseline.get("status") == "success":
        baseline_time = baseline.get("total_time", 0)
        baseline_entity = baseline.get("entity_time", 0)
        baseline_answer = baseline.get("answer_time", 0)
        
        print(f"\n   Baseline (Q1 Definition):")
        print(f"   • Entity extraction: {baseline_entity:.2f}s")
        print(f"   • Answer generation: {baseline_answer:.2f}s")
        
        for qid in ["Q5", "Q6", "Q7"]:
            data = results.get(qid, {})
            if data.get("status") == "success":
                entity_diff = data["entity_time"] - baseline_entity
                answer_diff = data["answer_time"] - baseline_answer
                
                print(f"\n   {qid} vs Baseline:")
                print(f"   • Entity time: +{entity_diff:.2f}s ({data['entity_time']:.2f}s vs {baseline_entity:.2f}s)")
                print(f"   • Answer time: +{answer_diff:.2f}s ({data['answer_time']:.2f}s vs {baseline_answer:.2f}s)")
                
                if entity_diff > 5:
                    print(f"   → ⚠️ ENTITY EXTRACTION is significantly slower!")
                if answer_diff > 30:
                    print(f"   → ⚠️ ANSWER GENERATION is significantly slower!")
            elif data.get("status") == "timeout":
                print(f"\n   {qid}: TIMED OUT - likely stuck in answer generation")
    
    print_section("5️⃣ HYPOTHESIS")
    print("""
   Organization/Role questions may be slow because:
   
   1. MORE COSMOS DB RELATIONSHIPS
      - DSCA has many relationships (reportsto, coordinateswith, oversees, etc.)
      - Each relationship requires processing
      
   2. LARGER CONTEXT BUILT
      - More relationships = bigger context for Ollama
      - Bigger context = slower generation
      
   3. ORGANIZATION INTENT = LONGER INSTRUCTIONS
      - Each intent type has different base instructions
      - Organization type may have more complex prompts
      
   4. MORE VECTOR DB RESULTS
      - Organization names appear in many SAMM sections
      - More results = more processing
      
   ✅ RECOMMENDED: Check server logs for exact input sizes
   Look for: [Ollama Enhanced] 📊 INPUT SIZE:
""")
    
    print("\n" + "="*70)
    print("DIAGNOSTIC COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()
