#!/usr/bin/env python3
"""
Simple Power BI Endpoint Test - No Backend Changes Required
Just checks if your Flask app endpoints are accessible
"""

import requests
import json

BASE_URL = "http://localhost:3000"
API_KEY = "25637f8c0d23347ed35a9106a9a0e44ed74524e8329d2fcdb2f4251999cda342"

def test_connection():
    """Test if Flask server is running"""
    print("\n" + "="*60)
    print("🔍 Testing Flask Server Connection")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Flask server is RUNNING")
            print(f"   Status: {response.json().get('status')}")
            return True
        else:
            print(f"⚠️  Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server!")
        print("   Please start your Flask app first:")
        print("   python app_3.2.py")  # or whichever app file you use
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_existing_endpoints():
    """Test what endpoints currently exist"""
    print("\n" + "="*60)
    print("🔍 Checking Existing Endpoints")
    print("="*60)
    
    endpoints_to_check = [
        "/api/query",
        "/api/user/cases",
        "/api/system/status",
        "/api/hitl/reviews",
        "/api/hitl/statistics",
    ]
    
    working_endpoints = []
    
    for endpoint in endpoints_to_check:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=2)
            if response.status_code in [200, 401, 403]:  # Any response means endpoint exists
                print(f"✅ {endpoint}")
                working_endpoints.append(endpoint)
            else:
                print(f"⚠️  {endpoint} (Status: {response.status_code})")
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint} (Not found)")
        except Exception as e:
            print(f"⚠️  {endpoint} (Error: {str(e)[:30]})")
    
    return working_endpoints

def check_powerbi_endpoints():
    """Check if Power BI endpoints exist"""
    print("\n" + "="*60)
    print("🔍 Checking Power BI Endpoints")
    print("="*60)
    
    powerbi_endpoints = [
        "/api/powerbi/reviews/summary",
        "/api/powerbi/reviews/detailed",
        "/api/powerbi/feedback/summary",
        "/api/powerbi/agent/performance",
    ]
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    found = False
    
    for endpoint in powerbi_endpoints:
        try:
            response = requests.get(
                f"{BASE_URL}{endpoint}?days=30", 
                headers=headers,
                timeout=2
            )
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - WORKING!")
                found = True
            elif response.status_code == 401:
                print(f"⚠️  {endpoint} - EXISTS but needs auth")
                found = True
            elif response.status_code == 404:
                print(f"❌ {endpoint} - NOT FOUND")
            else:
                print(f"⚠️  {endpoint} - Status: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint} - NOT FOUND")
        except Exception as e:
            print(f"⚠️  {endpoint} - Error")
    
    return found

def main():
    print("\n" + "🔍"*30)
    print("Power BI Endpoint Checker")
    print("No backend modification required!")
    print("🔍"*30)
    
    # Step 1: Check server
    if not test_connection():
        print("\n" + "="*60)
        print("❌ STOP: Flask server is not running")
        print("="*60)
        print("\nPlease start your Flask app first:")
        print("1. cd backend")
        print("2. Activate virtual environment: .venv\\Scripts\\activate")
        print("3. python app_3.2.py  (or whichever version you're using)")
        return
    
    # Step 2: Check existing endpoints
    working = test_existing_endpoints()
    
    # Step 3: Check Power BI endpoints
    powerbi_found = check_powerbi_endpoints()
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    if powerbi_found:
        print("✅ Power BI endpoints are READY!")
        print("   You can connect Power BI Desktop now.")
        print("\n📝 Next Steps:")
        print("   1. Open Power BI Desktop")
        print("   2. Get Data → Web")
        print("   3. URL: http://localhost:3000/api/powerbi/reviews/summary?days=30")
        print("   4. Add Header:")
        print("      Name: Authorization")
        print(f"      Value: Bearer {API_KEY}")
    else:
        print("❌ Power BI endpoints NOT found")
        print("\n📝 To add Power BI endpoints:")
        print("   1. Identify which app file you're using (app_3.2.py, app_backup.py, etc.)")
        print("   2. Add powerbi_integration.py code to that file")
        print("   3. Or manually add the endpoints")
        print("\n🔧 Quick Manual Setup:")
        print("   See: MANUAL_INTEGRATION_GUIDE.md")
    
    if working:
        print(f"\n✅ {len(working)} existing endpoints are working")
        print("   Your Flask app is running correctly")

if __name__ == "__main__":
    main()