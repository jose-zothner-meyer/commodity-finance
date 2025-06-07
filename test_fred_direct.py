#!/usr/bin/env python3
"""
Direct FRED API test to verify the API key and basic functionality
"""

import requests
import json

# FRED API configuration
FRED_API_KEY = "eff8f164a493be083561390b0f7da102"
FRED_BASE_URL = "https://api.stlouisfed.org/fred"

def test_fred_direct():
    print("🧪 Testing FRED API directly")
    print("=" * 50)
    
    # Test 1: Get series data for GDP
    print("\n1. Testing GDP series data...")
    try:
        url = f"{FRED_BASE_URL}/series/observations"
        params = {
            'api_key': FRED_API_KEY,
            'file_type': 'json',
            'series_id': 'GDP',
            'limit': 10
        }
        
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            observations = data.get('observations', [])
            print(f"✅ Success! Found {len(observations)} observations")
            if observations:
                latest = observations[-1]
                print(f"   Latest GDP: {latest.get('value')} on {latest.get('date')}")
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get series info for GDP
    print("\n2. Testing GDP series info...")
    try:
        url = f"{FRED_BASE_URL}/series"
        params = {
            'api_key': FRED_API_KEY,
            'file_type': 'json',
            'series_id': 'GDP'
        }
        
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            series = data.get('seriess', [])
            if series:
                info = series[0]
                print(f"✅ Success! GDP series info:")
                print(f"   Title: {info.get('title')}")
                print(f"   Units: {info.get('units')}")
                print(f"   Frequency: {info.get('frequency')}")
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Search for series
    print("\n3. Testing FRED search...")
    try:
        url = f"{FRED_BASE_URL}/series/search"
        params = {
            'api_key': FRED_API_KEY,
            'file_type': 'json',
            'search_text': 'unemployment rate',
            'limit': 5
        }
        
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            series = data.get('seriess', [])
            print(f"✅ Success! Found {len(series)} series")
            for s in series[:3]:  # Show first 3
                print(f"   {s.get('id')}: {s.get('title')}")
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Direct FRED API Test Complete!")

if __name__ == "__main__":
    test_fred_direct()
