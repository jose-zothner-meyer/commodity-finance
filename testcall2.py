# target return : [
#         { symbol: 'GC', name: 'Gold' },
#         { symbol: 'CL', name: 'Crude Oil' },
#         { symbol: 'NG', name: 'Natural Gas' },
#         { symbol: 'SI', name: 'Silver' },
#         { symbol: 'PL', name: 'Platinum' }
#     ],

# Call commodity price api endpoint
# return data that looks like above ^
# call endpoint in dashboard.js code 

import requests
import json
import yaml
from datetime import datetime, timedelta

def get_available_symbols():
    """Dynamically fetch all available commodity symbols from CommodityPriceAPI"""
    with open('api_keys.yaml', 'r') as f:
        config = yaml.safe_load(f)
        api_key = config['COMMODITYPRICEAPI_KEY']

    endpoint = 'https://api.commoditypriceapi.com/v2/symbols'
    try:
        response = requests.get(
            endpoint,
            headers={'x-api-key': api_key}
        )
        response.raise_for_status()
        data = response.json()
        print("Raw symbols response:", data)  # Debug print
        # Try to extract the correct list
        if isinstance(data, dict):
            if "symbols" in data:
                return data["symbols"]
            elif "data" in data:
                return data["data"]
        elif isinstance(data, list):
            # If it's a list of strings, convert to dicts for display
            return [{"symbol": s, "name": s} for s in data]
        return []
    except Exception as e:
        print(f"Error fetching symbols: {e}")
        return []

def test_commodity_price_api_call(symbol='XAU', date='2024-01-04'):
    """
    Test call to Commodity Price API for historical commodity data
    Args:
        symbol (str): Commodity symbol (e.g., 'XAU' for Gold)
        date (str): Date in YYYY-MM-DD format
    """
    with open('api_keys.yaml', 'r') as f:
        config = yaml.safe_load(f)
        api_key = config['COMMODITYPRICEAPI_KEY']

    base_url = 'https://api.commoditypriceapi.com/v2'
    endpoint = f'{base_url}/rates/historical'
    try:
        response = requests.get(
            endpoint,
            headers={'x-api-key': api_key},
            params={
                'symbols': symbol,
                'date': date
            }
        )
        response.raise_for_status()
        data = response.json()
        print(json.dumps(data, indent=2))
        return data
    except Exception as e:
        print(f"Error making API request: {e}")
        return None

if __name__ == "__main__":
    symbols = get_available_symbols()
    if symbols:
        print("Available Commodity Symbols:")
        for symbol in symbols:
            print(f"Symbol: {symbol['symbol']:<10} Name: {symbol['name']}")
        # Test the API call with the first symbol
        first_symbol = symbols[0]['symbol']
        print(f"\nTesting API call with symbol: {first_symbol}")
        test_commodity_price_api_call(first_symbol, '2024-01-04')
    else:
        print("Failed to fetch available symbols") 