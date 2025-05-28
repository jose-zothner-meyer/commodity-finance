# target return : [
#         { symbol: 'GC', name: 'Gold' },
#         { symbol: 'CL', name: 'Crude Oil' },
#         { symbol: 'NG', name: 'Natural Gas' },
#         { symbol: 'SI', name: 'Silver' },
#         { symbol: 'PL', name: 'Platinum' }
#     ],

# Call financial modelling prep api endpoint
# return data that looks like above ^
# call endpoint in dashboard.js code 

import requests
import json
import yaml
from datetime import datetime, timedelta

def get_available_symbols():
    """Get all available commodity symbols from FMP API"""
    with open('api_keys.yaml', 'r') as f:
        config = yaml.safe_load(f)
        api_key = config['FIN_MODELING_PREP_KEY']
    
    base_url = 'https://financialmodelingprep.com/api/v3'
    endpoint = f'{base_url}/symbol/available-commodities'
    
    try:
        response = requests.get(
            endpoint,
            params={'apikey': api_key}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching symbols: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing symbols response: {e}")
        return None

def test_fmp_api_call(symbol='GC', start_date=None, end_date=None):
    """
    Test call to Financial Modeling Prep API for historical commodity data
    
    Args:
        symbol (str): Commodity symbol (e.g., 'GC' for Gold)
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
    """
    # Load API key from config
    with open('api_keys.yaml', 'r') as f:
        config = yaml.safe_load(f)
        api_key = config['FIN_MODELING_PREP_KEY']
    
    # Set default dates if not provided
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    # Construct API URL
    base_url = 'https://financialmodelingprep.com/api/v3'
    endpoint = f'{base_url}/historical-price-full/{symbol}'
    
    # Make API request
    try:
        response = requests.get(
            endpoint,
            params={
                'apikey': api_key,
                'from': start_date,
                'to': end_date
            }
        )
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        
        # Format data for frontend
        formatted_data = {
            'dates': [],
            'prices': [],
            'source': 'fmp',
            'symbol': symbol
        }
        
        if 'historical' in data:
            for entry in data['historical']:
                formatted_data['dates'].append(entry['date'])
                formatted_data['prices'].append(entry['close'])
        
        return formatted_data
        
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing API response: {e}")
        return None

if __name__ == "__main__":
    # First, get all available symbols
    print("Fetching available commodity symbols...")
    symbols = get_available_symbols()
    
    if symbols:
        print("\nAvailable Commodity Symbols:")
        print("----------------------------")
        for symbol in symbols:
            print(f"Symbol: {symbol['symbol']:<6} Name: {symbol['name']}")
        
        # Test the API call with the first symbol
        if symbols:
            first_symbol = symbols[0]['symbol']
            print(f"\nTesting API call with symbol: {first_symbol}")
            result = test_fmp_api_call(first_symbol, '2024-01-01', '2024-01-31')
            if result:
                print("\nAPI Call Successful!")
                print(f"Number of data points: {len(result['dates'])}")
                print("Sample data:")
                print(json.dumps(result, indent=2))
            else:
                print("\nAPI Call Failed!")
    else:
        print("Failed to fetch available symbols")
