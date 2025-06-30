#!/usr/bin/env python3
"""
Backend API test script
Tests if the backend server is running and responding correctly
"""
import requests
import json
import sys

def test_backend_connection():
    """Test backend server connection"""
    
    # Test different possible backend URLs
    test_urls = [
        "http://localhost:8083/chatbot/api",
        "http://localhost:8085/chatbot/api", 
        "https://workmatechat.com/chatbot/api"
    ]
    
    for base_url in test_urls:
        print(f"\n🔍 Testing backend at: {base_url}")
        
        try:
            # Test basic connectivity
            response = requests.get(f"{base_url}/docs", timeout=5)
            if response.status_code == 200:
                print(f"✅ Backend is running at {base_url}")
                print(f"   Status: {response.status_code}")
                return base_url
            else:
                print(f"❌ Backend responded with status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed - server not running on this URL")
        except requests.exceptions.Timeout:
            print(f"❌ Connection timeout")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    return None

def test_chat_endpoint(base_url):
    """Test the chat endpoint specifically"""
    print(f"\n🔍 Testing chat endpoint at: {base_url}/chat")
    
    # Test data
    test_message = {
        "message": "Hello, this is a test message",
        "company_id": "test"
    }
    
    try:
        response = requests.post(
            f"{base_url}/chat",
            json=test_message,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 401:
            print("ℹ️  Authentication required - this is expected")
            return True
        elif response.status_code == 200:
            print("✅ Chat endpoint is working")
            return True
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing chat endpoint: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Backend API Test Script")
    print("=" * 50)
    
    # Test backend connection
    working_url = test_backend_connection()
    
    if working_url:
        print(f"\n✅ Found working backend at: {working_url}")
        
        # Test chat endpoint
        test_chat_endpoint(working_url)
        
        print(f"\n📋 Summary:")
        print(f"   Backend URL: {working_url}")
        print(f"   API Docs: {working_url}/docs")
        
    else:
        print(f"\n❌ No working backend found!")
        print(f"   Make sure the backend server is running")
        print(f"   Check the port configuration")
        sys.exit(1)