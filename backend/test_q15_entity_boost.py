"""
Q15 TEST - Entity Boosting Validation
======================================
Tests if entity boosting fixes the Secretary of State retrieval issue
"""

import requests
import json

# Try port 5000 first, then 3000
PORTS = [5000, 3000]
URL_TEMPLATE = "http://localhost:{}/api/test/query"

# Q15 - This was failing because C1.3.1 wasn't being retrieved
question = "What does the Secretary of State approve regarding SA?"

print("=" * 70)
print("Q15 ENTITY BOOSTING TEST")
print("=" * 70)
print(f"\nQuestion: {question}")
print("\nTrying to connect...")

response = None
used_port = None

for port in PORTS:
    url = URL_TEMPLATE.format(port)
    try:
        print(f"  Trying port {port}...")
        response = requests.post(
            url,
            json={"question": question},
            timeout=180
        )
        used_port = port
        print(f"  ✅ Connected on port {port}!")
        break
    except requests.exceptions.ConnectionError:
        print(f"  ❌ Port {port} not available")
        continue
    except Exception as e:
        print(f"  ❌ Port {port} error: {e}")
        continue

if response is None:
    print("\n❌ Cannot connect to server on any port!")
    print("   Start server first: python app_5_7_ENTITY_BOOST.py")
    print("=" * 70)
    exit(1)

if response.status_code == 200:
    data = response.json()
    
    print("\n" + "=" * 70)
    print("ANSWER:")
    print("=" * 70)
    answer = data.get("answer", "No answer")
    print(answer)
    
    print("\n" + "=" * 70)
    print("KEY PHRASE CHECK:")
    print("=" * 70)
    
    key_phrases = [
        "continuous supervision",
        "general direction",
        "program scope",
        "FAA",
        "Foreign Assistance Act",
        "AECA",
        "Arms Export Control Act",
        "EO 13637",
        "Executive Order",
    ]
    
    answer_lower = answer.lower()
    found = []
    missing = []
    
    for phrase in key_phrases:
        if phrase.lower() in answer_lower:
            found.append(phrase)
            print(f"  ✅ Found: {phrase}")
        else:
            missing.append(phrase)
            print(f"  ❌ Missing: {phrase}")
    
    print(f"\n  Score: {len(found)}/{len(key_phrases)} key phrases found")
    
    if len(found) >= 5:
        print("\n  🎉 ENTITY BOOSTING WORKING! Answer has key content!")
    elif len(found) >= 3:
        print("\n  ⚠️ PARTIAL SUCCESS - Some key content found")
    else:
        print("\n  ❌ STILL FAILING - Key content not retrieved")
    
    # Show citations if available
    citations = data.get("citations", [])
    if citations:
        print("\n" + "=" * 70)
        print("CITATIONS:")
        print("=" * 70)
        for c in citations:
            print(f"  • {c}")
    
else:
    print(f"\n❌ Error: {response.status_code}")
    print(response.text)

print("\n" + "=" * 70)
