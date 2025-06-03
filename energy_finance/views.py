import time
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta, timezone
import json
import logging
from django.views.decorators.csrf import csrf_exempt
import requests
import yaml
import os
import xml.etree.ElementTree as ET
import traceback
import sys
import numpy as np
from typing import List, Dict, Any, Tuple

from energy_finance.constants import SUPPORTED_NAMES, DataSource
from .data_ingest import (
    PowerPriceAPIClient,
    APINinjasCommodityClient,
    FMPCommoditiesClient,
    CommodityPriceAPIClient,
    OpenWeatherAPIClient,
    AlphaVantageAPIClient
)
from .oscillators import (
    calculate_rsi,
    calculate_macd,
    calculate_stochastic,
    calculate_cci,
    calculate_williams_r
)
from django.core.cache import cache
from django.shortcuts import render

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FMP symbol mapping (only supported ones)
FMP_SYMBOLS = {
    "GCUSD": "GCUSD",  # Gold
    "SIUSD": "SIUSD",  # Silver
    "BZUSD": "BZUSD",  # Brent Crude Oil
    "ESUSD": "ESUSD"   # Wheat
}

def parse_date(date_str):
    """Parse date string to datetime object"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

def error_response(endpoint, error_type, message, params=None, details=None, exc=None, status=500):
    """Helper function to create error responses"""
    response_data = {
        "error": message,
        "type": error_type,
        "endpoint": endpoint
    }
    if params:
        response_data["params"] = params
    if details:
        response_data["details"] = details
    if exc:
        response_data["traceback"] = traceback.format_exc()
    return JsonResponse(response_data, status=status)

@require_http_methods(["GET"])
def get_commodities(request):
    """Get historical commodity prices from selected source with robust validation and error handling."""
    endpoint = "get_commodities"
    try:
        try:
            commodities_file_path = os.path.join(os.path.dirname(__file__), '..', 'commodities_by_source.json')
            with open(commodities_file_path) as f:
                valid_commodities = json.load(f) if commodities_file_path.endswith('.json') else yaml.safe_load(f)
        except Exception as e:
            valid_commodities = {}

        source = request.GET.get('source')
        commodity = request.GET.get('name')
        start = request.GET.get('start')
        end = request.GET.get('end')
        period = request.GET.get('period', '1d')
        interval = request.GET.get('interval', '1d')
        valid_sources = ['api_ninjas', 'fmp', 'commodity_price_api', 'alpha_vantage']
        params = dict(request.GET)

        if not source or source not in valid_sources:
            return error_response(endpoint, "validation", f"Invalid or missing data source: '{source}'", params=params, details=f"Supported sources: {valid_sources}", status=400)
        if not commodity:
            return error_response(endpoint, "validation", f"Invalid or missing commodity for selected source: '{commodity}'", params=params, details=f"Supported commodities for {source}: {valid_commodities.get(source, [])}", status=400)
        if not start or not end:
            return error_response(endpoint, "validation", "Start and end dates are required.", params=params, details=f"Received start='{start}', end='{end}'", status=400)
        try:
            if start:
                datetime.strptime(start, '%Y-%m-%d')
            if end:
                datetime.strptime(end, '%Y-%m-%d')
            if start and end:
                start_date = datetime.strptime(start, '%Y-%m-%d')
                end_date = datetime.strptime(end, '%Y-%m-%d')
                if start_date > end_date:
                    return error_response(endpoint, "validation", "Start date must be before end date.", params=params, details=f"start='{start}', end='{end}'", status=400)
        except Exception as e:
            return error_response(endpoint, "validation", "Invalid date format for start or end. Use YYYY-MM-DD.", params=params, details=f"Received start='{start}', end='{end}'. Error: {e}", status=400)

        results = {"dates": [], "prices": []}
        oscillator = request.GET.get('oscillator', 'none')

        try:
            if source == 'api_ninjas':
                try:
                    client = APINinjasCommodityClient()
                except ValueError as e:
                    return error_response(endpoint, "config", str(e), params=params, status=500)
                url = f"https://api.api-ninjas.com/v1/commoditypricehistorical"
                params_api = {"name": commodity, "period": period, "start": start, "end": end}
                r = requests.get(url, params=params_api, headers=client.headers)
                if r.status_code == 400:
                    return error_response(endpoint, "vendor", "Invalid request to API Ninjas.", params=params, details=r.text, status=400)
                if r.status_code == 401:
                    return error_response(endpoint, "vendor", "Unauthorized. Check your API Ninjas key.", params=params, details=r.text, status=401)
                r.raise_for_status()
                data = r.json()
                for entry in data:
                    results["dates"].append(datetime.fromtimestamp(entry["time"], timezone.utc).strftime('%Y-%m-%d'))
                    results["prices"].append(entry["close"])

            elif source == 'fmp':
                try:
                    client = FMPCommoditiesClient()
                except ValueError as e:
                    return error_response(endpoint, "config", str(e), params=params, status=500)
                symbol = commodity
                endpoint_url = f"/historical-price-full/{symbol}"
                params_api = {"from": start, "to": end}
                try:
                    data = client.get(endpoint_url, params=params_api)
                except requests.exceptions.RequestException as e:
                    return error_response(endpoint, "vendor", "Failed to fetch data from vendor.", params=params, details=str(e), exc=e, status=502)
                if not data or 'historical' not in data:
                    return error_response(endpoint, "vendor", "No data returned from FMP.", params=params, status=404)
                for entry in data.get("historical", []):
                    results["dates"].append(entry["date"])
                    results["prices"].append(entry["close"])

            elif source == 'commodity_price_api':
                try:
                    client = CommodityPriceAPIClient()
                except ValueError as e:
                    return error_response(endpoint, "config", str(e), params=params, status=500)
                
                try:
                    data = client.get_historical(commodity, start, end, period)
                    if not data or 'data' not in data:
                        return error_response(endpoint, "vendor", 'No price data available for the specified date range', params=params, status=404)
                    
                    results = {
                        "dates": [],
                        "prices": []
                    }
                    
                    for entry in data['data']:
                        results["dates"].append(entry["date"])
                        results["prices"].append(float(entry["price"]))
                    
                    # Calculate oscillator if requested
                    if oscillator != 'none' and len(results["prices"]) > 0:
                        osc_values = []
                        if oscillator == 'rsi':
                            osc_values = calculate_rsi(results["prices"])
                        elif oscillator == 'macd':
                            macd, signal, hist = calculate_macd(results["prices"])
                            osc_values = macd  # You might want to return all three series
                        elif oscillator == 'stochastic':
                            # For stochastic, we need high and low prices
                            high_prices = [float(entry.get("high", entry["price"])) for entry in data['data']]
                            low_prices = [float(entry.get("low", entry["price"])) for entry in data['data']]
                            osc_values = calculate_stochastic(results["prices"], high_prices, low_prices)
                        elif oscillator == 'cci':
                            high_prices = [float(entry.get("high", entry["price"])) for entry in data['data']]
                            low_prices = [float(entry.get("low", entry["price"])) for entry in data['data']]
                            osc_values = calculate_cci(results["prices"], high_prices, low_prices)
                        elif oscillator == 'williamsr':
                            high_prices = [float(entry.get("high", entry["price"])) for entry in data['data']]
                            low_prices = [float(entry.get("low", entry["price"])) for entry in data['data']]
                            osc_values = calculate_williams_r(results["prices"], high_prices, low_prices)
                    
                    return JsonResponse(results)
                except requests.exceptions.RequestException as e:
                    return error_response(endpoint, "vendor", "Failed to fetch data from vendor.", params=params, details=str(e), exc=e, status=502)
                except Exception as e:
                    return error_response(endpoint, "internal", "Unexpected error occurred during data fetch.", params=params, details=str(e), exc=e, status=500)
            elif source == 'alpha_vantage':
                try:
                    client = AlphaVantageAPIClient()
                except ValueError as e:
                    return error_response(endpoint, "config", str(e), params=params, status=500)
                data = client.get_historical(commodity, start, end, interval)
                return JsonResponse(data)

            else:
                raise ValueError(f"Invalid source: {source}")
        except requests.exceptions.RequestException as e:
            return error_response(endpoint, "vendor", "Failed to fetch data from vendor.", params=params, details=str(e), exc=e, status=502)
        except Exception as e:
            return error_response(endpoint, "internal", "Unexpected error occurred during data fetch.", params=params, details=str(e), exc=e, status=500)

        return JsonResponse(results)
    except Exception as e:
        return error_response(endpoint, "internal", "Internal server error.", params=dict(request.GET), details=str(e), exc=e, status=500)

@require_http_methods(["GET"])
def get_weather(request):
    """Get current weather data for a city using OpenWeather API"""
    try:
        city = request.GET.get('city')
        if not city:
            return JsonResponse({'error': 'City parameter is required'}, status=400)
        # Get coordinates for the city
        client = OpenWeatherAPIClient()
        geocoding_response = client.get_geocoding(city)
        if not geocoding_response or not isinstance(geocoding_response, list) or len(geocoding_response) == 0:
            return JsonResponse({'error': f'City not found: {city}'}, status=404)
        location = geocoding_response[0]
        lat = location['lat']
        lon = location['lon']
        # Get current weather data
        try:
            response = client.get_current(lat, lon)
        except Exception as e:
            logger.error(f"Error fetching current weather data for {city}: {str(e)}")
            return JsonResponse({'error': f'Error fetching current weather data: {str(e)}'}, status=500)
        # Process the data
        processed_data = [{
            'date': datetime.utcfromtimestamp(response['dt']).strftime('%Y-%m-%d %H:%M'),
            'temperature': response['main']['temp'],
            'humidity': response['main']['humidity'],
            'pressure': response['main']['pressure'],
            'wind_speed': response['wind']['speed'],
            'description': response['weather'][0]['description'] if 'weather' in response and response['weather'] else 'N/A'
        }]
        return JsonResponse({
            'city': city,
            'coordinates': {'lat': lat, 'lon': lon},
            'data': processed_data
        })
    except Exception as e:
        logger.error(f"Error in get_weather: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_energy(request):
    """Get energy price data from ENTSO-E Transparency Platform (web-api.tp.entsoe.eu)."""
    try:
        market = request.GET.get('market', 'DE-LU')
        start = request.GET.get('start')
        end = request.GET.get('end')
        contract_type = request.GET.get('contract_MarketAgreement.type')
        offset = request.GET.get('offset')
        if not start or not end:
            return error_response("get_energy", "validation", "Missing required parameters: start and end dates are required (YYYY-MM-DD).", params=dict(request.GET), status=400)
        try:
            start_date = datetime.strptime(start, '%Y-%m-%d')
            end_date = datetime.strptime(end, '%Y-%m-%d')
        except Exception as e:
            return error_response("get_energy", "validation", "Invalid date format. Use YYYY-MM-DD.", params=dict(request.GET), details=str(e), status=400)
        if start_date > end_date:
            return error_response("get_energy", "validation", "Start date must be before end date.", params=dict(request.GET), status=400)

        # ENTSO-E area codes
        market_map = {
            'DE-LU': '10Y1001A1001A83F',  # Germany-Luxembourg
            'FR': '10YFR-RTE------C',    # France
            'ES': '10YES-REE------0',    # Spain
            'IT': '10YIT-GRTN-----B',    # Italy
            'AT': '10YAT-APG------L',    # Austria
        }
        domain = market_map.get(market, market)  # Allow direct EIC code as market

        # Format dates as YYYYMMDDHHMM (UTC, 00:00 for start, 23:00 for end)
        period_start = start_date.strftime('%Y%m%d2200')  # 22:00 UTC for ENTSO-E day-ahead
        period_end = end_date.strftime('%Y%m%d2200')

        try:
            client = PowerPriceAPIClient()
        except ValueError as e:
            return error_response("get_energy", "config", str(e), params=dict(request.GET), status=500)

        url = 'https://web-api.tp.entsoe.eu/api'
        params = {
            'documentType': 'A44',
            'in_Domain': domain,
            'out_Domain': domain,
            'periodStart': period_start,
            'periodEnd': period_end,
        }
        if contract_type:
            params['contract_MarketAgreement.type'] = contract_type
        if offset:
            params['offset'] = offset
        r = requests.get(url, params=params, headers=client.headers)
        if r.status_code == 401 or r.status_code == 403:
            return error_response("get_energy", "vendor", "Unauthorized or forbidden. Check your ENTSO-E API token and permissions.", params=dict(request.GET), details=r.text, status=401)
        elif r.status_code == 400:
            return error_response("get_energy", "vendor", "Invalid request to ENTSO-E API.", params=dict(request.GET), details=r.text, status=400)
        r.raise_for_status()

        # Parse XML response
        try:
            root = ET.fromstring(r.content)
            ns = {'ns': 'urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0'}
            timeseries = root.findall('.//ns:TimeSeries', ns)
            if not timeseries:
                return error_response("get_energy", "vendor", "No price data available for the selected period.", params=dict(request.GET), details="The ENTSO-E API returned no time series data.", status=404)
            dates = []
            prices = []
            for ts in timeseries:
                for period in ts.findall('.//ns:Period', ns):
                    start = period.find('ns:timeInterval/ns:start', ns).text
                    points = period.findall('ns:Point', ns)
                    for point in points:
                        price = point.find('ns:price.amount', ns).text
                        position = int(point.find('ns:position', ns).text)
                        dt = datetime.strptime(start, '%Y-%m-%dT%H:%MZ') + timedelta(hours=position-1)
                        dates.append(dt.strftime('%Y-%m-%dT%H:%MZ'))
                        prices.append(float(price))
            if not dates or not prices:
                return error_response("get_energy", "vendor", "No price data available for the selected period.", params=dict(request.GET), details="The parsed data contains no valid price points.", status=404)
            return JsonResponse({"dates": dates, "prices": prices})
        except ET.ParseError as e:
            return error_response("get_energy", "internal", "Failed to parse ENTSO-E response.", params=dict(request.GET), details=f"XML parsing error: {str(e)}", exc=e, status=500)
        except Exception as e:
            return error_response("get_energy", "internal", "Failed to process ENTSO-E data.", params=dict(request.GET), details=str(e), exc=e, status=500)
    except Exception as e:
        return error_response("get_energy", "internal", "Internal server error.", params=dict(request.GET), details=str(e), exc=e, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_commodities_list(request):
    source = request.GET.get('source', 'api_ninjas')
    import os
    import json as pyjson
    json_path = os.path.join(os.path.dirname(__file__), '..', 'commodities_by_source.json')
    print(f"DEBUG: commodities_by_source.json path: {json_path}")
    with open(json_path) as f:
        data = pyjson.load(f)
    print(f"DEBUG: loaded commodities_by_source.json: {data}")
    print(f"DEBUG: requested source: {source}")
    return JsonResponse({"commodities": data.get(source, [])})

@require_http_methods(["GET"])
def get_available_symbols_by_data_source(request):
    """Get all available commodity symbols from the specified data source with caching"""
    source = request.GET.get('source')
    
    # Try to get from cache first
    cache_key = f'{source}_commodity_symbols'
    cached_symbols = cache.get(cache_key)
    
    if cached_symbols is not None or []:
        return JsonResponse(cached_symbols, safe=False)
    
    # If not in cache, fetch from API
    with open('api_keys.yaml', 'r') as f:
        config = yaml.safe_load(f)
        api_key_fmp = config['FIN_MODELING_PREP_KEY']
        api_key_cpa = config['COMMODITYPRICEAPI_KEY']
        api_key = config['API_NINJAS_KEY']
        
    match source:
        case DataSource.FMP.value:
            base_url = 'https://financialmodelingprep.com/api/v3'
            endpoint = f'{base_url}/symbol/available-commodities'
            
            try:
                response = requests.get(
                    endpoint,
                    params={'apikey': api_key_fmp}
                )
                response.raise_for_status()
                symbols = response.json()
                
                # Cache the results for 24 hours (86400 seconds)
                cache.set(cache_key, symbols, timeout=86400)
                
                return JsonResponse(symbols, safe=False)
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching FMP symbols: {e}")
                return JsonResponse({"error": "Failed to fetch symbols"}, status=500)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing FMP symbols response: {e}")
                return JsonResponse({"error": "Invalid response from API"}, status=500)

        case DataSource.COMMODITYPRICEAPI.value:
            endpoint = 'https://api.commoditypriceapi.com/v2/symbols'
            try:
                response = requests.get(
                    endpoint,
                    headers={'x-api-key': api_key_cpa}
                )
                response.raise_for_status()
                data = response.json()
                
                if isinstance(data, dict):
                    if "symbols" in data:
                        cache.set(cache_key, data["symbols"], timeout=86400)
                        return JsonResponse(data["symbols"], safe=False)
                    elif "data" in data:
                        return JsonResponse(data["data"], safe=False)
                elif isinstance(data, list):
                    return JsonResponse([{"symbol": s, "name": s} for s in data], safe=False)
                return JsonResponse([], safe=False)
            except Exception as e:
                logger.error(f"Error fetching CommodityPriceAPI symbols: {e}")
                return JsonResponse([], safe=False)

        case DataSource.API_NINJAS.value:
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
                        logger.error(f"Error for {name}: {response.status_code} {response.text}")
                    time.sleep(0.2)  # Be polite to the API
                except Exception as e:
                    logger.error(f"Error fetching API Ninjas data for {name}: {e}")
                    return JsonResponse({"error": str(e)}, status=400)
            cache.set(cache_key, data, timeout=86400)
            return JsonResponse(data, safe=False)

        case DataSource.ALPHA_VANTAGE.value:
            try:
                client = AlphaVantageAPIClient()
                symbols = client.get_available_commodities()
                # Format symbols to match other sources
                formatted_symbols = [{"symbol": s, "name": s} for s in symbols]
                cache.set(cache_key, formatted_symbols, timeout=86400)
                return JsonResponse(formatted_symbols, safe=False)
            except Exception as e:
                logger.error(f"Error fetching Alpha Vantage symbols: {e}")
                return JsonResponse({"error": str(e)}, status=500)

        case _:
            return JsonResponse({"error": "Invalid source"}, status=400)

def index(request):
    return render(request, 'energy_finance/index.html')

@require_http_methods(["GET"])
def get_commodity_data(request):
    """Get commodity data from Alpha Vantage API"""
    try:
        commodity = request.GET.get('commodity')
        if not commodity:
            return JsonResponse({'error': 'Commodity parameter is required'}, status=400)
        
        client = AlphaVantageAPIClient()
        data = client.get_commodity_data(commodity)
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Error in get_commodity_data: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)  