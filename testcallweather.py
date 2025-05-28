import requests
import sys
from datetime import datetime, timedelta

# Set your test parameters here
CITY = 'London'
START_DATE = '2024-06-01'
END_DATE = '2024-06-02'

API_URL = 'http://localhost:8000/api/weather'


def test_weather(city, start, end):
    params = {
        'city': city,
        'start': start,
        'end': end
    }
    print(f"\nTesting /api/weather with params: {params}")
    try:
        r = requests.get(API_URL, params=params)
        print(f"Status Code: {r.status_code}")
        try:
            data = r.json()
        except Exception as e:
            print("Failed to parse JSON response:", e)
            print("Raw response:", r.text)
            return
        print("Response JSON:")
        print(data)
    except Exception as e:
        print("Request failed:", e)

if __name__ == "__main__":
    # Test with valid parameters
    test_weather(CITY, START_DATE, END_DATE)
    # Test with missing city
    test_weather('', START_DATE, END_DATE)
    # Test with invalid date
    test_weather(CITY, 'bad-date', END_DATE)
    # Test with city that likely doesn't exist
    test_weather('Atlantis', START_DATE, END_DATE) 