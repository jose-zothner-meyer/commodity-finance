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
        
    def get_historical(self, commodity: str, interval: str = "1d") -> Dict[str, Any]:
        """
        Fetch historical commodity data from Alpha Vantage.
        
        Args:
            commodity (str): The commodity symbol (e.g., 'WTI', 'BRENT', 'NATURAL_GAS')
            interval (str): Time period (1d, 1w, 1mo)
        """
        base = "https://www.alphavantage.co/query?function={commodity}&interval={interval}&apikey=demo"
        intervalMapping = {"1d": "daily", "1w": "weekly", "1mo": "monthly", "3m": "quarterly", "1y": "annual"}
        url = base.format(commodity=commodity, interval=intervalMapping[interval])
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not data:
            return {"dates": [], "values": []}
        data = data["data"]
        dates = []
        values = []
        for obj in data:
            dates.append(obj["date"])
            values.append(obj["value"])
        return {"dates": dates, "values": values}