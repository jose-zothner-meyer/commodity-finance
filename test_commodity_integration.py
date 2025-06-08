#!/usr/bin/env python3
"""
Test script to verify that the commodity tracker application is working correctly.
This script tests the complete pipeline from API endpoints to data retrieval.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union

BASE_URL = "http://127.0.0.1:8000"

def test_api_endpoint(url: str, description: str) -> tuple[bool, Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]]:
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

def main() -> bool:
    """Run comprehensive tests of the commodity tracker system."""
    print("🚀 Starting Commodity Tracker Integration Tests")
    
    # Test 1: Homepage accessibility
    home_success, _ = test_api_endpoint(f"{BASE_URL}/", "Dashboard Homepage")
    
    # Test 2: FMP commodity symbols
    fmp_success, fmp_symbols = test_api_endpoint(
        f"{BASE_URL}/api/params/?source=fmp", 
        "FMP Commodity Symbols"
    )
    
    # Test 3: Alpha Vantage commodity symbols  
    av_success, av_symbols = test_api_endpoint(
        f"{BASE_URL}/api/params/?source=alpha_vantage", 
        "Alpha Vantage Commodity Symbols"
    )
    
    # Test 4: Commodity data retrieval (Gold)
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    gold_success, gold_data = test_api_endpoint(
        f"{BASE_URL}/api/commodities/?source=fmp&name=GCUSD&start={start_date}&end={end_date}",
        "Gold Price Data (GCUSD)"
    )
    
    # Test 5: Commodity data retrieval (Silver)
    silver_success, silver_data = test_api_endpoint(
        f"{BASE_URL}/api/commodities/?source=fmp&name=SIUSD&start={start_date}&end={end_date}",
        "Silver Price Data (SIUSD)"
    )
    
    # Test 6: Crude Oil data
    oil_success, oil_data = test_api_endpoint(
        f"{BASE_URL}/api/commodities/?source=fmp&name=CLUSD&start={start_date}&end={end_date}",
        "Crude Oil Price Data (CLUSD)"
    )
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    if fmp_symbols and isinstance(fmp_symbols, list):
        print(f"✅ FMP Symbols Available: {len(fmp_symbols)}")
        
    if av_symbols and isinstance(av_symbols, list):
        print(f"✅ Alpha Vantage Symbols Available: {len(av_symbols)}")
        
    if gold_data and isinstance(gold_data, dict) and 'dates' in gold_data and 'prices' in gold_data:
        print(f"✅ Gold Data Points: {len(gold_data['dates'])}")
        prices = gold_data['prices']
        if prices and len(prices) > 0:
            print(f"   Latest Gold Price: ${prices[0]}")
        else:
            print("   Latest Gold Price: N/A")
        
    if silver_data and isinstance(silver_data, dict) and 'dates' in silver_data and 'prices' in silver_data:
        print(f"✅ Silver Data Points: {len(silver_data['dates'])}")
        prices = silver_data['prices']
        if prices and len(prices) > 0:
            print(f"   Latest Silver Price: ${prices[0]}")
        else:
            print("   Latest Silver Price: N/A")
        
    if oil_data and isinstance(oil_data, dict) and 'dates' in oil_data and 'prices' in oil_data:
        print(f"✅ Crude Oil Data Points: {len(oil_data['dates'])}")
        prices = oil_data['prices']
        if prices and len(prices) > 0:
            print(f"   Latest Oil Price: ${prices[0]}")
        else:
            print("   Latest Oil Price: N/A")
    
    print("\n🎉 Commodity Tracker System Integration Test Complete!")
    print(f"🌐 Dashboard URL: {BASE_URL}")
    
    # Return overall success status
    tests_passed = all([
        home_success,
        fmp_success or av_success,  # At least one data source should work
        gold_success or silver_success or oil_success  # At least one commodity should work
    ])
    
    return tests_passed

if __name__ == "__main__":
    main()
