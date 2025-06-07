#!/usr/bin/env python3
"""
Energy Analyst Dashboard Test - ENTSO-E Data Types
Testing various ENTSO-E data types that energy analysts actually use
"""
import requests
import yaml
from datetime import datetime, timedelta

# Load API configuration
with open('api_keys.yaml', 'r') as f:
    config = yaml.safe_load(f)

api_key = config.get('ENTSOE_API_KEY')
base_url = "https://web-api.tp.entsoe.eu/api"

# Common parameters for EU markets
domains = {
    'DE_LU': '10Y1001A1001A82H',  # Germany-Luxembourg
    'FR': '10YFR-RTE------C',     # France
    'ES': '10YES-REE------0',     # Spain
    'IT_NORD': '10Y1001A1001A73I', # Italy North
}

# Document types that energy analysts commonly use
doc_types = {
    'A65': 'System total load forecast',
    'A71': 'Generation forecast - wind offshore',
    'A69': 'Generation forecast - wind onshore', 
    'A70': 'Generation forecast - solar',
    'A73': 'Actual generation per type',
    'A75': 'Actual generation',
    'A11': 'Net position (imports/exports)',
    'A61': 'Unavailability of generation units',
    'A78': 'Unavailability of production units',
}

def test_entso_data_type(doc_type, domain, description):
    """Test a specific ENTSO-E data type"""
    # Use yesterday's data (more likely to be available)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)
    
    params = {
        'securityToken': api_key,
        'documentType': doc_type,
        'in_Domain': domain,
        'periodStart': start_date.strftime('%Y%m%d0000'),
        'periodEnd': end_date.strftime('%Y%m%d0000'),
    }
    
    # For generation data, we also need out_Domain
    if doc_type in ['A73', 'A75']:
        params['out_Domain'] = domain
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        print(f"\n{description} ({doc_type}) for {domain}:")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            # Check if we got actual data
            content = response.text
            if 'No matching data found' in content:
                print("✗ No data available")
            elif '<TimeSeries>' in content:
                # Count how many time series we got
                series_count = content.count('<TimeSeries>')
                print(f"✓ SUCCESS - {series_count} time series found")
                
                # Extract some sample data points if available
                if '<quantity>' in content:
                    quantities = []
                    start_idx = 0
                    for i in range(min(3, series_count)):  # Get first 3 data points
                        qty_start = content.find('<quantity>', start_idx)
                        if qty_start != -1:
                            qty_end = content.find('</quantity>', qty_start)
                            if qty_end != -1:
                                qty = content[qty_start+10:qty_end]
                                quantities.append(qty)
                                start_idx = qty_end
                    
                    if quantities:
                        print(f"  Sample values: {', '.join(quantities[:3])}")
                        
            else:
                print("? Unknown response format")
                
        elif response.status_code == 401:
            print("✗ Authentication failed")
        elif response.status_code == 400:
            print(f"✗ Bad request: {response.text[:200]}")
        else:
            print(f"✗ Error {response.status_code}")
            
    except Exception as e:
        print(f"✗ Exception: {e}")

def main():
    print("=== ENTSO-E Data Availability Test for Energy Analysts ===")
    print(f"API Key: {'✓ Available' if api_key else '✗ Missing'}")
    
    # Test the most useful data types for energy analysts
    test_domain = domains['DE_LU']  # Start with Germany-Luxembourg
    
    print(f"\nTesting data for Germany-Luxembourg market:")
    
    for doc_type, description in doc_types.items():
        test_entso_data_type(doc_type, test_domain, description)
    
    print("\n=== Summary ===")
    print("Based on results above, we'll build dashboard with available data types")

if __name__ == "__main__":
    main()
