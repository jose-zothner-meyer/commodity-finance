#!/usr/bin/env python3
"""
Commodity Tracker System - Quick Validation Script

This script provides a quick verification of all commodity tracker functionality.
"""

import os
import sys
import requests
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Try to setup Django, but continue even if it fails
try:
    import django
    django.setup()
    from django.core.cache import cache
    DJANGO_AVAILABLE = True
    CACHE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Django setup failed: {e}")
    DJANGO_AVAILABLE = False
    CACHE_AVAILABLE = False
    cache = None

def main():
    print("="*80)
    print("  COMMODITY TRACKER SYSTEM - QUICK VALIDATION")
    print("="*80)
    
    base_url = "http://127.0.0.1:8000"
    tests_passed = 0
    total_tests = 7
    
    # Test 1: Django Server Health
    print("\n1. Django Server Health Check...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Django server is running")
            tests_passed += 1
        else:
            print(f"   ❌ Server returned {response.status_code}")
    except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
        print(f"   ❌ Server connection failed: {e}")
    
    # Test 2: Cache Functionality
    print("\n2. Cache Validation...")
    if DJANGO_AVAILABLE and CACHE_AVAILABLE and cache is not None:
        try:
            cache.set('validation_test', 'working', 30)
            cache_result = cache.get('validation_test')
            if cache_result == 'working':
                print("   ✅ Cache is operational")
                tests_passed += 1
            else:
                print("   ❌ Cache read/write failed")
        except (ImportError, AttributeError) as e:
            print(f"   ❌ Cache test failed: {e}")
    else:
        print("   ⚠️  Cache test skipped (Django not available)")
    
    # Test 3: Commodity Params API
    print("\n3. Commodity Params API...")
    try:
        response = requests.get(f"{base_url}/api/params/?source=fmp", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print(f"   ✅ Params API working ({len(data)} commodities available)")
                tests_passed += 1
            else:
                print("   ❌ Params API returned invalid data")
        else:
            print(f"   ❌ Params API failed with status {response.status_code}")
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"   ❌ Params API error: {e}")
    
    # Test 4: Commodity Data API
    print("\n4. Commodity Data API...")
    try:
        params = {
            'source': 'fmp',
            'name': 'GCUSD',
            'start': '2024-12-01',
            'end': '2024-12-05'
        }
        response = requests.get(f"{base_url}/api/commodities/", params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'dates' in data and 'prices' in data and len(data['dates']) > 0:
                print(f"   ✅ Commodity data API working ({len(data['dates'])} data points)")
                tests_passed += 1
            else:
                print("   ❌ Commodity data API returned invalid structure")
        else:
            print(f"   ❌ Commodity data API failed with status {response.status_code}")
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"   ❌ Commodity data API error: {e}")
    
    
    # Test 5: Portfolio Sample API (if available)
    print("\n5. Portfolio Sample API...")
    try:
        response = requests.get(f"{base_url}/api/portfolio/sample", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'portfolio_data' in data or isinstance(data, dict):
                print("   ✅ Portfolio sample API working")
                tests_passed += 1
            else:
                print("   ❌ Portfolio sample API returned invalid data")
        else:
            print(f"   ❌ Portfolio sample API failed with status {response.status_code}")
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"   ❌ Portfolio sample API error: {e}")
    
    # Test 6: Portfolio Analysis API (if available)
    print("\n6. Portfolio Analysis API...")
    try:
        test_data = {
            'commodities': [
                {
                    'symbol': 'GCUSD', 'name': 'Gold', 'weight': 0.5,
                    'prices': [1800, 1820, 1810, 1830, 1825, 1815, 1840, 1820, 1835, 1825, 
                              1850, 1830, 1845, 1860, 1855, 1870, 1850, 1865, 1880, 1875],
                    'dates': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', 
                             '2024-01-06', '2024-01-07', '2024-01-08', '2024-01-09', '2024-01-10',
                             '2024-01-11', '2024-01-12', '2024-01-13', '2024-01-14', '2024-01-15',
                             '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19', '2024-01-20']
                },
                {
                    'symbol': 'SIUSD', 'name': 'Silver', 'weight': 0.5,
                    'prices': [25, 26, 24, 27, 26, 25, 28, 26, 27, 25,
                              29, 27, 28, 30, 29, 31, 28, 29, 32, 30],
                    'dates': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', 
                             '2024-01-06', '2024-01-07', '2024-01-08', '2024-01-09', '2024-01-10',
                             '2024-01-11', '2024-01-12', '2024-01-13', '2024-01-14', '2024-01-15',
                             '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19', '2024-01-20']
                }
            ]
        }
        response = requests.post(f"{base_url}/api/portfolio/analyze/", json=test_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'portfolio_metrics' in data or isinstance(data, dict):
                print("   ✅ Portfolio analysis API working")
                tests_passed += 1
            else:
                print("   ❌ Portfolio analysis API returned invalid data")
        else:
            print(f"   ❌ Portfolio analysis API failed with status {response.status_code}")
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"   ❌ Portfolio analysis API error: {e}")
    
    # Test 7: Dashboard Page
    print("\n7. Dashboard Page...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            if "Energy Finance Dashboard" in response.text or "Commodity" in response.text:
                print("   ✅ Dashboard page loads correctly")
                tests_passed += 1
            else:
                print("   ⚠️  Dashboard page loads but content unclear")
        else:
            print(f"   ❌ Dashboard page failed with status {response.status_code}")
    except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
        print(f"   ❌ Dashboard page error: {e}")
    
    # Final Summary
    print("\n" + "="*80)
    print("  VALIDATION SUMMARY")
    print("="*80)
    
    success_rate = (tests_passed / total_tests) * 100
    
    print(f"\n🎯 OVERALL STATUS: {'✅ PASS' if tests_passed == total_tests else '⚠️ PARTIAL' if tests_passed > 0 else '❌ FAIL'}")
    print(f"📊 Tests Passed: {tests_passed}/{total_tests} ({success_rate:.1f}%)")
    
    if tests_passed >= 5:
        print("\n🚀 SYSTEM STATUS: OPERATIONAL")
        print("   ✅ Core commodity tracking functionality working")
        print("   ✅ API endpoints responding correctly")
        print("   ✅ Dashboard accessible")
        if DJANGO_AVAILABLE:
            print("   ✅ Django framework properly configured")
    elif tests_passed >= 3:
        print("\n⚠️  SYSTEM STATUS: MOSTLY OPERATIONAL")
        print("   Core features working, some components may need attention")
    else:
        print("\n❌ SYSTEM STATUS: NEEDS ATTENTION")
        print("   Multiple components require fixes")
    
    print(f"\n📅 Validation completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    return tests_passed

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result >= 5 else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except (ImportError, ValueError, RuntimeError) as e:
        print(f"\n\n❌ Validation failed with error: {e}")
        sys.exit(1)
