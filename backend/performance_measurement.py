#!/usr/bin/env python3
"""
ASIST System Performance - 1-Hour Quick Measurement
Customized for app_3_3_5_FAST.py

INSTRUCTIONS:
1. Make sure your Flask app is running on http://localhost:5000
2. Make sure you're logged in (or modify AUTH_TOKEN below)
3. Run: python quick_measurement_asist.py | tee results.txt
"""

import time
import statistics
import concurrent.futures
from datetime import datetime
import requests
import json

# ============================================================================
# CONFIGURATION
# ============================================================================

# Your Flask app URL - IMPORTANT: This should be backend port, NOT frontend
BASE_URL = "http://localhost:5000"  # Backend Flask app
API_QUERY_ENDPOINT = f"{BASE_URL}/api/query"
CACHE_STATS_ENDPOINT = f"{BASE_URL}/api/cache/stats"

# Authentication Options - Pick ONE that works for you:

# Option 1: Session Cookie (EASIEST - Get from browser)
# Steps to get session cookie:
# 1. Open browser and login to localhost:5173
# 2. Press F12 (Developer Tools)
# 3. Go to Application tab → Cookies → localhost
# 4. Copy the 'session' cookie value
# 5. Paste it below:
SESSION_COOKIE = None  # Example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Option 2: Auth0 Bearer Token (If you have it)
AUTH_TOKEN = None  # Set to your Bearer token if you have one

# Option 3: Skip Auth for Testing (Modify app.py first)
# In app.py, temporarily comment out the authentication check:
# @app.route("/api/query", methods=["POST"])
# def query_ai_assistant():
#     # user = require_auth()  # COMMENT THIS OUT FOR TESTING
#     # if not user:
#     #     return jsonify({"error": "User not authenticated"}), 401
#     user = {"sub": "test_user"}  # ADD THIS FOR TESTING
SKIP_AUTH = False  # Set to True if you modified app.py as above

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def make_query_request(query_text: str, chat_history: list = None) -> dict:
    """
    Make a query request to ASIST system
    Returns: {success: bool, response: dict, time: float, from_cache: bool}
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    # Add authentication if available
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    
    cookies = {}
    if SESSION_COOKIE:
        cookies["session"] = SESSION_COOKIE
    
    payload = {
        "question": query_text,
        "chat_history": chat_history or [],
        "staged_chat_documents": []
    }
    
    try:
        start_time = time.time()
        
        response = requests.post(
            API_QUERY_ENDPOINT,
            json=payload,
            headers=headers,
            cookies=cookies,
            timeout=30  # 30 second timeout
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            from_cache = data.get("cached", False)
            
            return {
                "success": True,
                "response": data,
                "time": elapsed,
                "from_cache": from_cache,
                "error": None
            }
        else:
            return {
                "success": False,
                "response": None,
                "time": elapsed,
                "from_cache": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "response": None,
            "time": 30.0,
            "from_cache": False,
            "error": "Request timeout (>30s)"
        }
    except Exception as e:
        return {
            "success": False,
            "response": None,
            "time": 0,
            "from_cache": False,
            "error": str(e)
        }

def get_cache_statistics() -> dict:
    """Get cache statistics from the app"""
    try:
        response = requests.get(CACHE_STATS_ENDPOINT, timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

# ============================================================================
# MAIN MEASUREMENT SCRIPT
# ============================================================================

print("=" * 80)
print("ASIST SYSTEM PERFORMANCE MEASUREMENT")
print("1-Hour Quick Test")
print("=" * 80)
print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Target URL: {BASE_URL}")
print()

# Pre-flight check
print("🔍 Pre-flight check...")
try:
    test_response = requests.get(BASE_URL, timeout=5)
    print(f"✓ Server is running (status: {test_response.status_code})")
except:
    print("❌ ERROR: Cannot reach server at", BASE_URL)
    print("   Please make sure your Flask app is running!")
    print("   Run: python app_3_3_5_FAST.py")
    exit(1)

print()

# ============================================================================
# TASK 1: RESPONSE LATENCY (20 minutes)
# ============================================================================

print("\n[TASK 1/3] RESPONSE LATENCY TEST (20 minutes)")
print("-" * 80)
print("Testing 20 queries across simple, medium, and complex categories...\n")

test_queries = [
    # Simple queries (5)
    "What is FMS?",
    "What is DSCA?", 
    "Define LOA",
    "What is MDE?",
    "What is DCS?",
    
    # Medium queries (10)
    "How do I submit an LOA?",
    "What is the FMS process?",
    "Who approves FMS cases?",
    "What are Chapter 4 requirements?",
    "Difference between FMS and DCS?",
    "What is Congressional Notification?",
    "Timeline for case approval?",
    "What documents are needed for FMS?",
    "Who is involved in the review process?",
    "What is the role of State Department?",
    
    # Complex queries (5)
    "Explain the complete FMS case development process",
    "What are approval requirements for Major Defense Equipment cases?",
    "How does timeline differ between standard and expedited cases?",
    "What is the relationship between LOA, IA, and implementation?",
    "Compare financial requirements across Chapters 5, 6, and 7"
]

response_times = []
cache_hits_during_test = 0
failed_queries = []
task1_start = time.time()

for i, query in enumerate(test_queries, 1):
    print(f"  [{i:2d}/{len(test_queries)}] Testing: {query[:55]:<55}...", end=" ", flush=True)
    
    result = make_query_request(query)
    
    if result["success"]:
        response_times.append(result["time"])
        cache_status = "CACHE" if result["from_cache"] else "FRESH"
        if result["from_cache"]:
            cache_hits_during_test += 1
        print(f"{result['time']:5.2f}s [{cache_status}]")
    else:
        failed_queries.append((query, result["error"]))
        print(f"FAILED: {result['error'][:30]}")

task1_duration = time.time() - task1_start

# Calculate statistics (only for successful queries)
if response_times:
    avg_time = statistics.mean(response_times)
    median_time = statistics.median(response_times)
    min_time = min(response_times)
    max_time = max(response_times)
    
    print(f"\n{'':2}┌─ RESULTS ─" + "─" * 65)
    print(f"{'':2}│ Successful Queries:    {len(response_times)}/{len(test_queries)}")
    print(f"{'':2}│ Average Response Time: {avg_time:5.2f} seconds")
    print(f"{'':2}│ Median Response Time:  {median_time:5.2f} seconds")
    print(f"{'':2}│ Min Time:              {min_time:5.2f} seconds")
    print(f"{'':2}│ Max Time:              {max_time:5.2f} seconds")
    print(f"{'':2}│ Cache Hits During Test:{cache_hits_during_test}")
    print(f"{'':2}│ Test Duration:         {task1_duration:.0f} seconds")
    
    latency_status = "✓ MEETS TARGET" if avg_time <= 5.0 else "⚠ ABOVE TARGET"
    status_color = "✓" if avg_time <= 5.0 else "⚠"
    print(f"{'':2}│")
    print(f"{'':2}│ Status: {status_color} {latency_status} (target ≤5 seconds)")
    
    if failed_queries:
        print(f"{'':2}│")
        print(f"{'':2}│ ⚠ Failed Queries: {len(failed_queries)}")
        for q, err in failed_queries[:3]:  # Show first 3 failures
            print(f"{'':2}│   • {q[:50]}: {err[:30]}")
    
    print(f"{'':2}└" + "─" * 77)
    
    latency_result = {
        "average": avg_time,
        "median": median_time,
        "min": min_time,
        "max": max_time,
        "sample_size": len(response_times),
        "failed": len(failed_queries),
        "status": latency_status
    }
else:
    print("\n❌ All queries failed! Cannot calculate response time metrics.")
    print("   Please check:")
    print("   1. Is the Flask app running?")
    print("   2. Is authentication configured correctly?")
    print("   3. Check the error messages above")
    exit(1)

# ============================================================================
# TASK 2: CACHE HIT RATE (15 minutes)
# ============================================================================

print("\n[TASK 2/3] CACHE HIT RATE TEST (15 minutes)")
print("-" * 80)

# First, try to get cache stats from the API
cache_api_stats = get_cache_statistics()
if cache_api_stats and cache_api_stats.get('enabled'):
    print("✓ Using cache statistics from API\n")
    
    print(f"{'':2}┌─ CACHE STATISTICS FROM API ─" + "─" * 48)
    print(f"{'':2}│ Total Queries:   {cache_api_stats.get('total_queries', 0)}")
    print(f"{'':2}│ Cache Hits:      {cache_api_stats.get('cache_hits', 0)}")
    print(f"{'':2}│ Cache Misses:    {cache_api_stats.get('cache_misses', 0)}")
    print(f"{'':2}│ Hit Rate:        {cache_api_stats.get('hit_rate_percent', 0):.1f}%")
    print(f"{'':2}│ Cache Size:      {cache_api_stats.get('current_size', 0)}/{cache_api_stats.get('max_size', 0)}")
    print(f"{'':2}│ TTL:             {cache_api_stats.get('ttl_seconds', 0)} seconds")
    
    hit_rate = cache_api_stats.get('hit_rate_percent', 0)
    cache_status = "✓ GOOD" if hit_rate >= 30 else "⚠ COULD IMPROVE"
    status_color = "✓" if hit_rate >= 30 else "⚠"
    print(f"{'':2}│")
    print(f"{'':2}│ Status: {status_color} {cache_status} (30%+ is typical)")
    print(f"{'':2}└" + "─" * 77)
    
    cache_result = {
        "hit_rate": hit_rate,
        "hits": cache_api_stats.get('cache_hits', 0),
        "misses": cache_api_stats.get('cache_misses', 0),
        "total": cache_api_stats.get('total_queries', 0),
        "status": cache_status,
        "source": "api"
    }

else:
    # Fallback: Do live testing
    print("⚠ Cache API not available, running live test...\n")
    print("Testing 10 unique queries, 3 times each (30 total queries)...\n")
    
    unique_queries = [
        "What is FMS?",
        "What is DSCA?",
        "How to submit LOA?",
        "FMS approval process?",
        "Chapter 4 requirements?",
        "Congressional notification?",
        "What is MDE?",
        "Timeline for approval?",
        "Difference between FMS and DCS?",
        "Who reviews cases?"
    ]
    
    cache_hits = 0
    cache_misses = 0
    task2_start = time.time()
    
    for round_num in range(3):
        print(f"  Round {round_num + 1}/3:")
        for i, query in enumerate(unique_queries, 1):
            result = make_query_request(query)
            
            if result["success"]:
                if result["from_cache"]:
                    cache_hits += 1
                    print(f"    [{i:2d}] ✓ HIT:  {query}")
                else:
                    cache_misses += 1
                    print(f"    [{i:2d}] ✗ MISS: {query}")
            else:
                cache_misses += 1
                print(f"    [{i:2d}] ✗ ERROR: {query}")
    
    task2_duration = time.time() - task2_start
    
    total_cache_queries = cache_hits + cache_misses
    hit_rate = (cache_hits / total_cache_queries * 100) if total_cache_queries > 0 else 0
    
    print(f"\n{'':2}┌─ RESULTS ─" + "─" * 65)
    print(f"{'':2}│ Cache Hits:      {cache_hits:3d}")
    print(f"{'':2}│ Cache Misses:    {cache_misses:3d}")
    print(f"{'':2}│ Total Queries:   {total_cache_queries:3d}")
    print(f"{'':2}│ Hit Rate:        {hit_rate:5.1f}%")
    print(f"{'':2}│ Test Duration:   {task2_duration:.0f} seconds")
    
    cache_status = "✓ GOOD" if hit_rate >= 30 else "⚠ COULD IMPROVE"
    status_color = "✓" if hit_rate >= 30 else "⚠"
    print(f"{'':2}│")
    print(f"{'':2}│ Status: {status_color} {cache_status} (30%+ is typical)")
    print(f"{'':2}└" + "─" * 77)
    
    cache_result = {
        "hit_rate": hit_rate,
        "hits": cache_hits,
        "misses": cache_misses,
        "total": total_cache_queries,
        "status": cache_status,
        "source": "live_test"
    }

# ============================================================================
# TASK 3: THROUGHPUT (15 minutes)
# ============================================================================

print("\n[TASK 3/3] THROUGHPUT TEST (15 minutes)")
print("-" * 80)
print("Testing concurrent users: 10, 25, 50...\n")

def submit_concurrent_query(user_id):
    """Submit a query as one concurrent user"""
    query = f"What is FMS case {user_id}?"
    result = make_query_request(query)
    return result

task3_start = time.time()
max_handled = 0
test_results = []

for num_users in [10, 25, 50]:
    print(f"  Testing {num_users:3d} concurrent users... ", end="", flush=True)
    
    test_start = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = [executor.submit(submit_concurrent_query, i) for i in range(num_users)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    test_duration = time.time() - test_start
    
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    success_rate = (len(successful) / num_users) * 100
    
    avg_response = sum(r["time"] for r in successful) / len(successful) if successful else 0
    
    passed = len(successful) == num_users and avg_response < 10
    
    if passed:
        max_handled = num_users
        print(f"✓ PASS ({test_duration:4.1f}s, avg response: {avg_response:.2f}s)")
    else:
        print(f"⚠ FAIL (success rate: {success_rate:.0f}%, avg: {avg_response:.2f}s)")
        break
    
    test_results.append({
        "users": num_users,
        "success_rate": success_rate,
        "avg_response": avg_response,
        "passed": passed
    })

task3_duration = time.time() - task3_start

print(f"\n{'':2}┌─ RESULTS ─" + "─" * 65)
print(f"{'':2}│ Maximum Concurrent Users: {max_handled:3d} (without degradation)")
print(f"{'':2}│ Test Duration:            {task3_duration:.0f} seconds")

throughput_status = "✓ GOOD" if max_handled >= 50 else "⚠ ACCEPTABLE" if max_handled >= 25 else "⚠ NEEDS IMPROVEMENT"
status_color = "✓" if max_handled >= 50 else "⚠"
print(f"{'':2}│")
print(f"{'':2}│ Status: {status_color} {throughput_status} (target ≥50 users)")
print(f"{'':2}└" + "─" * 77)

throughput_result = {
    "max_users": max_handled,
    "status": throughput_status
}

# ============================================================================
# FINAL SUMMARY
# ============================================================================

total_duration = (time.time() - task1_start) / 60

print("\n" + "=" * 80)
print("MEASUREMENT COMPLETE - SUMMARY FOR TRAVIS")
print("=" * 80)
print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Total Duration: {total_duration:.1f} minutes\n")

print("📊 PERFORMANCE METRICS:")
print()
print("  ┌─ Response Latency ─────────────────────────────────────────────────")
print(f"  │ Average:     {latency_result['average']:5.2f} seconds")
print(f"  │ Median:      {latency_result['median']:5.2f} seconds")
print(f"  │ Range:       {latency_result['min']:.2f}s - {latency_result['max']:.2f}s")
print(f"  │ Sample Size: {latency_result['sample_size']} queries ({latency_result['failed']} failed)")
print(f"  │ Status:      {latency_result['status']}")
print("  └────────────────────────────────────────────────────────────────────")
print()
print("  ┌─ Cache Hit Rate ───────────────────────────────────────────────────")
print(f"  │ Hit Rate:    {cache_result['hit_rate']:5.1f}%")
print(f"  │ Hits:        {cache_result['hits']:3d} / {cache_result['total']:3d} queries")
print(f"  │ Source:      {cache_result['source']}")
print(f"  │ Status:      {cache_result['status']}")
print("  └────────────────────────────────────────────────────────────────────")
print()
print("  ┌─ Throughput ───────────────────────────────────────────────────────")
print(f"  │ Max Users:   {throughput_result['max_users']:3d} concurrent (without degradation)")
print(f"  │ Status:      {throughput_result['status']}")
print("  └────────────────────────────────────────────────────────────────────")

print("\n" + "=" * 80)
print("✓ READY FOR PRESENTATION")
print("=" * 80)

# Save results to file
results_text = f"""ASIST SYSTEM PERFORMANCE MEASUREMENTS
{"=" * 80}

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Duration: {total_duration:.1f} minutes
Server: {BASE_URL}

RESULTS:

1. Response Latency
   - Average: {latency_result['average']:.2f} seconds
   - Median: {latency_result['median']:.2f} seconds
   - Range: {latency_result['min']:.2f}s - {latency_result['max']:.2f}s
   - Sample: {latency_result['sample_size']} queries ({latency_result['failed']} failed)
   - Status: {latency_result['status']}

2. Cache Hit Rate
   - Hit Rate: {cache_result['hit_rate']:.1f}%
   - Hits: {cache_result['hits']} / {cache_result['total']} queries
   - Source: {cache_result['source']}
   - Status: {cache_result['status']}

3. Throughput
   - Maximum Concurrent Users: {throughput_result['max_users']}
   - Status: {throughput_result['status']}

{"=" * 80}
Ready for Travis Meeting ✓
"""

with open('asist_measurement_results.txt', 'w') as f:
    f.write(results_text)

print("\n📄 Results saved to: asist_measurement_results.txt")
print()

# ============================================================================
# TROUBLESHOOTING TIPS
# ============================================================================

if latency_result.get('failed', 0) > 0 or throughput_result['max_users'] < 25:
    print("\n⚠️  TROUBLESHOOTING TIPS:")
    print("-" * 80)
    
    if latency_result.get('failed', 0) > 0:
        print("• Some queries failed - check authentication:")
        print("  1. Update AUTH_TOKEN or SESSION_COOKIE in this script")
        print("  2. Or set SKIP_AUTH = True if testing without auth")
        print("  3. Check if Flask app is running: python app_3_3_5_FAST.py")
    
    if throughput_result['max_users'] < 25:
        print("• Low throughput detected:")
        print("  1. Check server resources (CPU, memory)")
        print("  2. Check database connection limits")
        print("  3. Consider horizontal scaling")
    
    print()