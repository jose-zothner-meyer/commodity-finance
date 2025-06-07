import requests
import yaml
import time
from typing import List, Dict, Any, Optional
import os
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.config = self._load_config()
        self.headers = {}

    def _load_config(self) -> Dict[str, str]:
        """Load configuration from api_keys.yaml"""
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'api_keys.yaml')
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
                time.sleep(wait_time + 1)  # Add 1 second buffer
        
        # Record this call
        self._api_calls.append(current_time)
    
    def _make_request_with_retry(self, params: dict, max_retries: int = 3) -> dict:
        """Make API request with retry logic and rate limiting"""
        
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

class EnergyChartsAPIClient(APIClient):
    def __init__(self):
        super().__init__("https://api.energy-charts.info")
        # No authentication required for Energy Charts API
    
    def get_price_data(self, country: str, start_dt: datetime, end_dt: datetime):
        """Get electricity price data from Energy Charts API"""
        # Energy Charts uses different country codes
        country_mapping = {
            'DE': 'de',
            'FR': 'fr', 
            'ES': 'es',
            'IT': 'it',
            'AT': 'at',
            'CH': 'ch',
            'NL': 'nl',
            'BE': 'be'
        }
        
        country_code = country_mapping.get(country, country.lower())
        start_date = start_dt.strftime('%Y-%m-%d')
        end_date = end_dt.strftime('%Y-%m-%d')
        
        params = {
            'country': country_code,
            'start': start_date,
            'end': end_date
        }
        
        try:
            response = requests.get(f"{self.base_url}/price", params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'unix_seconds' in data and 'price' in data:
                # Convert unix timestamps to ISO format
                dates = [datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%dT%H:%MZ') 
                        for ts in data['unix_seconds']]
                values = data['price']
                
                return {
                    'dates': dates,
                    'values': values,
                    'type': 'price',
                    'source': 'energy_charts'
                }
            else:
                logger.warning("No price data found in Energy Charts response")
                return None
                
        except requests.RequestException as e:
            logger.error("Error fetching Energy Charts price data: %s", str(e))
            return None
    
    def get_power_generation(self, country: str, start_dt: datetime, end_dt: datetime):
        """Get power generation data by source from Energy Charts API"""
        country_mapping = {
            'DE': 'de',
            'FR': 'fr', 
            'ES': 'es',
            'IT': 'it',
            'AT': 'at'
        }
        
        country_code = country_mapping.get(country, country.lower())
        start_date = start_dt.strftime('%Y-%m-%d')
        end_date = end_dt.strftime('%Y-%m-%d')
        
        params = {
            'country': country_code,
            'start': start_date,
            'end': end_date
        }
        
        try:
            response = requests.get(f"{self.base_url}/public_power", params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'unix_seconds' in data and 'production_types' in data:
                # Convert unix timestamps to ISO format
                dates = [datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%dT%H:%MZ') 
                        for ts in data['unix_seconds']]
                
                # Extract generation data by source
                generation_by_source = {}
                renewable_total = []
                fossil_total = []
                
                for production_type in data['production_types']:
                    name = production_type['name']
                    values = production_type['data']
                    generation_by_source[name] = values
                    
                    # Categorize as renewable or fossil
                    if any(renewable in name.lower() for renewable in 
                           ['wind', 'solar', 'hydro', 'biomass', 'geothermal']):
                        if not renewable_total:
                            renewable_total = [0] * len(values)
                        renewable_total = [r + max(0, v) for r, v in zip(renewable_total, values)]
                    elif any(fossil in name.lower() for fossil in 
                            ['coal', 'gas', 'oil', 'fossil']):
                        if not fossil_total:
                            fossil_total = [0] * len(values)
                        fossil_total = [f + max(0, v) for f, v in zip(fossil_total, values)]
                
                # Calculate renewable share
                total_generation = [r + f for r, f in zip(renewable_total, fossil_total)]
                renewable_share = [
                    (r / t * 100) if t > 0 else 0 
                    for r, t in zip(renewable_total, total_generation)
                ]
                
                return {
                    'dates': dates,
                    'generation_by_source': generation_by_source,
                    'renewable_total': renewable_total,
                    'fossil_total': fossil_total,
                    'renewable_share': renewable_share,
                    'type': 'generation',
                    'source': 'energy_charts'
                }
            else:
                logger.warning("No generation data found in Energy Charts response")
                return None
                
        except requests.RequestException as e:
            logger.error("Error fetching Energy Charts generation data: %s", str(e))
            return None
    
    def get_load_data(self, country: str, start_dt: datetime, end_dt: datetime):
        """Get electricity load/demand data from Energy Charts API"""
        # Load data is included in the public_power endpoint
        generation_data = self.get_power_generation(country, start_dt, end_dt)
        
        if generation_data and 'generation_by_source' in generation_data:
            # Look for load data in the generation sources
            load_data = generation_data['generation_by_source'].get('Load', [])
            if load_data:
                return {
                    'dates': generation_data['dates'],
                    'values': load_data,
                    'type': 'load',
                    'source': 'energy_charts'
                }
        
        return None

class EIAAPIClient(APIClient):
    """
    Energy Information Administration (EIA) API Client for US energy data.
    Provides access to comprehensive US energy statistics including electricity,
    natural gas, petroleum, coal, renewable energy, and nuclear data.
    """
    
    def __init__(self):
        super().__init__("https://api.eia.gov/v2")
        api_key = self.config.get('EIA_API_KEY')
        if not api_key:
            raise ValueError("EIA API key missing in config")
        self.api_key = api_key
        self.headers = {
            'X-Params': f'{{"api_key": "{self.api_key}"}}'
        }
        
        # Import cache here to avoid circular imports
        try:
            from django.core.cache import cache
            self.cache = cache
        except ImportError:
            self.cache = None
    
    def _make_eia_request(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        """Make EIA API request with proper authentication and error handling"""
        if params is None:
            params = {}
        
        # Add API key to params
        params['api_key'] = self.api_key
        
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params, headers={'Accept': 'application/json'}, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error("EIA API request failed: %s", str(e))
            return None
    
    def get_electricity_generation_by_source(self, state: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        Get electricity generation by energy source for US states or national level.
        
        Args:
            state: State abbreviation (e.g., 'CA', 'TX') or None for national data
            start_date: Start date in YYYY-MM format
            end_date: End date in YYYY-MM format
        """
        cache_key = f'eia_generation_{state}_{start_date}_{end_date}'
        
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
        
        # Use EIA electricity generation data series
        if state:
            # State-level data
            endpoint = f"electricity/electric-power-operational-data/data"
            params = {
                'frequency': 'monthly',
                'data[0]': 'generation',
                'facets[stateid][]': state,
                'sort[0][column]': 'period',
                'sort[0][direction]': 'desc',
                'offset': 0,
                'length': 5000
            }
        else:
            # National data
            endpoint = f"electricity/electric-power-operational-data/data"
            params = {
                'frequency': 'monthly',
                'data[0]': 'generation',
                'sort[0][column]': 'period',
                'sort[0][direction]': 'desc',
                'offset': 0,
                'length': 5000
            }
        
        if start_date:
            params['start'] = start_date
        if end_date:
            params['end'] = end_date
        
        data = self._make_eia_request(endpoint, params)
        
        if data and 'response' in data and 'data' in data['response']:
            generation_data = data['response']['data']
            
            # Process the data by energy source
            result = self._process_generation_data(generation_data)
            
            # Cache for 1 hour
            if self.cache:
                self.cache.set(cache_key, result, timeout=3600)
            
            return result
        
        return None
    
    def get_electricity_prices(self, region: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        Get electricity wholesale prices for US regions.
        
        Args:
            region: Region code (e.g., 'CAL', 'TEX', 'FLA') or None for national average
            start_date: Start date in YYYY-MM format
            end_date: End date in YYYY-MM format
        """
        cache_key = f'eia_prices_{region}_{start_date}_{end_date}'
        
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
        
        # EIA electricity price data
        endpoint = "electricity/retail-sales/data"
        params = {
            'frequency': 'monthly',
            'data[0]': 'price',
            'sort[0][column]': 'period',
            'sort[0][direction]': 'desc',
            'offset': 0,
            'length': 5000
        }
        
        if region:
            params['facets[stateid][]'] = region
        
        if start_date:
            params['start'] = start_date
        if end_date:
            params['end'] = end_date
        
        data = self._make_eia_request(endpoint, params)
        
        if data and 'response' in data and 'data' in data['response']:
            price_data = data['response']['data']
            
            # Process price data
            result = self._process_price_data(price_data)
            
            # Cache for 1 hour
            if self.cache:
                self.cache.set(cache_key, result, timeout=3600)
            
            return result
        
        return None
    
    def get_natural_gas_data(self, data_type: str = 'production', start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        Get natural gas production, consumption, or price data.
        
        Args:
            data_type: 'production', 'consumption', or 'price'
            start_date: Start date in YYYY-MM format
            end_date: End date in YYYY-MM format
        """
        cache_key = f'eia_natural_gas_{data_type}_{start_date}_{end_date}'
        
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
        
        # Natural gas data endpoints
        if data_type == 'production':
            endpoint = "natural-gas/prod/sum/data"
            data_param = 'value'
        elif data_type == 'consumption':
            endpoint = "natural-gas/cons/sum/data"
            data_param = 'value'
        else:  # price
            endpoint = "natural-gas/pri/sum/data"
            data_param = 'value'
        
        params = {
            'frequency': 'monthly',
            'data[0]': data_param,
            'sort[0][column]': 'period',
            'sort[0][direction]': 'desc',
            'offset': 0,
            'length': 5000
        }
        
        if start_date:
            params['start'] = start_date
        if end_date:
            params['end'] = end_date
        
        data = self._make_eia_request(endpoint, params)
        
        if data and 'response' in data and 'data' in data['response']:
            result = self._process_natural_gas_data(data['response']['data'])
            
            # Cache for 1 hour
            if self.cache:
                self.cache.set(cache_key, result, timeout=3600)
            
            return result
        
        return None
    
    def get_renewable_energy_data(self, source: str = 'all', start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        Get renewable energy generation data by source.
        
        Args:
            source: 'solar', 'wind', 'hydro', 'geothermal', 'biomass', or 'all'
            start_date: Start date in YYYY-MM format
            end_date: End date in YYYY-MM format
        """
        cache_key = f'eia_renewable_{source}_{start_date}_{end_date}'
        
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
        
        # Renewable energy data
        endpoint = "electricity/electric-power-operational-data/data"
        params = {
            'frequency': 'monthly',
            'data[0]': 'generation',
            'sort[0][column]': 'period',
            'sort[0][direction]': 'desc',
            'offset': 0,
            'length': 5000
        }
        
        # Filter by renewable energy sources
        if source != 'all':
            renewable_sources = {
                'solar': 'SUN',
                'wind': 'WND',
                'hydro': 'WAT',
                'geothermal': 'GEO',
                'biomass': 'WOO'  # Wood and waste biomass
            }
            if source in renewable_sources:
                params['facets[fueltypeid][]'] = renewable_sources[source]
        else:
            # All renewable sources
            params['facets[fueltypeid][]'] = ['SUN', 'WND', 'WAT', 'GEO', 'WOO']
        
        if start_date:
            params['start'] = start_date
        if end_date:
            params['end'] = end_date
        
        data = self._make_eia_request(endpoint, params)
        
        if data and 'response' in data and 'data' in data['response']:
            result = self._process_renewable_data(data['response']['data'])
            
            # Cache for 1 hour
            if self.cache:
                self.cache.set(cache_key, result, timeout=3600)
            
            return result
        
        return None
    
    def get_petroleum_data(self, product: str = 'crude_oil', data_type: str = 'production', start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        Get petroleum production, consumption, imports, exports, or price data.
        
        Args:
            product: 'crude_oil', 'gasoline', 'heating_oil', 'diesel'
            data_type: 'production', 'consumption', 'imports', 'exports', 'price'
            start_date: Start date in YYYY-MM format
            end_date: End date in YYYY-MM format
        """
        cache_key = f'eia_petroleum_{product}_{data_type}_{start_date}_{end_date}'
        
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
        
        # Petroleum data endpoints - using supply and disposition data
        endpoint = "petroleum/sum/snd/data"
        params = {
            'frequency': 'monthly',
            'data[0]': 'value',
            'sort[0][column]': 'period',
            'sort[0][direction]': 'desc',
            'offset': 0,
            'length': 5000
        }
        
        if start_date:
            params['start'] = start_date
        if end_date:
            params['end'] = end_date
        
        data = self._make_eia_request(endpoint, params)
        
        if data and 'response' in data and 'data' in data['response']:
            result = self._process_petroleum_data(data['response']['data'])
            
            # Cache for 1 hour
            if self.cache:
                self.cache.set(cache_key, result, timeout=3600)
            
            return result
        
        return None
    
    def _process_generation_data(self, raw_data: list) -> dict:
        """Process electricity generation data from EIA response"""
        generation_by_source = {}
        dates = []
        
        for item in raw_data:
            period = item.get('period')
            fuel_type = item.get('fueltypeid', 'Unknown')
            value = item.get('generation', 0)
            
            if period not in dates:
                dates.append(period)
            
            if fuel_type not in generation_by_source:
                generation_by_source[fuel_type] = {}
            
            generation_by_source[fuel_type][period] = value
        
        # Convert to time series format
        dates.sort()
        result = {
            'dates': dates,
            'generation_by_source': {},
            'type': 'generation',
            'source': 'eia'
        }
        
        for fuel_type, data in generation_by_source.items():
            values = [data.get(date, 0) for date in dates]
            result['generation_by_source'][fuel_type] = values
        
        return result
    
    def _process_price_data(self, raw_data: list) -> dict:
        """Process electricity price data from EIA response"""
        dates = []
        values = []
        
        for item in raw_data:
            period = item.get('period')
            value = item.get('price', 0)
            
            if period and value is not None:
                dates.append(period)
                values.append(float(value))
        
        # Sort by date
        date_value_pairs = list(zip(dates, values))
        date_value_pairs.sort()
        
        return {
            'dates': [pair[0] for pair in date_value_pairs],
            'values': [pair[1] for pair in date_value_pairs],
            'type': 'price',
            'source': 'eia',
            'unit': 'cents/kWh'
        }
    
    def _process_natural_gas_data(self, raw_data: list) -> dict:
        """Process natural gas data from EIA response"""
        dates = []
        values = []
        
        for item in raw_data:
            period = item.get('period')
            value = item.get('value', 0)
            
            if period and value is not None:
                dates.append(period)
                values.append(float(value))
        
        # Sort by date
        date_value_pairs = list(zip(dates, values))
        date_value_pairs.sort()
        
        return {
            'dates': [pair[0] for pair in date_value_pairs],
            'values': [pair[1] for pair in date_value_pairs],
            'type': 'natural_gas',
            'source': 'eia'
        }
    
    def _process_renewable_data(self, raw_data: list) -> dict:
        """Process renewable energy data from EIA response"""
        renewable_by_source = {}
        dates = []
        
        renewable_mapping = {
            'SUN': 'Solar',
            'WND': 'Wind',
            'WAT': 'Hydro',
            'GEO': 'Geothermal',
            'WOO': 'Biomass'
        }
        
        for item in raw_data:
            period = item.get('period')
            fuel_type = item.get('fueltypeid', 'Unknown')
            value = item.get('generation', 0)
            
            if period not in dates:
                dates.append(period)
            
            source_name = renewable_mapping.get(fuel_type, fuel_type)
            
            if source_name not in renewable_by_source:
                renewable_by_source[source_name] = {}
            
            renewable_by_source[source_name][period] = value
        
        # Convert to time series format
        dates.sort()
        result = {
            'dates': dates,
            'renewable_by_source': {},
            'type': 'renewable_generation',
            'source': 'eia'
        }
        
        for source, data in renewable_by_source.items():
            values = [data.get(date, 0) for date in dates]
            result['renewable_by_source'][source] = values
        
        return result
    
    def _process_petroleum_data(self, raw_data: list) -> dict:
        """Process petroleum data from EIA response"""
        dates = []
        values = []
        
        for item in raw_data:
            period = item.get('period')
            value = item.get('value', 0)
            
            if period and value is not None:
                dates.append(period)
                values.append(float(value))
        
        # Sort by date
        date_value_pairs = list(zip(dates, values))
        date_value_pairs.sort()
        
        return {
            'dates': [pair[0] for pair in date_value_pairs],
            'values': [pair[1] for pair in date_value_pairs],
            'type': 'petroleum',
            'source': 'eia'
        }

class FREDAPIClient(APIClient):
    """
    Federal Reserve Economic Data (FRED) API Client for US economic indicators.
    Provides access to comprehensive US economic data including GDP, inflation,
    unemployment, interest rates, money supply, and other macroeconomic indicators.
    """
    
    def __init__(self):
        super().__init__("https://api.stlouisfed.org/fred")
        api_key = self.config.get('FRED_API_KEY')
        if not api_key:
            raise ValueError("FRED API key missing in config")
        self.api_key = api_key
        
        # Import cache here to avoid circular imports
        try:
            from django.core.cache import cache
            self.cache = cache
        except ImportError:
            self.cache = None
    
    def _make_fred_request(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        """Make FRED API request with proper authentication and error handling"""
        if params is None:
            params = {}
        
        # Add API key and default format
        params['api_key'] = self.api_key
        params['file_type'] = 'json'
        
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error("FRED API request failed: %s", str(e))
            return None
    
    def get_series_data(self, series_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[dict]:
        """
        Get economic data for a specific FRED series.
        
        Args:
            series_id: FRED series ID (e.g., 'GDP', 'UNRATE', 'CPIAUCSL')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        """
        cache_key = f'fred_series_{series_id}_{start_date}_{end_date}'
        
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
        
        params = {}
        if start_date:
            params['observation_start'] = start_date
        if end_date:
            params['observation_end'] = end_date
        
        # Get series observations
        data = self._make_fred_request(f'series/observations', {
            'series_id': series_id,
            **params
        })
        
        if data and 'observations' in data:
            result = self._process_series_data(data['observations'], series_id)
            
            # Cache for 1 hour
            if self.cache:
                self.cache.set(cache_key, result, timeout=3600)
            
            return result
        
        return None
    
    def get_multiple_series(self, series_ids: List[str], start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[dict]:
        """
        Get data for multiple economic series.
        
        Args:
            series_ids: List of FRED series IDs
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        """
        results = {}
        
        for series_id in series_ids:
            data = self.get_series_data(series_id, start_date, end_date)
            if data:
                results[series_id] = data
        
        return results if results else None
    
    def get_economic_indicators(self, category: str = 'general', start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[dict]:
        """
        Get common economic indicators by category.
        
        Args:
            category: Category of indicators ('general', 'employment', 'inflation', 'monetary', 'trade', 'energy')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        """
        # Define common economic indicator series by category
        indicator_categories = {
            'general': {
                'GDP': 'Gross Domestic Product',
                'GDPC1': 'Real GDP',
                'UNRATE': 'Unemployment Rate',
                'CPIAUCSL': 'Consumer Price Index',
                'FEDFUNDS': 'Federal Funds Rate'
            },
            'employment': {
                'UNRATE': 'Unemployment Rate',
                'PAYEMS': 'Total Nonfarm Payrolls',
                'CIVPART': 'Labor Force Participation Rate',
                'EMRATIO': 'Employment-Population Ratio',
                'AWHMAN': 'Average Weekly Hours of Production Workers'
            },
            'inflation': {
                'CPIAUCSL': 'Consumer Price Index',
                'CPILFESL': 'Core CPI',
                'DFEDTARU': 'Federal Reserve Inflation Target',
                'T5YIE': '5-Year Breakeven Inflation Rate',
                'T10YIE': '10-Year Breakeven Inflation Rate'
            },
            'monetary': {
                'FEDFUNDS': 'Federal Funds Rate',
                'DGS10': '10-Year Treasury Rate',
                'DGS2': '2-Year Treasury Rate',
                'M2SL': 'M2 Money Supply',
                'BOGMBASE': 'Monetary Base'
            },
            'trade': {
                'BOPGSTB': 'Trade Balance: Goods and Services',
                'IMPGS': 'Imports of Goods and Services',
                'EXPGS': 'Exports of Goods and Services',
                'DEXUSEU': 'US / Euro Foreign Exchange Rate',
                'DEXCHUS': 'China / US Foreign Exchange Rate'
            },
            'energy': {
                'DCOILWTICO': 'Crude Oil Prices: West Texas Intermediate',
                'DCOILBRENTEU': 'Crude Oil Prices: Brent - Europe',
                'DHHNGSP': 'Henry Hub Natural Gas Spot Price',
                'DGENEUKUS': 'US Petroleum and Natural Gas Extraction Output',
                'TOTALSA': 'Total Vehicle Sales'
            }
        }
        
        if category not in indicator_categories:
            return None
        
        series_data = {}
        series_info = indicator_categories[category]
        
        for series_id, description in series_info.items():
            data = self.get_series_data(series_id, start_date, end_date)
            if data:
                data['description'] = description
                series_data[series_id] = data
        
        return {
            'category': category,
            'series': series_data,
            'source': 'fred',
            'timestamp': datetime.now().isoformat()
        } if series_data else None
    
    def get_series_info(self, series_id: str) -> Optional[dict]:
        """Get metadata information for a FRED series."""
        data = self._make_fred_request('series', {'series_id': series_id})
        
        if data and 'seriess' in data and data['seriess']:
            series_info = data['seriess'][0]
            return {
                'id': series_info.get('id'),
                'title': series_info.get('title'),
                'units': series_info.get('units'),
                'frequency': series_info.get('frequency'),
                'seasonal_adjustment': series_info.get('seasonal_adjustment'),
                'last_updated': series_info.get('last_updated'),
                'notes': series_info.get('notes')
            }
        
        return None
    
    def search_series(self, search_text: str, limit: int = 20) -> Optional[List[dict]]:
        """Search for FRED series by text."""
        data = self._make_fred_request('series/search', {
            'search_text': search_text,
            'limit': limit,
            'order_by': 'popularity'
        })
        
        if data and 'seriess' in data:
            return [{
                'id': series.get('id'),
                'title': series.get('title'),
                'units': series.get('units'),
                'frequency': series.get('frequency'),
                'last_updated': series.get('last_updated')
            } for series in data['seriess']]
        
        return None
    
    def _process_series_data(self, observations: list, series_id: str) -> dict:
        """Process FRED series observations into structured data"""
        processed_observations = []
        
        for obs in observations:
            # Skip missing values (marked as '.')
            if obs.get('value') != '.' and obs.get('value') is not None:
                try:
                    processed_observations.append({
                        'date': obs['date'],
                        'value': obs['value']
                    })
                except (ValueError, TypeError):
                    continue
        
        return {
            'series_id': series_id,
            'observations': processed_observations,
            'count': len(processed_observations),
            'source': 'fred',
            'type': 'economic_indicator'
        }