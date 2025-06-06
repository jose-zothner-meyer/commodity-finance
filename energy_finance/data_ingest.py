import requests
import yaml
from typing import List, Dict, Any, Optional
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.config = self._load_config()
        self.headers = {}

    def _load_config(self) -> Dict[str, str]:
        """Load configuration from api_keys.yaml"""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'api_keys.yaml')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except (FileNotFoundError, yaml.YAMLError) as e:
            raise ValueError(f"Failed to load configuration: {str(e)}") from e

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make a GET request to the API"""
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()

# Energy clients
class PowerPriceAPIClient(APIClient):
    def __init__(self):
        super().__init__("https://web-api.tp.entsoe.eu/api")
        token = self.config.get('ENTSOE_TOKEN') or self.config.get('ENTSOE_API_KEY')
        if not token:
            raise ValueError("ENTSO-E API token missing in config")
        # ENTSO-E uses securityToken parameter, not Bearer authentication
        self.security_token = token
        self.headers = {}  # No special headers needed for ENTSO-E
    
    def get_historical(self, area, start, end):
        return self.get("marketdata/dayaheadprices", {"biddingZone": area, "start": start, "end": end})
    
    def get_price_data(self, country: str, start_dt: datetime, end_dt: datetime):
        """Get electricity price data for energy trading analysis"""
        area_codes = {
            'DE': '10Y1001A1001A82H',  # Germany
            'FR': '10YFR-RTE------C',  # France
            'ES': '10YES-REE------0',  # Spain
            'IT': '10YIT-GRTN-----B',  # Italy
            'AT': '10YAT-APG------L',  # Austria
        }
        
        domain = area_codes.get(country, country)
        period_start = start_dt.strftime('%Y%m%d0000')
        period_end = end_dt.strftime('%Y%m%d0000')
        
        params = {
            'documentType': 'A44',  # Price Document (Day-ahead Prices)
            'in_Domain': domain,
            'out_Domain': domain,
            'periodStart': period_start,
            'periodEnd': period_end,
            'securityToken': self.security_token,
        }
        
        try:
            response = requests.get('https://web-api.tp.entsoe.eu/api', params=params, timeout=30)
            response.raise_for_status()
            return self._parse_entso_xml(response.content, 'price')
        except requests.RequestException as e:
            logger.error("Error fetching price data: %s", str(e))
            return None
    
    def get_market_data(self, country: str, start_dt: datetime, end_dt: datetime, data_type: str = 'price'):
        """Get energy market data - currently only price data is reliably available"""
        if data_type == 'price':
            return self.get_price_data(country, start_dt, end_dt)
        else:
            # For now, only price data is reliably available from ENTSO-E
            return self.get_price_data(country, start_dt, end_dt)
    
    def _parse_entso_xml(self, xml_content, data_type):
        """Parse ENTSO-E XML response into structured data"""
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(xml_content)
            
            # Use the correct namespace from the XML response
            ns = {'ns': 'urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3'}
            
            dates = []
            values = []
            
            # Find all TimeSeries elements
            timeseries = root.findall('.//ns:TimeSeries', ns)
            
            if not timeseries:
                logger.warning("No TimeSeries found in XML response")
                return None
            
            for ts in timeseries:
                # Find all Period elements within this TimeSeries
                periods = ts.findall('ns:Period', ns)
                
                for period in periods:
                    # Find the time interval start
                    start_element = period.find('ns:timeInterval/ns:start', ns)
                    if start_element is None or start_element.text is None:
                        continue
                    
                    start = start_element.text
                    
                    # Find all Point elements within this Period
                    points = period.findall('ns:Point', ns)
                    
                    for point in points:
                        quantity_element = point.find('ns:price.amount', ns)  # Correct element name for prices
                        position_element = point.find('ns:position', ns)
                        
                        if quantity_element is None or position_element is None:
                            continue
                        if quantity_element.text is None or position_element.text is None:
                            continue
                        
                        try:
                            quantity = float(quantity_element.text)
                            position = int(position_element.text)
                            # Calculate datetime for this point
                            dt = datetime.strptime(start, '%Y-%m-%dT%H:%MZ') + timedelta(hours=position-1)
                            date_str = dt.strftime('%Y-%m-%dT%H:%MZ')
                            
                            dates.append(date_str)
                            values.append(quantity)
                        except (ValueError, TypeError) as e:
                            logger.debug("Error parsing point data: %s", str(e))
                            continue
            
            if dates and values:
                logger.info("Successfully parsed %d data points from XML", len(dates))
                return {'dates': dates, 'values': values, 'type': data_type}
            else:
                logger.warning("No valid data points found in XML response")
                return None
                
        except (ET.ParseError, ValueError) as e:
            logger.error("Error parsing ENTSO-E XML: %s", str(e))
            return None
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

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
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
        response = requests.get("https://history.openweathermap.org/data/2.5/history/city", params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_geocoding(self, city: str):
        """Get coordinates for a city name"""
        params = {
            "q": city,
            "limit": 1,
            "appid": self.api_key
        }
        response = requests.get("http://api.openweathermap.org/geo/1.0/direct", params=params, timeout=30)
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
        response = requests.get("https://api.openweathermap.org/data/2.5/weather", params=params, timeout=30)
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
        
        # Import cache here to avoid circular imports
        try:
            from django.core.cache import cache
            self.cache = cache
        except ImportError:
            self.cache = None
        
        # Rate limiting - Alpha Vantage has 5 calls per minute for free tier
        self.rate_limit_calls = 5
        self.rate_limit_window = 60  # seconds
        self._api_calls = []

    def _check_rate_limit(self):
        """Check if we're within API rate limits"""
        import time
        current_time = time.time()
        
        # Remove calls older than the rate limit window
        self._api_calls = [call_time for call_time in self._api_calls 
                          if current_time - call_time < self.rate_limit_window]
        
        # Check if we can make another call
        if len(self._api_calls) >= self.rate_limit_calls:
            # Need to wait
            oldest_call = min(self._api_calls)
            wait_time = self.rate_limit_window - (current_time - oldest_call)
            if wait_time > 0:
                import time
                time.sleep(wait_time + 1)  # Add 1 second buffer
        
        # Record this call
        self._api_calls.append(current_time)
    
    def _make_request_with_retry(self, params: dict, max_retries: int = 3) -> dict:
        """Make API request with retry logic and rate limiting"""
        import time
        
        for attempt in range(max_retries):
            try:
                # Check rate limit before making call
                self._check_rate_limit()
                
                response = requests.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # Check for Alpha Vantage API errors
                if "Error Message" in data:
                    raise ValueError(f"Alpha Vantage API Error: {data['Error Message']}")
                
                if "Note" in data:
                    # Rate limit hit, wait and retry
                    if attempt < max_retries - 1:
                        time.sleep(60)  # Wait 1 minute
                        continue
                    else:
                        raise ValueError(f"Alpha Vantage rate limit exceeded: {data['Note']}")
                
                return data
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    # Wait before retry (exponential backoff)
                    wait_time = (2 ** attempt) * 1
                    time.sleep(wait_time)
                    continue
                else:
                    raise e
        
        raise ValueError("Max retries exceeded")

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
        Returns a list of available commodity symbols from Alpha Vantage with caching.
        Expanded list based on Alpha Vantage API documentation.
        """
        # Create cache key
        cache_key = 'alpha_vantage_available_commodities'
        
        # Try to get from cache first (cache for 24 hours since this rarely changes)
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
        
        commodities = [
            # Energy Commodities
            'WTI',          # West Texas Intermediate Crude Oil
            'BRENT',        # Brent Crude Oil
            'NATURAL_GAS',  # Natural Gas
            'HEATING_OIL',  # Heating Oil
            'GASOLINE',     # Gasoline/RBOB
            
            # Precious Metals  
            'COPPER',       # Copper
            'ALUMINUM',     # Aluminum
            'ZINC',         # Zinc
            'NICKEL',       # Nickel
            'LEAD',         # Lead
            'TIN',          # Tin
            
            # Agricultural Commodities
            'WHEAT',        # Wheat
            'CORN',         # Corn
            'COTTON',       # Cotton
            'SUGAR',        # Sugar
            'COFFEE',       # Coffee
            'COCOA',        # Cocoa
            'RICE',         # Rice
            'OATS',         # Oats
            'SOYBEANS',     # Soybeans
            
            # Additional commodities (if supported by Alpha Vantage)
            'GOLD',         # Gold (if available as direct function)
            'SILVER',       # Silver (if available as direct function)
            'PLATINUM',     # Platinum (if available as direct function)
            'PALLADIUM',    # Palladium (if available as direct function)
        ]
        
        # Cache the results for 24 hours (86400 seconds)
        if self.cache:
            self.cache.set(cache_key, commodities, timeout=86400)
        
        return commodities 
        
    def get_historical(self, commodity: str, interval: str = "1d") -> Dict[str, Any]:
        """
        Fetch historical commodity data from Alpha Vantage with caching.
        
        Args:
            commodity (str): The commodity symbol (e.g., 'WTI', 'BRENT', 'NATURAL_GAS')
            interval (str): Time period (1d, 1w, 1mo)
        """
        # Create cache key
        cache_key = f'alpha_vantage_historical_{commodity}_{interval}'
        
        # Try to get from cache first (cache for 1 hour for Alpha Vantage data)
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
        
        intervalMapping = {"1d": "daily", "1w": "weekly", "1mo": "monthly", "3m": "quarterly", "1y": "annual"}
        params = {
            'function': commodity,
            'interval': intervalMapping.get(interval, "daily"),
            'apikey': self.api_key
        }
        
        # Use retry logic for API calls
        data = self._make_request_with_retry(params)
        
        if not data:
            result = {"dates": [], "values": []}
        else:
            # Check if response contains rate limit information
            if "Information" in data:
                # API rate limit exceeded - return empty result with error info
                print(f"Alpha Vantage API rate limit: {data['Information']}")
                result = {"dates": [], "values": [], "error": "API rate limit exceeded"}
            elif "data" in data:
                # Normal response with data
                data_points = data["data"]
                dates = []
                values = []
                for obj in data_points:
                    dates.append(obj["date"])
                    values.append(obj["value"])
                result = {"dates": dates, "values": values}
            else:
                # Unknown response format
                print(f"Unexpected Alpha Vantage response format: {data}")
                result = {"dates": [], "values": [], "error": "Unexpected API response format"}
        
        # Cache the results for 1 hour (3600 seconds)
        if self.cache:
            self.cache.set(cache_key, result, timeout=3600)
        
        return result

    def get_historical_with_dates(self, commodity: str, start_date: str, end_date: str, interval: str = "1d") -> Dict[str, Any]:
        """
        Fetch historical commodity data from Alpha Vantage with date filtering and caching.
        
        Args:
            commodity (str): The commodity symbol (e.g., 'WTI', 'BRENT', 'NATURAL_GAS')
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            interval (str): Time period (1d, 1w, 1mo)
        
        Returns:
            dict: Historical data with dates and values filtered by date range
        """
        from datetime import datetime
        
        # Create cache key for the filtered data
        cache_key = f'alpha_vantage_filtered_{commodity}_{start_date}_{end_date}_{interval}'
        
        # Try to get from cache first (cache for 30 minutes for filtered data)
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
        
        # Get all historical data first (this will use its own caching)
        all_data = self.get_historical(commodity, interval)
        
        if not all_data or 'dates' not in all_data or not all_data['dates']:
            # Pass through any error information from get_historical
            return all_data if all_data else {"dates": [], "values": []}
        
        # Parse date range
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            # If date parsing fails, return all data
            return all_data
        
        # Filter data by date range
        filtered_dates = []
        filtered_values = []
        
        for i, date_str in enumerate(all_data['dates']):
            try:
                # Parse the date from Alpha Vantage response
                data_dt = datetime.strptime(date_str, '%Y-%m-%d')
                if start_dt <= data_dt <= end_dt:
                    filtered_dates.append(date_str)
                    if i < len(all_data['values']):
                        filtered_values.append(all_data['values'][i])
            except ValueError:
                # Skip invalid dates
                continue
        
        result = {
            "dates": filtered_dates,
            "values": filtered_values
        }
        
        # Cache the filtered results for 30 minutes (1800 seconds)
        if self.cache:
            self.cache.set(cache_key, result, timeout=1800)
        
        return result