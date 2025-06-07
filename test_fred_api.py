#!/usr/bin/env python3
"""
Test script to verify FRED API integration
"""

import requests
import json
from datetime import datetime, timedelta

# Test the FRED API endpoints
BASE_URL = "http://127.0.0.1:8001"

def test_fred_endpoints():
    print("🧪 Testing FRED API Integration")
    print("=" * 50)
    
    # Test 1: Economic Indicators
    print("\n1. Testing Economic Indicators endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/fred/economic-indicators/")
        if response.status_code == 200:
            data = response.json()
            series_data = data.get('data', {}).get('series', {})
            print(f"✅ Success! Found {len(series_data)} economic indicators")
            if series_data:
                for series_id, info in list(series_data.items())[:3]:  # Show first 3
                    print(f"   {series_id}: {info.get('description', 'No description')}")
        else:
            print(f"❌ Failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Series Data (GDP)
    print("\n2. Testing Series Data endpoint (GDP)...")
    try:
        params = {
            'series_id': 'GDP',
            'frequency': 'q',
            'start_date': '2020-01-01',
            'end_date': '2024-12-31'
        }
        response = requests.get(f"{BASE_URL}/api/fred/series/", params=params)
        if response.status_code == 200:
            data = response.json()
            observations = data.get('data', {}).get('observations', [])
            print(f"✅ Success! Found {len(observations)} GDP observations")
            if observations:
                latest = observations[-1]
                print(f"   Latest GDP: {latest.get('value')} on {latest.get('date')}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Multiple Series
    print("\n3. Testing Multiple Series endpoint...")
    try:
        params = {
            'series_ids': 'UNRATE,FEDFUNDS',
            'frequency': 'm',
            'start_date': '2023-01-01',
            'end_date': '2024-12-31'
        }
        response = requests.get(f"{BASE_URL}/api/fred/multiple-series/", params=params)
        if response.status_code == 200:
            data = response.json()
            series_data = data.get('data', {})
            print(f"✅ Success! Retrieved {len(series_data)} series")
            for series_id, series_info in series_data.items():
                obs_count = len(series_info.get('observations', []))
                print(f"   {series_id}: {obs_count} observations")
        else:
            print(f"❌ Failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Search
    print("\n4. Testing Search endpoint...")
    try:
        params = {
            'query': 'unemployment',
            'limit': 5
        }
        response = requests.get(f"{BASE_URL}/api/fred/search/", params=params)
        if response.status_code == 200:
            data = response.json()
            results = data.get('data', [])
            print(f"✅ Success! Found {len(results)} search results")
            for result in results[:3]:  # Show first 3
                print(f"   {result.get('id')}: {result.get('title')}")
        else:
            print(f"❌ Failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 FRED API Integration Test Complete!")

if __name__ == "__main__":
    test_fred_endpoints()
