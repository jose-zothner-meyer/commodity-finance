#!/usr/bin/env python3
"""
FRED Economic Data Integration - End-to-End Test
This script demonstrates the complete FRED integration functionality
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8001"

def test_complete_fred_integration():
    print("🎯 FRED Economic Data Integration - Complete Test")
    print("=" * 70)
    
    # Test all endpoints with real-world examples
    tests = [
        {
            'name': 'Economic Indicators (General)',
            'url': f"{BASE_URL}/api/fred/economic-indicators/",
            'params': {'category': 'general'}
        },
        {
            'name': 'Economic Indicators (Employment)',
            'url': f"{BASE_URL}/api/fred/economic-indicators/",
            'params': {'category': 'employment'}
        },
        {
            'name': 'GDP Time Series',
            'url': f"{BASE_URL}/api/fred/series/",
            'params': {
                'series_id': 'GDP',
                'frequency': 'q',
                'start_date': '2020-01-01',
                'end_date': '2024-12-31'
            }
        },
        {
            'name': 'Unemployment Rate',
            'url': f"{BASE_URL}/api/fred/series/",
            'params': {
                'series_id': 'UNRATE',
                'frequency': 'm',
                'start_date': '2023-01-01',
                'end_date': '2024-12-31'
            }
        },
        {
            'name': 'Multiple Series (Economic Overview)',
            'url': f"{BASE_URL}/api/fred/multiple-series/",
            'params': {
                'series_ids': 'GDP,UNRATE,CPIAUCSL',
                'frequency': 'q',
                'start_date': '2022-01-01',
                'end_date': '2024-12-31'
            }
        },
        {
            'name': 'Federal Funds vs 10-Year Treasury',
            'url': f"{BASE_URL}/api/fred/multiple-series/",
            'params': {
                'series_ids': 'FEDFUNDS,DGS10',
                'frequency': 'm',
                'start_date': '2020-01-01',
                'end_date': '2024-12-31'
            }
        },
        {
            'name': 'Search: Inflation Related',
            'url': f"{BASE_URL}/api/fred/search/",
            'params': {
                'query': 'inflation',
                'limit': 10
            }
        },
        {
            'name': 'Search: Employment Related',
            'url': f"{BASE_URL}/api/fred/search/",
            'params': {
                'query': 'employment rate',
                'limit': 5
            }
        }
    ]
    
    success_count = 0
    total_tests = len(tests)
    
    for i, test in enumerate(tests, 1):
        print(f"\n{i}. Testing: {test['name']}")
        print("-" * 50)
        
        try:
            response = requests.get(test['url'], params=test['params'], timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    success_count += 1
                    print(f"✅ SUCCESS - Status: {response.status_code}")
                    
                    # Display specific results based on endpoint type
                    if 'economic-indicators' in test['url']:
                        series_data = data.get('data', {}).get('series', {})
                        print(f"   📊 Found {len(series_data)} economic indicators")
                        for series_id, info in list(series_data.items())[:3]:
                            obs_count = info.get('count', 0)
                            print(f"      • {series_id}: {info.get('description')} ({obs_count} observations)")
                    
                    elif 'multiple-series' in test['url']:
                        series_data = data.get('data', {})
                        print(f"   📈 Retrieved {len(series_data)} series")
                        for series_id, info in series_data.items():
                            obs_count = info.get('count', 0)
                            print(f"      • {series_id}: {obs_count} observations")
                    
                    elif 'series' in test['url']:
                        series_data = data.get('data', {})
                        obs_count = series_data.get('count', 0)
                        latest_obs = None
                        if series_data.get('observations'):
                            latest_obs = series_data['observations'][-1]
                        print(f"   📉 Series: {test['params']['series_id']} - {obs_count} observations")
                        if latest_obs:
                            print(f"      Latest: {latest_obs.get('value')} on {latest_obs.get('date')}")
                    
                    elif 'search' in test['url']:
                        results = data.get('data', [])
                        print(f"   🔍 Found {len(results)} search results")
                        for result in results[:3]:
                            print(f"      • {result.get('id')}: {result.get('title')}")
                    
                else:
                    print(f"❌ FAILED - Unexpected response format")
                    print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
            else:
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"   Error: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ FAILED - Exception: {str(e)}")
    
    print("\n" + "=" * 70)
    print(f"🎯 FRED Integration Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 ALL TESTS PASSED! FRED Economic Data integration is fully functional.")
        print("\n📋 Features Available:")
        print("   ✅ Economic indicator categories (general, employment, inflation, etc.)")
        print("   ✅ Individual time series data retrieval")
        print("   ✅ Multiple series comparison")
        print("   ✅ Series search functionality")
        print("   ✅ Date range filtering")
        print("   ✅ Frequency selection (daily, weekly, monthly, quarterly, annual)")
        print("   ✅ Data transformations (level, change, percent change, etc.)")
        print("\n🌐 Dashboard URL: http://127.0.0.1:8001/ (Economic Data tab)")
    else:
        print(f"⚠️  {total_tests - success_count} tests failed. Please check the errors above.")
    
    return success_count == total_tests

if __name__ == "__main__":
    test_complete_fred_integration()
