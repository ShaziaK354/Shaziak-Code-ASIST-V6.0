"""
Simple Single Question Tester - For Debugging
Run this to test ONE question and see the FULL error response
"""

import requests
import json

# Configuration
API_URL = "http://127.0.0.1:3000"
ENDPOINT = "/api/test/query"

def test_single_question(question: str):
    """Test a single question and show full response"""
    
    print("="*70)
    print(f"🧪 TESTING: {question}")
    print("="*70)
    
    url = f"{API_URL}{ENDPOINT}"
    payload = {"question": question}
    
    print(f"\n📡 Calling: {url}")
    print(f"📤 Payload: {json.dumps(payload)}")
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        
        print(f"\n📥 Status Code: {response.status_code}")
        print(f"📥 Headers: {dict(response.headers)}")
        
        # Try to parse JSON
        try:
            data = response.json()
            print(f"\n📦 Response JSON:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
            
            # Check for answer
            if "answer" in data:
                print(f"\n✅ ANSWER FOUND ({len(data['answer'])} chars):")
                print("-"*50)
                print(data['answer'][:500])
                print("-"*50)
            else:
                print(f"\n⚠️ NO 'answer' FIELD IN RESPONSE!")
                print(f"   Available keys: {list(data.keys())}")
                
            # Check for error
            if "error" in data:
                print(f"\n❌ ERROR in response: {data['error']}")
                
        except json.JSONDecodeError:
            print(f"\n📥 Raw Response (not JSON):")
            print(response.text[:1000])
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ CONNECTION ERROR - Is server running at {API_URL}?")
    except requests.exceptions.Timeout:
        print(f"\n❌ TIMEOUT - Server took too long to respond")
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")

def main():
    # Test questions - one at a time
    questions = [
        "What is Security Cooperation?",
        "What is the difference between SC and SA?",
        "Who supervises Security Assistance programs?",
    ]
    
    print("\n" + "#"*70)
    print("# SINGLE QUESTION DIAGNOSTIC TESTER")
    print("# Tests ONE question at a time to debug issues")
    print("#"*70)
    
    # Test first question only
    test_single_question(questions[0])
    
    # Ask if user wants to continue
    print("\n" + "="*70)
    user_input = input("Test next question? (y/n): ").strip().lower()
    
    if user_input == 'y':
        for q in questions[1:]:
            test_single_question(q)
            cont = input("\nContinue? (y/n): ").strip().lower()
            if cont != 'y':
                break

if __name__ == "__main__":
    main()
