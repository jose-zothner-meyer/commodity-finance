import requests
import os
import yaml

# Load Alpha Vantage API key from api_keys.yaml
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'api_keys.yaml')
try:
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
        API_KEY = config.get('ALPHAVANTAGE_API_KEY') or config.get('ALPHA_VANTAGE_KEY') or config.get('ALPHA_VANTAGE_API_KEY')
except Exception as e:
    print(f"Failed to load API key from {CONFIG_PATH}: {e}")
    API_KEY = None

# Alpha Vantage endpoint for commodity symbols (use 'physical_currency_list' for FX, but for commodities, use documentation)
# Alpha Vantage does not have a direct endpoint for all commodity symbols, but you can list supported symbols from their documentation or try the 'symbol_search' endpoint.
# We'll try the symbol search for a common commodity and print the result.

BASE_URL = 'https://www.alphavantage.co/query'

# List of direct commodity functions from Alpha Vantage documentation
COMMODITY_FUNCTIONS = [
    'WTI', 'BRENT', 'NATURAL_GAS', 'COPPER', 'ALUMINUM',
    'WHEAT', 'CORN', 'COTTON', 'SUGAR', 'COFFEE'
]

def fetch_commodity(function):
    params = {
        'function': function,
        'apikey': API_KEY
    }
    r = requests.get(BASE_URL, params=params)
    print(f"Request URL: {r.url}")
    print(f"Status Code: {r.status_code}")
    try:
        data = r.json()
        print(f"Response for {function}:")
        print(data)
    except Exception as e:
        print("Failed to parse JSON response:", e)
        print("Raw response:", r.text)

if __name__ == "__main__":
    if not API_KEY:
        print(f"Please set your Alpha Vantage API key in {CONFIG_PATH} (key: ALPHAVANTAGE_API_KEY)")
    else:
        for function in COMMODITY_FUNCTIONS:
            print(f"\nFetching commodity data for: {function}")
            fetch_commodity(function) 