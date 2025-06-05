#!/usr/bin/env python3
"""
Integration test for Kaufman oscillators with different data sources
Tests the complete pipeline from API call to oscillator calculation
"""

import requests
import json
import sys
from datetime import datetime, timedelta

def test_oscillator_api(base_url="http://127.0.0.1:8000"):
    """Test oscillator calculations through the API endpoints"""
    
    # Define test cases
    test_cases = [
        {
            "source": "fmp",
            "name": "GCUSD",  # Gold
            "start": "2024-01-01",
            "end": "2024-02-29",
            "oscillators": ["kama", "price_osc", "momentum", "roc", "efficiency_ratio"]
        },
        {
            "source": "fmp", 
            "name": "SIUSD",  # Silver
            "start": "2024-01-01",
            "end": "2024-02-29",
            "oscillators": ["cci_enhanced", "smi"]
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        source = test_case["source"]
        name = test_case["name"]
        start = test_case["start"]
        end = test_case["end"]
        
        print(f"\n{'='*60}")
        print(f"Testing {source.upper()} - {name}")
        print(f"Date range: {start} to {end}")
        print(f"{'='*60}")
        
        # Test without oscillator first
        url = f"{base_url}/api/commodities"
        params = {
            "source": source,
            "name": name,
            "start": start,
            "end": end
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            print(f"✓ Basic data fetch successful")
            print(f"  - Dates: {len(data.get('dates', []))} points")
            print(f"  - Prices: {len(data.get('prices', []))} points")
            print(f"  - Price range: ${min(data.get('prices', [0])):.2f} - ${max(data.get('prices', [0])):.2f}")
            
            base_result = {
                "source": source,
                "symbol": name,
                "data_points": len(data.get('dates', [])),
                "price_range": f"${min(data.get('prices', [0])):.2f} - ${max(data.get('prices', [0])):.2f}",
                "oscillators": {}
            }
            
        except Exception as e:
            print(f"✗ Basic data fetch failed: {e}")
            continue
        
        # Test each oscillator
        for oscillator in test_case["oscillators"]:
            params["oscillator"] = oscillator
            
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if "oscillator" in data:
                    osc_data = data["oscillator"]
                    osc_values = osc_data.get("values", [])
                    non_zero_values = [v for v in osc_values if v != 0 and str(v) != 'NaN']
                    
                    print(f"  ✓ {oscillator.upper()}: {len(osc_values)} values")
                    print(f"    - Non-zero/NaN values: {len(non_zero_values)}")
                    if non_zero_values:
                        print(f"    - Range: {min(non_zero_values):.4f} to {max(non_zero_values):.4f}")
                    
                    base_result["oscillators"][oscillator] = {
                        "total_values": len(osc_values),
                        "meaningful_values": len(non_zero_values),
                        "success": True
                    }
                else:
                    print(f"  ✗ {oscillator.upper()}: No oscillator data returned")
                    base_result["oscillators"][oscillator] = {"success": False, "error": "No oscillator data"}
                    
            except Exception as e:
                print(f"  ✗ {oscillator.upper()}: {e}")
                base_result["oscillators"][oscillator] = {"success": False, "error": str(e)}
        
        results.append(base_result)
    
    return results

def generate_report(results):
    """Generate a comprehensive test report"""
    print(f"\n{'='*80}")
    print("KAUFMAN OSCILLATORS INTEGRATION TEST REPORT")
    print(f"{'='*80}")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    total_tests = 0
    passed_tests = 0
    
    for result in results:
        print(f"\n📊 {result['source'].upper()} - {result['symbol']}")
        print(f"   Data Points: {result['data_points']}")
        print(f"   Price Range: {result['price_range']}")
        
        for osc_name, osc_result in result["oscillators"].items():
            total_tests += 1
            if osc_result["success"]:
                passed_tests += 1
                status = "✅ PASS"
                details = f"({osc_result['meaningful_values']}/{osc_result['total_values']} meaningful values)"
            else:
                status = "❌ FAIL"
                details = f"({osc_result.get('error', 'Unknown error')})"
            
            print(f"   {osc_name.upper():15} {status} {details}")
    
    print(f"\n{'='*80}")
    print(f"SUMMARY: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
    print(f"{'='*80}")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Kaufman oscillators are working correctly.")
    else:
        print(f"⚠️  {total_tests - passed_tests} tests failed. Check the details above.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    print("🔍 Starting Kaufman Oscillators Integration Test...")
    
    try:
        results = test_oscillator_api()
        success = generate_report(results)
        
        # Save detailed results to file
        with open("oscillator_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n📝 Detailed results saved to oscillator_test_results.json")
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(1)
