#!/usr/bin/env python3
"""
Test script to verify that the commodity tracker application is working correctly.
This script tests the complete pipeline from API endpoints to data retrieval.
"""

import requests
import json
import sys
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000"

def test_api_endpoint(url, description):
    """Test an API endpoint and return the result."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS: Received {len(data) if isinstance(data, list) else 'valid'} data")
            if isinstance(data, list) and len(data) > 0:
                print(f"Sample data: {json.dumps(data[0], indent=2)}")
            elif isinstance(data, dict):
                print(f"Data keys: {list(data.keys())}")
            return True, data
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: {e}")
        return False, None

def main():
    """Run comprehensive tests of the commodity tracker system."""
    print("🚀 Starting Commodity Tracker Integration Tests")
    
    # Test 1: Homepage accessibility
    success, _ = test_api_endpoint(f"{BASE_URL}/", "Dashboard Homepage")
    
    # Test 2: FMP commodity symbols
    success, fmp_symbols = test_api_endpoint(
        f"{BASE_URL}/api/params/?source=fmp", 
        "FMP Commodity Symbols"
    )
    
    # Test 3: Alpha Vantage commodity symbols  
    success, av_symbols = test_api_endpoint(
        f"{BASE_URL}/api/params/?source=alpha_vantage", 
        "Alpha Vantage Commodity Symbols"
    )
    
    # Test 4: Commodity data retrieval (Gold)
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    success, gold_data = test_api_endpoint(
        f"{BASE_URL}/api/commodities/?source=fmp&name=GCUSD&start={start_date}&end={end_date}",
        "Gold Price Data (GCUSD)"
    )
    
    # Test 5: Commodity data retrieval (Silver)
    success, silver_data = test_api_endpoint(
        f"{BASE_URL}/api/commodities/?source=fmp&name=SIUSD&start={start_date}&end={end_date}",
        "Silver Price Data (SIUSD)"
    )
    
    # Test 6: Crude Oil data
    success, oil_data = test_api_endpoint(
        f"{BASE_URL}/api/commodities/?source=fmp&name=CLUSD&start={start_date}&end={end_date}",
        "Crude Oil Price Data (CLUSD)"
    )
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    if fmp_symbols:
        print(f"✅ FMP Symbols Available: {len(fmp_symbols)}")
        
    if av_symbols:
        print(f"✅ Alpha Vantage Symbols Available: {len(av_symbols)}")
        
    if gold_data and 'dates' in gold_data and 'prices' in gold_data:
        print(f"✅ Gold Data Points: {len(gold_data['dates'])}")
        print(f"   Latest Gold Price: ${gold_data['prices'][0] if gold_data['prices'] else 'N/A'}")
        
    if silver_data and 'dates' in silver_data and 'prices' in silver_data:
        print(f"✅ Silver Data Points: {len(silver_data['dates'])}")
        print(f"   Latest Silver Price: ${silver_data['prices'][0] if silver_data['prices'] else 'N/A'}")
        
    if oil_data and 'dates' in oil_data and 'prices' in oil_data:
        print(f"✅ Crude Oil Data Points: {len(oil_data['dates'])}")
        print(f"   Latest Oil Price: ${oil_data['prices'][0] if oil_data['prices'] else 'N/A'}")
    
    print(f"\n🎉 Commodity Tracker System Integration Test Complete!")
    print(f"🌐 Dashboard URL: {BASE_URL}")
    
    return True

if __name__ == "__main__":
    main()
