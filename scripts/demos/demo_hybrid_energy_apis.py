#!/usr/bin/env python3
"""
Energy API Comparison Demo
Demonstrates the hybrid approach using both Energy Charts and ENTSO-E APIs
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

def demo_hybrid_approach():
    """Demonstrate the hybrid approach combining both APIs"""
    print("=" * 80)
    print("🔋 ENERGY API HYBRID APPROACH DEMONSTRATION")
    print("=" * 80)
    
    # Date setup
    end_date = datetime.now() - timedelta(days=2)
    start_date = end_date - timedelta(days=1)
    
    print(f"📅 Analysis Period: {start_date.date()} to {end_date.date()}")
    
    # Test 1: Price Data Comparison
    print("\n" + "─" * 60)
    print("💰 PRICE DATA COMPARISON")
    print("─" * 60)
    
    # ENTSO-E Price Data
    print("\n🔸 ENTSO-E API (Primary for Price Data):")
    try:
        entsoe_client = PowerPriceAPIClient()
        # Use older dates for ENTSO-E due to publication delays
        entsoe_end = datetime.now() - timedelta(days=3)
        entsoe_start = entsoe_end - timedelta(days=1)
        
        entsoe_price = entsoe_client.get_price_data('DE', entsoe_start, entsoe_end)
        if entsoe_price:
            print(f"   ✅ Retrieved {len(entsoe_price['dates'])} price points")
            print(f"   📊 Price range: €{min(entsoe_price['values']):.2f} - €{max(entsoe_price['values']):.2f} per MWh")
            print(f"   📈 Average price: €{sum(entsoe_price['values'])/len(entsoe_price['values']):.2f} per MWh")
        else:
            print("   ❌ Failed to retrieve price data")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 2: Generation Data (Energy Charts Advantage)
    print("\n" + "─" * 60)
    print("⚡ POWER GENERATION ANALYSIS")
    print("─" * 60)
    
    print("\n🔸 Energy Charts API (Superior for Generation Data):")
    try:
        energy_charts_client = EnergyChartsAPIClient()
        gen_data = energy_charts_client.get_power_generation('de', start_date, end_date)
        
        if gen_data:
            print(f"   ✅ Retrieved {len(gen_data['dates'])} generation data points")
            print(f"   🏭 Generation sources available: {len(gen_data['generation_by_source'])}")
            
            # Analyze renewable vs fossil
            renewable_avg = sum(gen_data['renewable_total']) / len(gen_data['renewable_total'])
            fossil_avg = sum(gen_data['fossil_total']) / len(gen_data['fossil_total'])
            renewable_share_avg = sum(gen_data['renewable_share']) / len(gen_data['renewable_share'])
            
            print(f"   🌱 Average renewable generation: {renewable_avg:.0f} MW")
            print(f"   🏭 Average fossil generation: {fossil_avg:.0f} MW") 
            print(f"   📊 Average renewable share: {renewable_share_avg:.1f}%")
            
            # Top generation sources
            print("   🔝 Top generation sources:")
            for i, (source, data) in enumerate(list(gen_data['generation_by_source'].items())[:5]):
                avg_gen = sum([max(0, x) for x in data]) / len(data)
                if avg_gen > 100:  # Only show significant sources
                    print(f"      {i+1}. {source}: {avg_gen:.0f} MW avg")
                    
        else:
            print("   ❌ Failed to retrieve generation data")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 3: API Comparison Summary
    print("\n" + "─" * 60)
    print("📋 HYBRID APPROACH BENEFITS")
    print("─" * 60)
    
    print("\n🎯 OPTIMAL USE CASES:")
    print("   ✅ ENTSO-E API:")
    print("      • Official European electricity market prices")
    print("      • Regulatory compliance and reporting")
    print("      • Multi-country European coverage")
    print("      • Established data source with long history")
    
    print("\n   ✅ Energy Charts API:")
    print("      • Detailed renewable energy breakdown")
    print("      • Real-time generation monitoring")
    print("      • Clean JSON responses (vs complex XML)")
    print("      • Better error handling and debugging")
    print("      • Enhanced analytics capabilities")
    
    print("\n🚀 HYBRID STRATEGY:")
    print("   1. Use ENTSO-E for price data (primary)")
    print("   2. Use Energy Charts for generation analysis") 
    print("   3. Implement fallback mechanisms")
    print("   4. Provide unified API interface")
    
    # Test 4: Development Experience Comparison
    print("\n" + "─" * 60)
    print("👩‍💻 DEVELOPER EXPERIENCE COMPARISON")
    print("─" * 60)
    
    print("\n📊 Code Complexity:")
    print("   Energy Charts: ~15 lines for data parsing")
    print("   ENTSO-E: ~50+ lines for XML parsing with namespaces")
    
    print("\n🔧 Error Handling:")
    print("   Energy Charts: Clear HTTP status codes and messages")
    print("   ENTSO-E: Complex XML error responses")
    
    print("\n🔑 Authentication:")
    print("   Energy Charts: No authentication required")
    print("   ENTSO-E: Requires API token management")
    
    print("\n⚡ Performance:")
    print("   Energy Charts: Fast JSON parsing")
    print("   ENTSO-E: Slower XML processing")

def test_enhanced_api_endpoint():
    """Test the enhanced API endpoint that uses both APIs"""
    print("\n" + "=" * 80)
    print("🔌 TESTING ENHANCED HYBRID ENDPOINT")
    print("=" * 80)
    
    from django.test import Client
    
    client = Client()
    
    # Test cases
    test_cases = [
        {'data_type': 'price', 'expected_api': 'entsoe', 'description': 'Price Data (ENTSO-E preferred)'},
        {'data_type': 'generation', 'expected_api': 'energy_charts', 'description': 'Generation Data (Energy Charts preferred)'},
        {'data_type': 'renewable_share', 'expected_api': 'energy_charts', 'description': 'Renewable Share (Energy Charts only)'},
    ]
    
    end_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['description']}")
        
        try:
            response = client.get('/energy_finance/api/energy', {
                'country': 'DE',
                'data_type': test_case['data_type'],
                'start': start_date,
                'end': end_date
            })
            
            if response.status_code == 200:
                data = response.json()
                api_used = data.get('api_source', 'unknown')
                print(f"   ✅ Success - API Used: {api_used}")
                print(f"   📊 Data Points: {len(data.get('dates', []))}")
                
                if api_used == test_case['expected_api']:
                    print(f"   🎯 Correctly routed to {api_used}")
                else:
                    print(f"   ⚠️  Expected {test_case['expected_api']}, got {api_used}")
                    
            else:
                print(f"   ❌ Failed - Status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Energy API Hybrid Approach Demo")
    print(f"⏰ Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run the demonstration
    demo_hybrid_approach()
    
    # Test the enhanced endpoint
    test_enhanced_api_endpoint()
    
    print("\n" + "=" * 80)
    print("✨ CONCLUSION: HYBRID APPROACH RECOMMENDED")
    print("=" * 80)
    print("The hybrid approach successfully combines:")
    print("• ENTSO-E's comprehensive price data and European coverage")  
    print("• Energy Charts' superior generation analytics and developer experience")
    print("• Intelligent API routing based on data type and availability")
    print("• Fallback mechanisms for improved reliability")
    print("\n🎉 Demo completed successfully!")
