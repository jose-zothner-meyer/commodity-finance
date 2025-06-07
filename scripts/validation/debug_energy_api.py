#!/usr/bin/env python3
"""Debug script to test ENTSO-E API directly"""

import requests
from datetime import datetime, timedelta

print("Starting ENTSO-E API debug script...")

try:
    # Load API key
    import yaml
    print("Loading API configuration...")
    with open('api_keys.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    token = config['ENTSOE_API_KEY']
    print("API Token loaded: %s...%s" % (token[:10], token[-4:]))

    # Test parameters - use dates from 2024
    domain = '10Y1001A1001A83F'  # Germany-Luxembourg
    
    # Try a specific date from 2024 that should have data
    test_date = datetime(2024, 12, 1)
    next_date = test_date + timedelta(days=1)

    # Try day-ahead prices (A44) 
    period_start = test_date.strftime('%Y%m%d0000')  # Start at 00:00
    period_end = next_date.strftime('%Y%m%d0000')    # End at 00:00 next day

    url = 'https://web-api.tp.entsoe.eu/api'
    params = {
        'documentType': 'A44',  # Day-ahead prices
        'in_Domain': domain,
        'out_Domain': domain,
        'periodStart': period_start,
        'periodEnd': period_end,
        'securityToken': token,
    }

    print("Testing ENTSO-E API:")
    print("URL: %s" % url)
    print("Parameters: %s" % params)
    print("Period: %s to %s" % (period_start, period_end))
    print()

    response = requests.get(url, params=params, timeout=30)
    print("Status Code: %d" % response.status_code)
    print("Response Length: %d bytes" % len(response.content))
    print()
    
    if response.status_code == 200:
        print("Raw Response (first 1000 chars):")
        print(response.text[:1000])
        print("SUCCESS: Energy API is working!")
        
    else:
        print("Error Response:")
        print(response.text)
        
except Exception as e:
    print("Script failed: %s" % e)
    import traceback
    traceback.print_exc()
