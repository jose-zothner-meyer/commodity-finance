import requests
import yaml
from typing import List, Dict, Any
import os

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.config = self._load_config()
        self.headers = {}

    def _load_config(self) -> Dict[str, str]:
        """Load configuration from api_keys.yaml"""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'api_keys.yaml')
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to load configuration: {str(e)}")

    def get(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        """Make a GET request to the API"""
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()

# Energy clients
class PowerPriceAPIClient(APIClient):
    def __init__(self):
        super().__init__("https://web-api.tp.entsoe.eu/api")
        token = self.config.get('ENTSOE_TOKEN') or self.config.get('ENTSOE_API_KEY')
        if not token:
            raise ValueError("ENTSO-E API token missing in config")
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def get_historical(self, area, start, end):
        return self.get("marketdata/dayaheadprices", {"biddingZone": area, "start": start, "end": end})

# Commodity clients
class APINinjasCommodityClient(APIClient):
    def __init__(self):
        super().__init__("https://api.api-ninjas.com/v1")
        api_key = self.config.get('API_NINJAS_KEY')
        if not api_key:
            raise ValueError("API key missing for API Ninjas")
        self.headers = {"X-Api-Key": api_key}
    
    def get_price(self, item: str):
        return self.get("", {"item": item})

class FMPCommoditiesClient(APIClient):
    def __init__(self):
        super().__init__("https://financialmodelingprep.com/api/v3")
        api_key = self.config.get('FIN_MODELING_PREP_KEY')
        if not api_key:
            raise ValueError("API key missing for FMP")
        self.api_key = api_key

    def get(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        if params is None:
            params = {}
        params['apikey'] = self.api_key
        return super().get(endpoint, params)

class CommodityPriceAPIClient(APIClient):
    def __init__(self):
        super().__init__("https://api.commoditypriceapi.com/v1")
        api_key = self.config.get('COMMODITYPRICEAPI_KEY')
        if not api_key:
            raise ValueError("API key missing for CommodityPriceAPI")
        self.api_key = api_key
    
    def get_historical(self, symbol: str, start_date: str, end_date: str, interval: str = "1d"):
        """Get historical commodity prices
        
        Args:
            symbol: Commodity symbol (e.g., XAU, WTIOIL)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            interval: Time interval (1m, 5m, 1h, 1d, 1w, 1mo)
        """
        params = {
            "symbol": symbol,
            "currency": "USD",
            "interval": interval,
            "start_date": start_date,
            "end_date": end_date,
            "api_key": self.api_key
        }
        return self.get("/history", params)

    def get_realtime(self, symbol: str):
        """Get real-time commodity price
        
        Args:
            symbol: Commodity symbol (e.g., XAU, WTIOIL)
        """
        params = {
            "symbol": symbol,
            "currency": "USD",
            "api_key": self.api_key
        }
        return self.get("/latest", params)

class OpenWeatherAPIClient(APIClient):
    def __init__(self, base_url: str = "https://api.openweathermap.org/data/3.0"):
        super().__init__(base_url)
        api_key = self.config.get('OPENWEATHER_API_KEY')
        if not api_key:
            raise ValueError("API key missing for OpenWeather")
        self.api_key = api_key

    def get_historical(self, lat: float, lon: float, start: int, end: int):
        """Get historical weather data for a specific date range using the OpenWeather History API
        Args:
            lat: Latitude
            lon: Longitude
            start: Start unix timestamp (UTC)
            end: End unix timestamp (UTC)
        """
        params = {
            "lat": lat,
            "lon": lon,
            "type": "hour",
            "start": start,
            "end": end,
            "appid": self.api_key
        }
        response = requests.get("https://history.openweathermap.org/data/2.5/history/city", params=params)
        response.raise_for_status()
        return response.json()

    def get_geocoding(self, city: str):
        """Get coordinates for a city name"""
        params = {
            "q": city,
            "limit": 1,
            "appid": self.api_key
        }
        response = requests.get("http://api.openweathermap.org/geo/1.0/direct", params=params)
        response.raise_for_status()
        return response.json()

    def get_current(self, lat: float, lon: float):
        """Get current weather data for a specific location."""
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric"
        }
        response = requests.get("https://api.openweathermap.org/data/2.5/weather", params=params)
        response.raise_for_status()
        return response.json()

class AlphaVantageAPIClient(APIClient):
    def __init__(self):
        super().__init__("https://www.alphavantage.co/query")
        api_key = (self.config.get('ALPHAVANTAGE_API_KEY') or 
                  self.config.get('ALPHA_VANTAGE_KEY') or 
                  self.config.get('ALPHA_VANTAGE_API_KEY'))
        if not api_key:
            raise ValueError("API key missing for Alpha Vantage")
        self.api_key = api_key

    def get_commodity_data(self, commodity: str) -> Dict[str, Any]:
        """
        Fetch commodity data from Alpha Vantage.
        
        Args:
            commodity (str): The commodity symbol (e.g., 'WTI', 'BRENT', 'NATURAL_GAS')
            
        Returns:
            dict: The commodity data response
        """
        params = {
            'function': commodity,
            'apikey': self.api_key
        }
        return self.get("", params)

    def get_available_commodities(self) -> List[str]:
        """
        Returns a list of available commodity symbols.
        """
        return [
            'WTI', 'BRENT', 'NATURAL_GAS', 'COPPER', 'ALUMINUM',
            'WHEAT', 'CORN', 'COTTON', 'SUGAR', 'COFFEE'
        ] 