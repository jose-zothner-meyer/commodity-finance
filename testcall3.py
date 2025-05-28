import requests
import json
import yaml
import time
from datetime import datetime, timedelta

# List of supported commodity names from API Ninjas docs
# https://api-ninjas.com/api/commodityprice
SUPPORTED_NAMES = [
    "gold",
    "platinum",
    "lean_hogs",
    "oat",
    "aluminum",
    "soybean_meal",
    "lumber",
    "micro_gold",
    "feeder_cattle",
    "rough_rice",
    "palladium"
]

def test_api_ninjas_historical_call():
    """
    Test call to API Ninjas for historical commodity data
    Args:
        name (str): Commodity name (e.g., 'gold')
        period (str): Time interval (e.g., '1h')
        start (int): Start timestamp (Unix)
        end (int): End timestamp (Unix)
    """
    with open('api_keys.yaml', 'r') as f:
        config = yaml.safe_load(f)
        api_key = config['API_NINJAS_KEY']

    data = []
    base_url = 'https://api.api-ninjas.com/v1/commodityprice'
    for name in SUPPORTED_NAMES:
        try:
            response = requests.get(
                base_url,
                headers={'X-Api-Key': api_key},
                params={'name': name}
            )
            if response.status_code == 200:
                res = response.json()
                data.append(res)
            else:
                print(f"Error for {name}: {response.status_code} {response.text}")
            time.sleep(0.2)  # Be polite to the API
        except Exception as e:
            print(f"Exception for {name}: {e}")

    return data

if __name__ == "__main__":
    data = test_api_ninjas_historical_call()
    print(data)