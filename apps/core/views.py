import time
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta, timezone
import json
import logging
from django.views.decorators.csrf import csrf_exempt
import requests
import yaml
import os
import traceback

from apps.core.constants import SUPPORTED_NAMES, DataSource
from apps.core.data_ingest import (
    PowerPriceAPIClient,
    EnergyChartsAPIClient,
    APINinjasCommodityClient,
    FMPCommoditiesClient,
    CommodityPriceAPIClient,
    OpenWeatherAPIClient,
    AlphaVantageAPIClient
)
# Import custom Kaufman oscillators and Ehlers digital signal processing oscillators
from apps.core.oscillators import (
    # Kaufman oscillators
    calculate_kaufman_adaptive_moving_average,
    calculate_price_oscillator,
    calculate_commodity_channel_index_enhanced,
    calculate_momentum_oscillator,
    calculate_rate_of_change_oscillator,
    calculate_stochastic_momentum_index,
    calculate_accumulation_distribution_oscillator,
    calculate_kaufman_efficiency_ratio,
    # Ehlers oscillators
    calculate_ehlers_fisher_transform,
    calculate_ehlers_stochastic_cg,
    calculate_ehlers_super_smoother,
    calculate_ehlers_cycle_period,
    calculate_ehlers_mama,
    calculate_ehlers_sinewave_indicator,
    calculate_ehlers_hilbert_transform
)
# Import portfolio analytics
from apps.core.portfolio import (
    PortfolioAnalyzer,
    MonteCarloSimulator,
    PortfolioOptimizer,
    clean_portfolio_values
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
    except ValueError as exc:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD.") from exc

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
            commodities_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'commodities_by_source.json')
            with open(commodities_file_path, encoding='utf-8') as f:
                valid_commodities = json.load(f) if commodities_file_path.endswith('.json') else yaml.safe_load(f)
        except FileNotFoundError:
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
        except ValueError as e:
            return error_response(endpoint, "validation", "Invalid date format for start or end. Use YYYY-MM-DD.", params=params, details=f"Received start='{start}', end='{end}'. Error: {e}", status=400)

        results: dict = {"dates": [], "prices": []}
        oscillator = request.GET.get('oscillator', 'none')

        try:
            if source == 'api_ninjas':
                try:
                    client = APINinjasCommodityClient()
                except ValueError as e:
                    return error_response(endpoint, "config", str(e), params=params, status=500)
                url = "https://api.api-ninjas.com/v1/commoditypricehistorical"
                params_api = {"name": commodity, "period": period, "start": start, "end": end}
                r = requests.get(url, params=params_api, headers=client.headers, timeout=30)
                if r.status_code == 400:
                    return error_response(endpoint, "vendor", "Invalid request to API Ninjas.", params=params, details=r.text, status=400)
                if r.status_code == 401:
                    return error_response(endpoint, "vendor", "Unauthorized. Check your API Ninjas key.", params=params, details=r.text, status=401)
                r.raise_for_status()
                data = r.json()
                for entry in data:
                    results["dates"].append(datetime.fromtimestamp(entry["time"], timezone.utc).strftime('%Y-%m-%d'))
                    results["prices"].append(entry["close"])
                
                # Calculate Kaufman oscillators if requested for API Ninjas data
                if oscillator != 'none' and len(results["prices"]) > 0:
                    osc_values = []
                    osc_dates = results["dates"]
                    
                    if oscillator == 'kama':
                        osc_values = calculate_kaufman_adaptive_moving_average(results["prices"])
                    elif oscillator == 'price_osc':
                        osc_values = calculate_price_oscillator(results["prices"])
                    elif oscillator == 'cci_enhanced':
                        # For enhanced CCI, we need high and low prices from API Ninjas data
                        high_prices = [float(entry.get("high", entry["close"])) for entry in data]
                        low_prices = [float(entry.get("low", entry["close"])) for entry in data]
                        osc_values = calculate_commodity_channel_index_enhanced(high_prices, low_prices, results["prices"])
                    elif oscillator == 'momentum':
                        osc_values = calculate_momentum_oscillator(results["prices"])
                    elif oscillator == 'roc':
                        osc_values = calculate_rate_of_change_oscillator(results["prices"])
                    elif oscillator == 'smi':
                        high_prices = [float(entry.get("high", entry["close"])) for entry in data]
                        low_prices = [float(entry.get("low", entry["close"])) for entry in data]
                        smi_k, _ = calculate_stochastic_momentum_index(high_prices, low_prices, results["prices"])
                        osc_values = smi_k  # Return %K line
                    elif oscillator == 'efficiency_ratio':
                        osc_values = calculate_kaufman_efficiency_ratio(results["prices"])
                    # Ehlers Digital Signal Processing Oscillators
                    elif oscillator == 'fisher_transform':
                        osc_values = calculate_ehlers_fisher_transform(results["prices"])
                    elif oscillator == 'stochastic_cg':
                        high_prices = [float(entry.get("high", entry["close"])) for entry in data]
                        low_prices = [float(entry.get("low", entry["close"])) for entry in data]
                        osc_values = calculate_ehlers_stochastic_cg(high_prices, low_prices, results["prices"])
                    elif oscillator == 'super_smoother':
                        osc_values = calculate_ehlers_super_smoother(results["prices"])
                    elif oscillator == 'cycle_period':
                        osc_values = calculate_ehlers_cycle_period(results["prices"])
                    elif oscillator == 'mama':
                        mama_values, _ = calculate_ehlers_mama(results["prices"])
                        osc_values = mama_values  # Return MAMA line
                    elif oscillator == 'sinewave':
                        sine_values, _ = calculate_ehlers_sinewave_indicator(results["prices"])
                        osc_values = sine_values  # Return Sine wave
                    elif oscillator == 'hilbert_transform':
                        osc_values = calculate_ehlers_hilbert_transform(results["prices"])
                    
                    # Add oscillator data to results
                    if osc_values:
                        results["oscillator"] = {
                            "values": osc_values,
                            "dates": osc_dates,
                            "name": oscillator.upper()
                        }

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
                
                # Calculate Kaufman oscillators if requested for FMP data
                if oscillator != 'none' and len(results["prices"]) > 0:
                    osc_values = []
                    osc_dates = results["dates"]
                    
                    if oscillator == 'kama':
                        osc_values = calculate_kaufman_adaptive_moving_average(results["prices"])
                    elif oscillator == 'price_osc':
                        osc_values = calculate_price_oscillator(results["prices"])
                    elif oscillator == 'cci_enhanced':
                        # For enhanced CCI, we need high and low prices from FMP data
                        high_prices = [float(entry.get("high", entry["close"])) for entry in data.get("historical", [])]
                        low_prices = [float(entry.get("low", entry["close"])) for entry in data.get("historical", [])]
                        osc_values = calculate_commodity_channel_index_enhanced(high_prices, low_prices, results["prices"])
                    elif oscillator == 'momentum':
                        osc_values = calculate_momentum_oscillator(results["prices"])
                    elif oscillator == 'roc':
                        osc_values = calculate_rate_of_change_oscillator(results["prices"])
                    elif oscillator == 'smi':
                        high_prices = [float(entry.get("high", entry["close"])) for entry in data.get("historical", [])]
                        low_prices = [float(entry.get("low", entry["close"])) for entry in data.get("historical", [])]
                        smi_k, _ = calculate_stochastic_momentum_index(high_prices, low_prices, results["prices"])
                        osc_values = smi_k  # Return %K line
                    elif oscillator == 'efficiency_ratio':
                        osc_values = calculate_kaufman_efficiency_ratio(results["prices"])
                    # Ehlers Digital Signal Processing Oscillators
                    elif oscillator == 'fisher_transform':
                        osc_values = calculate_ehlers_fisher_transform(results["prices"])
                    elif oscillator == 'stochastic_cg':
                        high_prices = [float(entry.get("high", entry["close"])) for entry in data.get("historical", [])]
                        low_prices = [float(entry.get("low", entry["close"])) for entry in data.get("historical", [])]
                        osc_values = calculate_ehlers_stochastic_cg(high_prices, low_prices, results["prices"])
                    elif oscillator == 'super_smoother':
                        osc_values = calculate_ehlers_super_smoother(results["prices"])
                    elif oscillator == 'cycle_period':
                        osc_values = calculate_ehlers_cycle_period(results["prices"])
                    elif oscillator == 'mama':
                        mama_values, _ = calculate_ehlers_mama(results["prices"])
                        osc_values = mama_values  # Return MAMA line
                    elif oscillator == 'sinewave':
                        sine_values, _ = calculate_ehlers_sinewave_indicator(results["prices"])
                        osc_values = sine_values  # Return Sine wave
                    elif oscillator == 'hilbert_transform':
                        osc_values = calculate_ehlers_hilbert_transform(results["prices"])
                    
                    # Add oscillator data to results
                    if osc_values:
                        results["oscillator"] = {
                            "values": osc_values,
                            "dates": osc_dates,
                            "name": oscillator.upper()
                        }

            elif source == 'commodity_price_api':
                try:
                    client = CommodityPriceAPIClient()
                except ValueError as e:
                    return error_response(endpoint, "config", str(e), params=params, status=500)
                
                try:
                    data = client.get_historical(commodity, start, end, period)
                    if not data or 'data' not in data:
                        return error_response(endpoint, "vendor", 'No price data available for the specified date range', params=params, status=404)
                    
                    results: dict = {
                        "dates": [],
                        "prices": []
                    }
                    
                    for entry in data['data']:
                        results["dates"].append(entry["date"])
                        results["prices"].append(float(entry["price"]))
                    
                    # Calculate Kaufman oscillators if requested
                    if oscillator != 'none' and len(results["prices"]) > 0:
                        osc_values = []
                        osc_dates = results["dates"]
                        
                        if oscillator == 'kama':
                            osc_values = calculate_kaufman_adaptive_moving_average(results["prices"])
                        elif oscillator == 'price_osc':
                            osc_values = calculate_price_oscillator(results["prices"])
                        elif oscillator == 'cci_enhanced':
                            # For enhanced CCI, we need high and low prices
                            high_prices = [float(entry.get("high", entry["price"])) for entry in data['data']]
                            low_prices = [float(entry.get("low", entry["price"])) for entry in data['data']]
                            osc_values = calculate_commodity_channel_index_enhanced(high_prices, low_prices, results["prices"])
                        elif oscillator == 'momentum':
                            osc_values = calculate_momentum_oscillator(results["prices"])
                        elif oscillator == 'roc':
                            osc_values = calculate_rate_of_change_oscillator(results["prices"])
                        elif oscillator == 'smi':
                            high_prices = [float(entry.get("high", entry["price"])) for entry in data['data']]
                            low_prices = [float(entry.get("low", entry["price"])) for entry in data['data']]
                            smi_k, _ = calculate_stochastic_momentum_index(high_prices, low_prices, results["prices"])
                            osc_values = smi_k  # Return %K line
                        elif oscillator == 'efficiency_ratio':
                            osc_values = calculate_kaufman_efficiency_ratio(results["prices"])
                        # Ehlers Digital Signal Processing Oscillators
                        elif oscillator == 'fisher_transform':
                            osc_values = calculate_ehlers_fisher_transform(results["prices"])
                        elif oscillator == 'stochastic_cg':
                            high_prices = [float(entry.get("high", entry["price"])) for entry in data['data']]
                            low_prices = [float(entry.get("low", entry["price"])) for entry in data['data']]
                            osc_values = calculate_ehlers_stochastic_cg(high_prices, low_prices, results["prices"])
                        elif oscillator == 'super_smoother':
                            osc_values = calculate_ehlers_super_smoother(results["prices"])
                        elif oscillator == 'cycle_period':
                            osc_values = calculate_ehlers_cycle_period(results["prices"])
                        elif oscillator == 'mama':
                            mama_values, _ = calculate_ehlers_mama(results["prices"])
                            osc_values = mama_values  # Return MAMA line
                        elif oscillator == 'sinewave':
                            sine_values, _ = calculate_ehlers_sinewave_indicator(results["prices"])
                            osc_values = sine_values  # Return Sine wave
                        elif oscillator == 'hilbert_transform':
                            osc_values = calculate_ehlers_hilbert_transform(results["prices"])
                        
                        # Add oscillator data to results
                        if osc_values:
                            results["oscillator"] = {
                                "values": osc_values,
                                "dates": osc_dates,
                                "name": oscillator.upper()
                            }
                    
                    return JsonResponse(results)
                except requests.exceptions.RequestException as e:
                    return error_response(endpoint, "vendor", "Failed to fetch data from vendor.", params=params, details=str(e), exc=e, status=502)
                except ValueError as e:
                    return error_response(endpoint, "internal", "Unexpected error occurred during data fetch.", params=params, details=str(e), exc=e, status=500)
            elif source == 'alpha_vantage':
                try:
                    client = AlphaVantageAPIClient()
                except ValueError as e:
                    return error_response(endpoint, "config", str(e), params=params, status=500)
                
                try:
                    # Get historical data with date filtering support
                    data = client.get_historical_with_dates(commodity, start, end, interval)
                    
                    # Check if the response contains an error (e.g., rate limit exceeded)
                    if data and 'error' in data:
                        return error_response(endpoint, "vendor", data['error'], params=params, status=429)
                    
                    if not data or 'dates' not in data or not data['dates']:
                        return error_response(endpoint, "vendor", 'No price data available for the specified date range', params=params, status=404)
                    
                    results = {
                        "dates": data['dates'],
                        "prices": data['values']
                    }
                    
                    # Calculate oscillators if requested for Alpha Vantage data
                    if oscillator != 'none' and len(results["prices"]) > 0:
                        osc_values = []
                        osc_dates = results["dates"]
                        
                        # Kaufman Oscillators
                        if oscillator == 'kama':
                            osc_values = calculate_kaufman_adaptive_moving_average(results["prices"])
                        elif oscillator == 'price_osc':
                            osc_values = calculate_price_oscillator(results["prices"])
                        elif oscillator == 'cci_enhanced':
                            # Use closing prices for high/low estimation
                            high_prices = results["prices"]  # Alpha Vantage only provides single price value
                            low_prices = results["prices"]
                            osc_values = calculate_commodity_channel_index_enhanced(high_prices, low_prices, results["prices"])
                        elif oscillator == 'momentum':
                            osc_values = calculate_momentum_oscillator(results["prices"])
                        elif oscillator == 'roc':
                            osc_values = calculate_rate_of_change_oscillator(results["prices"])
                        elif oscillator == 'smi':
                            # For SMI, use closing prices as approximation for high/low
                            high_prices = results["prices"]
                            low_prices = results["prices"]
                            smi_k, _ = calculate_stochastic_momentum_index(high_prices, low_prices, results["prices"])
                            osc_values = smi_k
                        elif oscillator == 'efficiency_ratio':
                            osc_values = calculate_kaufman_efficiency_ratio(results["prices"])
                        
                        # Ehlers Digital Signal Processing Oscillators
                        elif oscillator == 'fisher_transform':
                            osc_values = calculate_ehlers_fisher_transform(results["prices"])
                        elif oscillator == 'stochastic_cg':
                            # Use closing prices as approximation for high/low
                            high_prices = results["prices"]
                            low_prices = results["prices"]
                            osc_values = calculate_ehlers_stochastic_cg(high_prices, low_prices, results["prices"])
                        elif oscillator == 'super_smoother':
                            osc_values = calculate_ehlers_super_smoother(results["prices"])
                        elif oscillator == 'cycle_period':
                            osc_values = calculate_ehlers_cycle_period(results["prices"])
                        elif oscillator == 'mama':
                            mama_values, _ = calculate_ehlers_mama(results["prices"])
                            osc_values = mama_values
                        elif oscillator == 'sinewave':
                            sine_values, _ = calculate_ehlers_sinewave_indicator(results["prices"])
                            osc_values = sine_values
                        elif oscillator == 'hilbert_transform':
                            osc_values = calculate_ehlers_hilbert_transform(results["prices"])
                        
                        # Add oscillator data to results
                        if osc_values:
                            results["oscillator"] = {
                                "values": osc_values,
                                "dates": osc_dates,
                                "name": oscillator.upper()
                            }
                    
                    return JsonResponse(results)
                    
                except requests.exceptions.RequestException as e:
                    return error_response(endpoint, "vendor", "Failed to fetch data from Alpha Vantage.", params=params, details=str(e), exc=e, status=502)
                except ValueError as e:
                    return error_response(endpoint, "internal", "Unexpected error occurred during Alpha Vantage data fetch.", params=params, details=str(e), exc=e, status=500)

            else:
                raise ValueError(f"Invalid source: {source}")
        except requests.exceptions.RequestException as e:
            return error_response(endpoint, "vendor", "Failed to fetch data from vendor.", params=params, details=str(e), exc=e, status=502)
        except ValueError as e:
            return error_response(endpoint, "internal", "Unexpected error occurred during data fetch.", params=params, details=str(e), exc=e, status=500)

        return JsonResponse(results)
    except (requests.exceptions.RequestException, ValueError) as e:
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
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.error("Error fetching current weather data for %s: %s", city, str(e))
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
    except (requests.exceptions.RequestException, ValueError) as e:
        logger.error("Error in get_weather: %s", str(e))
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_energy(request):
    """Get energy system data - supports both ENTSO-E and Energy Charts APIs"""
    try:
        # Get parameters for energy analysis
        country = request.GET.get('country', 'DE')  # ISO country code
        data_type = request.GET.get('data_type', 'price')  # price, generation, load, or renewable_share
        api_source = request.GET.get('api_source', 'auto')  # auto, entsoe, or energy_charts
        start_date = request.GET.get('start')
        end_date = request.GET.get('end')
        
        if not start_date or not end_date:
            return JsonResponse({
                'error': 'Both start and end dates are required',
                'type': 'validation'
            }, status=400)
        
        try:
            # Validate date format and ensure we use historical dates
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Ensure we're requesting historical data (both APIs have some delays)
            today = datetime.now()
            if start_dt >= today - timedelta(days=1):
                # Use recent historical dates for demo
                end_dt = today - timedelta(days=2)
                start_dt = end_dt - timedelta(days=7)
                logger.info("Adjusted dates to historical period: %s to %s", start_dt.date(), end_dt.date())
                
        except ValueError as e:
            return JsonResponse({
                'error': f'Invalid date format. Use YYYY-MM-DD: {str(e)}',
                'type': 'validation'
            }, status=400)
        
        # Intelligent API selection based on data type and availability
        def select_api_and_get_data():
            """Select the best API for the requested data type"""
            result = None
            
            # For generation and renewable data, prefer Energy Charts
            if data_type in ['generation', 'renewable_share', 'load'] and api_source != 'entsoe':
                try:
                    energy_charts_client = EnergyChartsAPIClient()
                    
                    if data_type == 'generation':
                        result = energy_charts_client.get_power_generation(country, start_dt, end_dt)
                    elif data_type == 'load':
                        result = energy_charts_client.get_load_data(country, start_dt, end_dt)
                    elif data_type == 'renewable_share':
                        gen_data = energy_charts_client.get_power_generation(country, start_dt, end_dt)
                        if gen_data and 'renewable_share' in gen_data:
                            result = {
                                'dates': gen_data['dates'],
                                'values': gen_data['renewable_share'],
                                'type': 'renewable_share',
                                'source': 'energy_charts'
                            }
                        else:
                            result = None
                    
                    if result:
                        return result, 'energy_charts'
                except (requests.RequestException, ValueError, KeyError) as e:
                    logger.warning("Energy Charts API failed, falling back to ENTSO-E: %s", str(e))
            
            # For price data or fallback, use ENTSO-E
            if api_source != 'energy_charts':
                try:
                    entsoe_client = PowerPriceAPIClient()
                    # ENTSO-E currently only supports price data reliably
                    if data_type in ['price', 'generation', 'load']:
                        result = entsoe_client.get_price_data(country, start_dt, end_dt)
                        if result:
                            return result, 'entsoe'
                except (requests.RequestException, ValueError, KeyError) as e:
                    logger.warning("ENTSO-E API failed: %s", str(e))
            
            # Try Energy Charts as final fallback for price data
            if data_type == 'price':
                try:
                    energy_charts_client = EnergyChartsAPIClient()
                    result = energy_charts_client.get_price_data(country, start_dt, end_dt)
                    if result:
                        return result, 'energy_charts'
                except (requests.RequestException, ValueError, KeyError) as e:
                    logger.warning("Energy Charts fallback failed: %s", str(e))
            
            return None, None
        
        # Get data using intelligent API selection
        result, used_api = select_api_and_get_data()
        
        if result and result.get('dates'):
            # Check for valid data based on data type
            if ((data_type == 'generation' and 'generation_by_source' in result) or
                (data_type != 'generation' and result.get('values'))):
                
                # Format response based on data type
                response_data = {
                    'country': country,
                    'dates': result['dates'],
                    'api_source': used_api,
                    'success': True
                }
                
                if data_type == 'generation' and 'generation_by_source' in result:
                    # Enhanced generation data from Energy Charts
                    response_data.update({
                        'title': f'Power Generation Mix - {country}',
                        'unit': 'MW',
                        'type': 'generation',
                        'generation_by_source': result['generation_by_source'],
                        'renewable_total': result.get('renewable_total', []),
                        'fossil_total': result.get('fossil_total', []),
                        'renewable_share': result.get('renewable_share', [])
                    })
                elif data_type == 'renewable_share':
                    response_data.update({
                        'title': f'Renewable Energy Share - {country}',
                        'unit': '%',
                        'type': 'renewable_share',
                        'values': result['values']
                    })
                elif data_type == 'load':
                    response_data.update({
                        'title': f'Electricity Load - {country}',
                        'unit': 'MW',
                        'type': 'load',
                        'values': result['values']
                    })
                else:  # price data
                    response_data.update({
                        'title': f'Electricity Prices - {country}',
                        'unit': '€/MWh',
                        'type': 'price',
                        'values': result['values']
                    })
                
                return JsonResponse(response_data)
        else:
            return JsonResponse({
                'error': f'No {data_type} data available for {country} in the specified period',
                'type': 'no_data',
                'suggestion': 'Try using recent historical dates (2-7 days ago) as energy APIs have publication delays',
                'supported_data_types': ['price', 'generation', 'load', 'renewable_share'],
                'supported_countries': ['DE', 'FR', 'ES', 'IT', 'AT']
            }, status=404)
        
    except (requests.RequestException, ValueError, KeyError) as e:
        logger.error("Error in get_energy: %s", str(e))
        return JsonResponse({
            'error': str(e),
            'type': 'server_error'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_commodities_list(request):
    source = request.GET.get('source', 'api_ninjas')
    json_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'commodities_by_source.json')
    print(f"DEBUG: commodities_by_source.json path: {json_path}")
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
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
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'api_keys.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        api_key_fmp = config['FIN_MODELING_PREP_KEY']
        api_key_cpa = config['COMMODITYPRICEAPI_KEY']
        api_key = config['API_NINJAS_KEY']
        
    if source == DataSource.FMP.value:
        base_url = 'https://financialmodelingprep.com/api/v3'
        endpoint = f'{base_url}/symbol/available-commodities'
        
        try:
            response = requests.get(
                endpoint,
                params={'apikey': api_key_fmp},
                timeout=30
            )
            response.raise_for_status()
            symbols = response.json()
            
            # Cache the results for 24 hours (86400 seconds)
            cache.set(cache_key, symbols, timeout=86400)
            
            return JsonResponse(symbols, safe=False)
        except requests.exceptions.RequestException as e:
            logger.error("Error fetching FMP symbols: %s", e)
            return JsonResponse({"error": "Failed to fetch symbols"}, status=500)
        except json.JSONDecodeError as e:
            logger.error("Error parsing FMP symbols response: %s", e)
            return JsonResponse({"error": "Invalid response from API"}, status=500)

    elif source == DataSource.COMMODITYPRICEAPI.value:
        endpoint = 'https://api.commoditypriceapi.com/v2/symbols'
        try:
            response = requests.get(
                endpoint,
                headers={'x-api-key': api_key_cpa},
                timeout=30
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
        except requests.exceptions.RequestException as e:
            logger.error("Error fetching CommodityPriceAPI symbols: %s", e)
            return JsonResponse([], safe=False)

    elif source == DataSource.API_NINJAS.value:
        data = []
        base_url = 'https://api.api-ninjas.com/v1/commodityprice'
        for name in SUPPORTED_NAMES:
            try:
                response = requests.get(
                    base_url,
                    headers={'X-Api-Key': api_key},
                    params={'name': name},
                    timeout=30
                )
                if response.status_code == 200:
                    res = response.json()
                    data.append(res)
                else:
                    logger.error("Error for %s: %s %s", name, response.status_code, response.text)
                time.sleep(0.2)  # Be polite to the API
            except requests.exceptions.RequestException as e:
                logger.error("Error fetching API Ninjas data for %s: %s", name, e)
                return JsonResponse({"error": str(e)}, status=400)
        cache.set(cache_key, data, timeout=86400)
        return JsonResponse(data, safe=False)

    elif source == DataSource.ALPHA_VANTAGE.value:
        try:
            client = AlphaVantageAPIClient()
            symbols = client.get_available_commodities()
            # Format symbols to match other sources
            formatted_symbols = [{"symbol": s, "name": s} for s in symbols]
            cache.set(cache_key, formatted_symbols, timeout=86400)
            return JsonResponse(formatted_symbols, safe=False)
        except requests.exceptions.RequestException as e:
            logger.error("Error fetching Alpha Vantage symbols: %s", e)
            return JsonResponse({"error": str(e)}, status=500)

    else:
        return JsonResponse({"error": "Invalid source"}, status=400)

def index(request):
    return render(request, 'dashboard/index.html')

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
    except requests.exceptions.RequestException as e:
        logger.error("Error in get_commodity_data: %s", str(e))
        return JsonResponse({'error': str(e)}, status=500)


