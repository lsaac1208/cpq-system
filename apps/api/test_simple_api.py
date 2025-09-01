#!/usr/bin/env python3
import requests
import json

# Test login first
login_data = {"username": "admin", "password": "admin123"}
login_response = requests.post("http://127.0.0.1:5000/api/v1/auth/login", json=login_data)

print(f"Login response: {login_response.status_code}")
if login_response.status_code == 200:
    login_result = login_response.json()
    print(f"Login result: {login_result}")
    # Try different possible token locations
    token = (login_result.get('access_token') or 
             login_result.get('token') or 
             login_result.get('data', {}).get('access_token') or
             login_result.get('data', {}).get('token') or
             login_result.get('data', {}).get('tokens', {}).get('access_token'))
    print(f"Got token: {token[:20] if token else 'None'}...")
    
    # Test document analysis
    test_content = """A703产品说明书
ToC509006008
3.2 D  
测试电压 0-240V
"""
    
    with open('/tmp/simple_test.txt', 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    with open('/tmp/simple_test.txt', 'rb') as f:
        files = {'document': ('simple_test.txt', f, 'text/plain')}
        headers = {'Authorization': f'Bearer {token}'}
        
        print("Sending analysis request...")
        response = requests.post(
            "http://127.0.0.1:5000/api/v1/ai-analysis/analyze-document",
            files=files,
            headers=headers,
            timeout=60
        )
        
        print(f"Analysis response: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            specs = result.get('extracted_data', {}).get('specifications', {})
            print(f"Extracted specs: {list(specs.keys())}")
            
            # Check for problems
            problem_specs = ['ToC509006008', '3.2 D']
            found_problems = [spec for spec in specs.keys() if any(problem.lower() in spec.lower() for problem in problem_specs)]
            
            if found_problems:
                print(f"❌ Found problem specs: {found_problems}")
            else:
                print("✅ No problem specs found")
        else:
            print(f"Error: {response.text}")
            
else:
    print(f"Login failed: {login_response.text}")