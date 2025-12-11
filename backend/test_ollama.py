"""
Quick Ollama Test - Check if Ollama is responding
"""
import requests
import time

OLLAMA_URL = "http://localhost:11434"

print("="*50)
print("OLLAMA CONNECTION TEST")
print("="*50)

# Test 1: Check if Ollama is running
print("\n1️⃣ Checking Ollama server...")
try:
    r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
    if r.status_code == 200:
        models = r.json().get("models", [])
        print(f"   ✅ Ollama running! Models: {[m['name'] for m in models]}")
    else:
        print(f"   ❌ Ollama returned: {r.status_code}")
except Exception as e:
    print(f"   ❌ Cannot connect: {e}")
    exit(1)

# Test 2: Simple generation
print("\n2️⃣ Testing simple generation (What is 2+2?)...")
start = time.time()
try:
    r = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": "llama3.1:8b",
            "prompt": "What is 2+2? Reply in one word.",
            "stream": False
        },
        timeout=120
    )
    elapsed = time.time() - start
    
    if r.status_code == 200:
        response = r.json().get("response", "No response")
        print(f"   ✅ Response in {elapsed:.2f}s: {response[:100]}")
    else:
        print(f"   ❌ Error: {r.status_code} - {r.text[:200]}")
except requests.exceptions.Timeout:
    print(f"   ❌ TIMEOUT after {time.time()-start:.2f}s")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Longer generation (like actual query)
print("\n3️⃣ Testing longer generation (Security Cooperation)...")
start = time.time()
try:
    r = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": "llama3.1:8b",
            "prompt": "What is Security Cooperation? Answer in 2-3 sentences.",
            "stream": False
        },
        timeout=120
    )
    elapsed = time.time() - start
    
    if r.status_code == 200:
        response = r.json().get("response", "No response")
        print(f"   ✅ Response in {elapsed:.2f}s:")
        print(f"   {response[:300]}...")
    else:
        print(f"   ❌ Error: {r.status_code}")
except requests.exceptions.Timeout:
    print(f"   ❌ TIMEOUT after {time.time()-start:.2f}s")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*50)
print("TEST COMPLETE")
print("="*50)

if elapsed > 30:
    print("\n⚠️ Response is SLOW (>30s)")
    print("   Suggestions:")
    print("   - Try smaller model: llama3.2:3b")
    print("   - Check system RAM/GPU usage")
    print("   - Restart Ollama: taskkill /f /im ollama.exe && ollama serve")
