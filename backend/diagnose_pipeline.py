"""
SAMM Agent - Detailed Diagnostic Tool v1.0
Analyzes EVERY step of the query pipeline to find bottlenecks

Run: python diagnose_pipeline.py
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_URL = "http://127.0.0.1:3000"
OLLAMA_URL = "http://localhost:11434"
TEST_QUESTION = "What is Security Cooperation?"

def format_size(text):
    """Format text size in chars and approx tokens"""
    chars = len(text) if text else 0
    tokens = chars // 4  # Rough estimate: 4 chars = 1 token
    return f"{chars:,} chars (~{tokens:,} tokens)"

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)

def test_ollama_direct():
    """Test Ollama directly with different prompt sizes"""
    print_section("1️⃣ OLLAMA DIRECT TEST")
    
    test_cases = [
        ("Tiny", "Hi"),
        ("Small", "What is 2+2?"),
        ("Medium", "What is Security Cooperation? Answer in 2 sentences."),
        ("Large", """You are a SAMM expert. Based on the following context, answer the question.

Context:
Security cooperation (SC) comprises all activities undertaken by the DoD to encourage 
and enable international partners to work with the United States to achieve strategic 
objectives. It includes all DoD interactions with foreign defense and security 
establishments, including all DoD-administered security assistance (SA) programs.

Question: What is Security Cooperation?

Provide a comprehensive answer with SAMM section citations."""),
    ]
    
    for name, prompt in test_cases:
        print(f"\n📝 Test: {name} ({format_size(prompt)})")
        start = time.time()
        try:
            r = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": "llama3.1:8b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 200}
                },
                timeout=180
            )
            elapsed = time.time() - start
            
            if r.status_code == 200:
                response = r.json().get("response", "")
                print(f"   ✅ Time: {elapsed:.2f}s")
                print(f"   📤 Output: {format_size(response)}")
                print(f"   📄 Preview: {response[:100]}...")
            else:
                print(f"   ❌ Error: {r.status_code}")
        except requests.exceptions.Timeout:
            print(f"   ❌ TIMEOUT after {time.time()-start:.2f}s")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_api_steps():
    """Test API and analyze each step"""
    print_section("2️⃣ API ENDPOINT TEST")
    
    url = f"{API_URL}/api/test/query"
    payload = {"question": TEST_QUESTION}
    
    print(f"\n📡 Endpoint: {url}")
    print(f"📤 Request: {json.dumps(payload)}")
    
    start = time.time()
    try:
        r = requests.post(url, json=payload, timeout=300)  # 5 min timeout
        total_time = time.time() - start
        
        print(f"\n⏱️ Total Response Time: {total_time:.2f}s")
        print(f"📥 Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            
            print(f"\n📊 RESPONSE ANALYSIS:")
            print("-"*50)
            
            # Check timings
            if "timings" in data:
                print("\n⏱️ Step Timings:")
                for step, time_val in data["timings"].items():
                    pct = (time_val / total_time * 100) if total_time > 0 else 0
                    bar = "█" * int(pct/5) + "░" * (20 - int(pct/5))
                    print(f"   {step:<15}: {time_val:>6.2f}s  {bar} {pct:.1f}%")
            
            # Check answer
            answer = data.get("answer", "")
            print(f"\n📝 Answer:")
            print(f"   Length: {format_size(answer)}")
            if answer:
                print(f"   Preview: {answer[:200]}...")
            else:
                print(f"   ⚠️ NO ANSWER!")
            
            # Check other fields
            print(f"\n📋 Other Data:")
            print(f"   Intent: {data.get('intent', 'N/A')} (conf: {data.get('intent_confidence', 0):.2f})")
            print(f"   Entities: {data.get('entities', [])}")
            print(f"   Quality Score: {data.get('quality_score', 'N/A')}")
            print(f"   Citations: {data.get('citations_found', [])}")
            print(f"   Vector Results: {data.get('vector_results_count', data.get('data_sources', {}).get('vector_db', 'N/A'))}")
            print(f"   Cosmos Results: {data.get('cosmos_results_count', data.get('data_sources', {}).get('cosmos_gremlin', 'N/A'))}")
            
            # Check for errors
            if "error" in data:
                print(f"\n❌ Error in response: {data['error']}")
                
        else:
            print(f"\n❌ HTTP Error: {r.status_code}")
            print(f"Response: {r.text[:500]}")
            
    except requests.exceptions.Timeout:
        print(f"\n❌ TIMEOUT after {time.time()-start:.2f}s")
        print("   The server is taking too long to respond.")
    except requests.exceptions.ConnectionError:
        print(f"\n❌ CONNECTION ERROR - Is server running at {API_URL}?")
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")

def check_server_logs_hint():
    """Provide hint about checking server logs"""
    print_section("3️⃣ SERVER-SIDE DEBUGGING")
    
    print("""
To see detailed server-side timing, check your terminal where app is running.
You should see logs like:

[TEST ENDPOINT] 🧪 Query: What is Security Cooperation?
[IntentAgent] ...
[TEST ENDPOINT] ✅ Intent: definition (0.91)
[IntegratedEntityAgent] ...
[TEST ENDPOINT] ✅ Entities: ['Security Cooperation', 'SC']
[Ollama Enhanced] Attempt 1/3 (timeout: 120s)   <-- CHECK THIS
[Ollama Enhanced] ✅ Success - XXX chars         <-- OR THIS
[TEST ENDPOINT] ✅ Answer generated: XXX chars

If you see:
- "Timeout on attempt 1" → Ollama is too slow
- "Success" but no answer in response → Response parsing issue
- No "Answer generated" line → Error before answer generation
""")

def analyze_context_size():
    """Estimate context size being sent to Ollama"""
    print_section("4️⃣ CONTEXT SIZE ESTIMATION")
    
    print("""
Based on your earlier logs, the context includes:

📊 TYPICAL CONTEXT BREAKDOWN:
┌─────────────────────────────────────┬──────────────┬────────────┐
│ Component                           │ Size (chars) │ ~Tokens    │
├─────────────────────────────────────┼──────────────┼────────────┤
│ System Message (SAMM expert prompt) │ ~2,000       │ ~500       │
│ Entity Definitions (5 entities)     │ ~1,500       │ ~375       │
│ Vector DB Results (5 chunks)        │ ~5,000       │ ~1,250     │
│ Relationships (13 relationships)    │ ~1,000       │ ~250       │
│ User Question                       │ ~50          │ ~12        │
├─────────────────────────────────────┼──────────────┼────────────┤
│ TOTAL INPUT                         │ ~9,550       │ ~2,400     │
│ Expected Output                     │ ~1,500       │ ~375       │
├─────────────────────────────────────┼──────────────┼────────────┤
│ TOTAL CONTEXT                       │ ~11,000      │ ~2,750     │
└─────────────────────────────────────┴──────────────┴────────────┘

⚠️ num_ctx in app is set to 2048 tokens - this may be TOO SMALL!

The model config shows:
  "num_ctx": 2048,      ← Context window
  "num_predict": 500    ← Max output tokens

If input is ~2,400 tokens but num_ctx is 2048, context gets TRUNCATED!
""")

def suggest_fixes():
    """Suggest potential fixes"""
    print_section("5️⃣ RECOMMENDED FIXES")
    
    print("""
Based on analysis, here are potential fixes:

🔧 FIX 1: Increase Context Window (Recommended)
   In app, find call_ollama_enhanced() and change:
   "num_ctx": 2048  →  "num_ctx": 4096
   
🔧 FIX 2: Reduce Context Size
   - Limit vector results from 5 to 3
   - Limit relationships from 13 to 5
   - Shorter system message
   
🔧 FIX 3: Use Faster Model
   Change OLLAMA_MODEL from "llama3.1:8b" to "llama3.2:3b"
   (Faster but less accurate)
   
🔧 FIX 4: Increase Timeout Further
   OLLAMA_TIMEOUT_NORMAL = 180  (3 minutes)
   
🔧 FIX 5: Reduce Output Length
   "num_predict": 500  →  "num_predict": 300

Would you like me to apply any of these fixes?
""")

def main():
    print("\n" + "#"*70)
    print("#" + " "*20 + "SAMM AGENT DIAGNOSTIC" + " "*21 + "#")
    print("#" + " "*15 + "Detailed Pipeline Analysis v1.0" + " "*16 + "#")
    print("#"*70)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test Question: '{TEST_QUESTION}'")
    
    # Run all diagnostics
    test_ollama_direct()
    test_api_steps()
    check_server_logs_hint()
    analyze_context_size()
    suggest_fixes()
    
    print("\n" + "="*70)
    print("DIAGNOSTIC COMPLETE")
    print("="*70)
    print("\nShare the output above to identify the exact bottleneck.")

if __name__ == "__main__":
    main()
