#!/usr/bin/env python3
"""
Complete system test for the Commodity Tracker application.
Tests all API endpoints and functionality.
"""

import requests
import json
import sys
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000"

def test_params_endpoint():
    """Test the params endpoint for all data sources"""
    print("🔍 Testing params endpoints...")
    
    sources = ['fmp', 'alpha_vantage', 'api_ninjas']
    results = {}
    
    for source in sources:
        try:
            response = requests.get(f"{BASE_URL}/api/params/", params={'source': source}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results[source] = len(data) if isinstance(data, list) else 0
                print(f"  ✅ {source}: {results[source]} commodities available")
            else:
                print(f"  ❌ {source}: HTTP {response.status_code}")
                results[source] = 0
        except Exception as e:
            print(f"  ❌ {source}: Error - {e}")
            results[source] = 0
    
    return results

def test_commodity_data():
    """Test commodity data endpoints"""
    print("\n💰 Testing commodity data endpoints...")
    
    # Test different commodities and sources
    test_cases = [
        {'source': 'fmp', 'name': 'GCUSD', 'description': 'Gold (FMP)'},
        {'source': 'fmp', 'name': 'SIUSD', 'description': 'Silver (FMP)'},
        {'source': 'fmp', 'name': 'CLUSD', 'description': 'Crude Oil (FMP)'},
    ]
    
    # Use recent dates
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    results = {}
    
    for case in test_cases:
        try:
            params = {
                'source': case['source'],
                'name': case['name'],
                'start': start_date,
                'end': end_date
            }
            
            response = requests.get(f"{BASE_URL}/api/commodities/", params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                dates_count = len(data.get('dates', []))
                prices_count = len(data.get('prices', []))
                
                if dates_count > 0 and prices_count > 0:
                    latest_price = data['prices'][-1] if data['prices'] else 'N/A'
                    print(f"  ✅ {case['description']}: {dates_count} data points, latest price: ${latest_price}")
                    results[case['name']] = {'status': 'success', 'data_points': dates_count, 'latest_price': latest_price}
                else:
                    print(f"  ⚠️  {case['description']}: No data returned")
                    results[case['name']] = {'status': 'no_data', 'data_points': 0}
            else:
                print(f"  ❌ {case['description']}: HTTP {response.status_code} - {response.text[:100]}")
                results[case['name']] = {'status': 'error', 'code': response.status_code}
                
        except Exception as e:
            print(f"  ❌ {case['description']}: Error - {e}")
            results[case['name']] = {'status': 'exception', 'error': str(e)}
    
    return results

def test_dashboard_access():
    """Test dashboard page access"""
    print("\n🖥️  Testing dashboard access...")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            if "Energy Finance Dashboard" in response.text:
                print("  ✅ Dashboard page loads successfully")
                return True
            else:
                print("  ⚠️  Dashboard page loads but title not found")
                return False
        else:
            print(f"  ❌ Dashboard HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Dashboard Error: {e}")
        return False

def main():
    print("🚀 Starting Complete System Test for Commodity Tracker")
    print("=" * 60)
    
    # Run all tests
    params_results = test_params_endpoint()
    commodity_results = test_commodity_data()
    dashboard_ok = test_dashboard_access()
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 60)
    
    total_sources = len(params_results)
    working_sources = sum(1 for count in params_results.values() if count > 0)
    print(f"Data Sources: {working_sources}/{total_sources} working")
    
    total_commodities = len(commodity_results)
    working_commodities = sum(1 for result in commodity_results.values() if result['status'] == 'success')
    print(f"Commodity Data: {working_commodities}/{total_commodities} working")
    
    print(f"Dashboard: {'✅ Working' if dashboard_ok else '❌ Not Working'}")
    
    # Overall status
    if working_sources > 0 and working_commodities > 0 and dashboard_ok:
        print("\n🎉 OVERALL STATUS: ✅ SYSTEM IS WORKING!")
        print("The commodity tracker is successfully loading and displaying data.")
        return 0
    else:
        print("\n⚠️  OVERALL STATUS: ❌ ISSUES DETECTED")
        print("Some components are not working properly.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
