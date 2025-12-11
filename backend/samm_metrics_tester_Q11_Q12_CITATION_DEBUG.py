"""
SAMM Citation Debug Tester - Q11 & Q12 Only
============================================
Testing ITAR and USML questions to debug wrong citations

Q11: What is ITAR and who manages it?
     Expected: C1.3.1
     Getting: C7.17.1.1 (WRONG!)

Q12: What is USML?
     Expected: C1.3.1
     Getting: C12 (WRONG!)
"""

import requests
import json
import time
from datetime import datetime

API_BASE_URL = "http://127.0.0.1:3000"
ENDPOINT = "/api/test/query"

# Only Q11 and Q12
TEST_QUESTIONS = [
    {
        "id": "Q11",
        "question": "What is ITAR and who manages it?",
        "expected_section": "C1.3.1",
        "expected_citations": ["C1.3.1"],
    },
    {
        "id": "Q12",
        "question": "What is USML?",
        "expected_section": "C1.3.1", 
        "expected_citations": ["C1.3.1"],
    },
]

def run_test():
    print("="*70)
    print("CITATION DEBUG TEST - Q11 & Q12")
    print("="*70)
    print(f"Started: {datetime.now().isoformat()}")
    print()
    
    for q in TEST_QUESTIONS:
        print("="*70)
        print(f"Testing: {q['id']}")
        print(f"Question: {q['question']}")
        print(f"Expected Citation: {q['expected_section']}")
        print("="*70)
        
        try:
            payload = {"question": q["question"]}
            start = time.time()
            response = requests.post(
                f"{API_BASE_URL}{ENDPOINT}",
                json=payload,
                timeout=200
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                citations = data.get("citations", [])
                
                print(f"\n⏱️ Response Time: {elapsed:.1f}s")
                print(f"\n📝 ANSWER ({len(answer)} chars):")
                print("-"*50)
                print(answer[:1000] + "..." if len(answer) > 1000 else answer)
                print("-"*50)
                
                print(f"\n📚 CITATIONS RETURNED BY API: {citations}")
                print(f"🎯 EXPECTED CITATION: {q['expected_section']}")
                
                # Check if expected citation is in answer
                if q['expected_section'] in answer:
                    print(f"✅ Expected citation {q['expected_section']} FOUND in answer")
                else:
                    print(f"❌ Expected citation {q['expected_section']} NOT FOUND in answer")
                
                # Find what citations ARE in the answer
                import re
                found_citations = re.findall(r'C\d+\.[\d\.]+', answer)
                print(f"\n🔍 CITATIONS FOUND IN ANSWER TEXT: {found_citations}")
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text[:500])
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    run_test()
