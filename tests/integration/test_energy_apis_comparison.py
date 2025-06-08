#!/usr/bin/env python3
"""
Test script for Energy Charts vs ENTSO-E API comparison
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Add the project root to the Python path
project_root = '/Users/jomeme/Documents/AiCore/projects/Commodity_Tracker/commodity-tracker-1'
sys.path.insert(0, project_root)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.core.data_ingest import PowerPriceAPIClient, EnergyChartsAPIClient
import json
import time

def test_energy_charts_api():
    """Test Energy Charts API functionality"""
    print("=" * 60)
    print("TESTING ENERGY CHARTS API")
    print("=" * 60)
    
    client = EnergyChartsAPIClient()
    end_date = datetime.now() - timedelta(days=2)
    start_date = end_date - timedelta(days=1)
    
    print(f"Testing date range: {start_date.date()} to {end_date.date()}")
    
    # Test price data
    print("\n1. Testing Price Data...")
    price_data = client.get_price_data('DE', start_date, end_date)
    if price_data:
        print(f"✅ Price data retrieved: {len(price_data['dates'])} data points")
        print(f"   Sample values: {price_data['values'][:3]}...")
        print(f"   Data source: {price_data.get('source', 'unknown')}")
    else:
        print("❌ Failed to retrieve price data")
    
    # Test power generation data
    print("\n2. Testing Power Generation Data...")
    gen_data = client.get_power_generation('DE', start_date, end_date)
    if gen_data:
        print(f"✅ Generation data retrieved: {len(gen_data['dates'])} data points")
        print(f"   Generation sources: {list(gen_data['generation_by_source'].keys())}")
        print(f"   Renewable share range: {min(gen_data['renewable_share']):.1f}% - {max(gen_data['renewable_share']):.1f}%")
        print(f"   Data source: {gen_data.get('source', 'unknown')}")
    else:
        print("❌ Failed to retrieve generation data")
    
    # Test load data
    print("\n3. Testing Load Data...")
    load_data = client.get_load_data('DE', start_date, end_date)
    if load_data:
        print(f"✅ Load data retrieved: {len(load_data['dates'])} data points")
        print(f"   Sample load values: {load_data['values'][:3]}...")
        print(f"   Data source: {load_data.get('source', 'unknown')}")
    else:
        print("❌ Failed to retrieve load data")
    
    return {
        'price': price_data is not None,
        'generation': gen_data is not None,
        'load': load_data is not None
    }

def test_entsoe_api():
    """Test ENTSO-E API functionality"""
    print("\n" + "=" * 60)
    print("TESTING ENTSO-E API")
    print("=" * 60)
    
    try:
        client = PowerPriceAPIClient()
        end_date = datetime.now() - timedelta(days=3)  # ENTSO-E needs more delay
        start_date = end_date - timedelta(days=1)
        
        print(f"Testing date range: {start_date.date()} to {end_date.date()}")
        
        # Test price data
        print("\n1. Testing Price Data...")
        price_data = client.get_price_data('DE', start_date, end_date)
        if price_data:
            print(f"✅ Price data retrieved: {len(price_data['dates'])} data points")
            print(f"   Sample values: {price_data['values'][:3]}...")
            print(f"   Data type: {price_data.get('type', 'unknown')}")
        else:
            print("❌ Failed to retrieve price data")
        
        return {'price': price_data is not None}
        
    except Exception as e:
        print(f"❌ ENTSO-E API test failed with error: {str(e)}")
        return {'price': False}

def compare_apis():
    """Compare the performance and capabilities of both APIs"""
    print("\n" + "=" * 60)
    print("API COMPARISON RESULTS")
    print("=" * 60)
    
    # Test Energy Charts
    start_time = time.time()
    energy_charts_results = test_energy_charts_api()
    energy_charts_time = time.time() - start_time
    
    # Test ENTSO-E
    start_time = time.time()
    entsoe_results = test_entsoe_api()
    entsoe_time = time.time() - start_time
    
    # Summary comparison
    print(f"\n🔍 PERFORMANCE COMPARISON:")
    print(f"   Energy Charts API time: {energy_charts_time:.2f} seconds")
    print(f"   ENTSO-E API time: {entsoe_time:.2f} seconds")
    
    print(f"\n📊 CAPABILITY COMPARISON:")
    print(f"   Energy Charts - Price data: {'✅' if energy_charts_results.get('price') else '❌'}")
    print(f"   Energy Charts - Generation data: {'✅' if energy_charts_results.get('generation') else '❌'}")
    print(f"   Energy Charts - Load data: {'✅' if energy_charts_results.get('load') else '❌'}")
    print(f"   ENTSO-E - Price data: {'✅' if entsoe_results.get('price') else '❌'}")
    print(f"   ENTSO-E - Generation data: ❌ (Complex to implement)")
    print(f"   ENTSO-E - Load data: ❌ (Complex to implement)")
    
    print(f"\n🏆 RECOMMENDATION:")
    if energy_charts_results.get('generation') and energy_charts_results.get('price'):
        print("   ✅ Energy Charts API provides superior functionality and performance")
        print("   ✅ Recommend hybrid approach: Energy Charts for enhanced features, ENTSO-E for backup")
    else:
        print("   ⚠️  Mixed results - detailed analysis needed")
    
    return {
        'energy_charts': energy_charts_results,
        'entsoe': entsoe_results,
        'performance': {
            'energy_charts_time': energy_charts_time,
            'entsoe_time': entsoe_time
        }
    }

def test_enhanced_endpoint():
    """Test the enhanced energy endpoint with both APIs"""
    print("\n" + "=" * 60)
    print("TESTING ENHANCED ENERGY ENDPOINT")
    print("=" * 60)
    
    from django.test import Client
    from django.urls import reverse
    
    client = Client()
    
    # Test different data types
    test_cases = [
        {'data_type': 'price', 'description': 'Price Data'},
        {'data_type': 'generation', 'description': 'Generation Data'},
        {'data_type': 'load', 'description': 'Load Data'},
        {'data_type': 'renewable_share', 'description': 'Renewable Share'}
    ]
    
    end_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
    
    for test_case in test_cases:
        print(f"\n🧪 Testing {test_case['description']}...")
        
        try:
            response = client.get('/api/energy/', {
                'country': 'DE',
                'data_type': test_case['data_type'],
                'start': start_date,
                'end': end_date
            })
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success - API: {data.get('api_source', 'unknown')}")
                print(f"   📊 Data points: {len(data.get('dates', []))}")
            else:
                print(f"   ❌ Failed - Status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Energy Charts vs ENTSO-E API Comparison Test")
    print(f"📅 Test date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run comprehensive comparison
    results = compare_apis()
    
    # Test the enhanced endpoint
    test_enhanced_endpoint()
    
    print("\n" + "=" * 60)
    print("✅ TESTING COMPLETED")
    print("=" * 60)
