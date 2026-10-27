#!/usr/bin/env python3
"""
Test the API connection and document upload
"""
import requests
import json
import time

def test_api():
    base_url = "http://127.0.0.1:8000"
    
    print("🔍 Testing Intelli-Credit API Connection...")
    print("=" * 50)
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend server is running!")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("   Please start the backend server first:")
        print("   cd d:\\Chronicles\\intelli-credit\\backend")
        print("   npm start")
        return False
    
    print("\n📄 Testing Document Upload API...")
    
    # Test document upload with a simple text file
    try:
        # Create a test file
        test_content = "This is a test document for OCR processing."
        files = {'file': ('test.txt', test_content, 'text/plain')}
        
        response = requests.post(f"{base_url}/api/v1/documents/upload", files=files, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Document upload test successful!")
                print(f"   Document ID: {result['data']['document_id']}")
                print(f"   File Name: {result['data']['file_name']}")
                print(f"   Confidence: {result['data']['confidence']}")
            else:
                print(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ Upload failed with status: {response.status_code}")
            print(f"   Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Upload test failed: {e}")
    
    print("\n📋 Testing Document List API...")
    
    try:
        response = requests.get(f"{base_url}/api/v1/documents/list", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                docs = result.get('data', [])
                print(f"✅ Document list retrieved successfully!")
                print(f"   Total documents: {result.get('total', 0)}")
                for doc in docs:
                    print(f"   - {doc['file_name']} (ID: {doc['document_id']})")
            else:
                print(f"❌ List failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ List failed with status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ List test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 API Test Complete!")
    print("   Frontend URL: http://localhost:3000")
    print("   Backend URL:  http://127.0.0.1:8000")
    print("   API Docs:     http://127.0.0.1:8000")
    
    return True

if __name__ == "__main__":
    test_api()
