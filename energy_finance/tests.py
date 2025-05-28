from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock, mock_open
import json
from datetime import datetime, timedelta
import requests
import yaml # Import yaml for mocking
import os # Import os for path joining
import pytest

# Helper function to create a mock requests.Response object
def create_mock_response(status_code=200, json_data=None, text=""):
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data
    mock_response.text = text
    if status_code >= 400:
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
    else:
        mock_response.raise_for_status.return_value = None
    return mock_response

class CommodityAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        # Set up mock configuration
        self.mock_config = {
            'API_NINJAS_KEY': 'fake_key_ninja',
            'FIN_MODELING_PREP_KEY': 'fake_key_fmp',
            'COMMODITYPRICEAPI_KEY': 'fake_key_commodity',
            'ENTSOE_API_KEY': 'fake_entsoe_key',
            'OPENWEATHER_API_KEY': 'fake_openweather_key'
        }
        # Set up commodities data
        self.commodities_data = {
            "api_ninjas": ["gold", "silver"],
            "fmp": ["gold"],
            "commodity_price_api": ["gold"]
        }
        # Create patches for _load_config and commodities file
        self.patcher_load_config = patch('energy_finance.data_ingest.APIClient._load_config', return_value=self.mock_config)
        self.patcher_commodities = patch('builtins.open', mock_open(read_data=json.dumps(self.commodities_data)))
        self.mock_load_config = self.patcher_load_config.start()
        self.mock_commodities = self.patcher_commodities.start()

    def tearDown(self):
        self.patcher_load_config.stop()
        self.patcher_commodities.stop()

    # Redundant test, removed as validation is handled by test_unsupported_commodity
    # @patch('energy_finance.views.APINinjasCommodityClient.get_price')
    # def test_get_commodities_invalid_commodity(self, mock_get_price):
    #     response = self.client.get('/api/commodities?source=api_ninjas&name=invalidcommodity&start=2023-01-01&end=2023-01-02')
    #     self.assertEqual(response.status_code, 400)
    #     self.assertIn("error", json.loads(response.content))

    # Test for missing API key is still valid and expects 500
    @patch('energy_finance.views.requests.get')
    def test_get_commodities_missing_api_key_fmp(self, mock_get):
        # Override mock config to simulate missing FMP key
        self.mock_config.pop('FIN_MODELING_PREP_KEY')
        response = self.client.get('/api/commodities?source=fmp&name=gold&start=2023-01-01&end=2023-01-02')
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", json.loads(response.content))
        self.assertIn("API key missing for FMP", json.loads(response.content)["error"])

    @patch('energy_finance.views.requests.get')
    def test_get_commodities_network_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Simulated network error")
        response = self.client.get('/api/commodities?source=api_ninjas&name=gold&start=2023-01-01&end=2023-01-02')
        self.assertEqual(response.status_code, 502)
        self.assertIn("error", json.loads(response.content))
        self.assertIn("Failed to fetch data from vendor.", json.loads(response.content)["error"])

    @patch('energy_finance.views.PowerPriceAPIClient.get_historical')
    def test_get_energy_invalid_date_format(self, mock_get_historical):
        response = self.client.get('/api/energy?market=DE-LU&start=invalid-date&end=2023-01-02')
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", json.loads(response.content))
        self.assertIn("Invalid date format", json.loads(response.content)["error"])

    # No need to mock requests.get for missing parameter tests as they should fail before API call
    def test_missing_parameters(self):
        response = self.client.get('/api/commodities')
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid or missing data source", json.loads(response.content)["error"])
        response = self.client.get('/api/commodities?source=api_ninjas&start=2023-01-01&end=2023-01-02')
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid or missing commodity for selected source", json.loads(response.content)["error"])
        response = self.client.get('/api/commodities?source=commodity_price_api&name=gold')
        self.assertEqual(response.status_code, 400)
        self.assertIn("Start and end dates are required", json.loads(response.content)["error"])
        response = self.client.get('/api/commodities?source=api_ninjas&name=gold&start=2023-01-01')
        self.assertEqual(response.status_code, 400)
        self.assertIn("Start and end dates are required", json.loads(response.content)["error"])

    def test_unsupported_data_source(self):
        response = self.client.get('/api/commodities?source=unknown&name=gold&start=2023-01-01&end=2023-01-02')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid or missing data source', json.loads(response.content)["error"])

    @patch('energy_finance.views.requests.get')
    def test_unsupported_commodity_validation(self, mock_get):
        response = self.client.get('/api/commodities?source=api_ninjas&name=unknowncommodity&start=2023-01-01&end=2023-01-02')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid or missing commodity for selected source', json.loads(response.content)["error"])

    # Test for date range calculation logic (Pure Python logic, doesn't need Django test client)
    def test_date_range_logic_helper(self):
        today = datetime.today()
        # Approximation for 1 month
        one_month_ago = today - timedelta(days=30)
        self.assertTrue((today.date() - one_month_ago.date()).days >= 28)
        # Approximation for 1 year
        one_year_ago = today - timedelta(days=365)
        self.assertTrue((today.date() - one_year_ago.date()).days >= 364)

    @patch('energy_finance.views.requests.get')
    def test_api_vendor_400_error_handling(self, mock_get):
        # Simulate a 400 error response from the vendor API
        mock_response = create_mock_response(status_code=400, text="Vendor specific bad request details")
        mock_get.return_value = mock_response
        response = self.client.get('/api/commodities?source=api_ninjas&name=gold&start=2023-01-01&end=2023-01-02')
        # Backend catches 400 from vendor and returns 400
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn("Invalid request to API Ninjas.", data['error'])
        self.assertIn("Vendor specific bad request details", data['details'])

    @patch('energy_finance.views.requests.get')
    def test_api_vendor_401_error_handling(self, mock_get):
        # Simulate a 401 error response from the vendor API
        mock_response = create_mock_response(status_code=401, text="Vendor specific unauthorized details")
        mock_get.return_value = mock_response
        response = self.client.get('/api/commodities?source=api_ninjas&name=gold&start=2023-01-01&end=2023-01-02')
        # Backend catches 401 from vendor and returns 401
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn("Unauthorized. Check your API Ninjas key.", data['error'])
        self.assertIn("Vendor specific unauthorized details", data['details'])

    @patch('energy_finance.views.requests.get')
    def test_empty_results_from_vendor(self, mock_get):
        # Simulate a 200 OK response with empty historical data from vendor
        mock_response = create_mock_response(status_code=200, json_data=[] )# Empty list for API Ninjas/CommodityPriceAPI
        mock_get.return_value = mock_response
        response = self.client.get('/api/commodities?source=api_ninjas&name=gold&start=2023-01-01&end=2023-01-02')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('dates', data)
        self.assertIn('prices', data)
        self.assertEqual(data['dates'], [])
        self.assertEqual(data['prices'], [])

        # Test for FMP empty historical data case
        mock_response = create_mock_response(status_code=200, json_data={'historical': []})
        mock_get.return_value = mock_response
        response = self.client.get('/api/commodities?source=fmp&name=gold&start=2023-01-01&end=2023-01-02')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('dates', data)
        self.assertIn('prices', data)
        self.assertEqual(data['dates'], [])
        self.assertEqual(data['prices'], [])

    # Add a test for successful API call
    @patch('energy_finance.views.requests.get')
    def test_successful_api_call(self, mock_get):
        # Simulate a successful API response
        mock_response = create_mock_response(status_code=200, json_data=[{"time": 1672531200, "close": 1800}]) # Example data
        mock_get.return_value = mock_response
        response = self.client.get('/api/commodities?source=api_ninjas&name=gold&start=2023-01-01&end=2023-01-02')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('dates', data)
        self.assertIn('prices', data)
        self.assertEqual(data['dates'], ['2023-01-01'])
        self.assertEqual(data['prices'], [1800])

        # Simulate a successful FMP API response
        mock_response = create_mock_response(status_code=200, json_data={'historical': [{'date': '2023-01-01', 'close': 1800}]})
        mock_get.return_value = mock_response
        response = self.client.get('/api/commodities?source=fmp&name=gold&start=2023-01-01&end=2023-01-02')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('dates', data)
        self.assertIn('prices', data)
        self.assertEqual(data['dates'], ['2023-01-01'])
        self.assertEqual(data['prices'], [1800])

        # Simulate a successful CommodityPriceAPI response (looping over dates is handled in view)
        # Mock get for each date in the range
        def mock_commodity_price_get(*args, **kwargs):
            date_param = kwargs['params']['date']
            if date_param == '2023-01-01':
                return create_mock_response(status_code=200, json_data={'data': [{'symbol': 'gold', 'rate': 1800}]})
            elif date_param == '2023-01-02':
                 return create_mock_response(status_code=200, json_data={'data': [{'symbol': 'gold', 'rate': 1810}]})
            return create_mock_response(status_code=200, json_data={'data': []})

        mock_get.side_effect = mock_commodity_price_get
        response = self.client.get('/api/commodities?source=commodity_price_api&name=gold&start=2023-01-01&end=2023-01-02')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('prices', data)
        self.assertEqual(data['prices'], {'2023-01-01': 1800, '2023-01-02': 1810})

    def test_commodities_list_valid_and_invalid_source(self):
        # Valid source
        response = self.client.get('/api/commodities_list?source=fmp')
        data = json.loads(response.content)
        print('DEBUG: Requested source=fmp, returned:', data)
        self.assertIn('commodities', data)
        # Invalid source
        response = self.client.get('/api/commodities_list?source=invalid_source')
        data = json.loads(response.content)
        print('DEBUG: Requested source=invalid_source, returned:', data)
        self.assertIn('commodities', data)

    def test_weather_valid_and_invalid(self):
        with patch('energy_finance.data_ingest.APIClient._load_config', return_value=self.mock_config):
            with patch('energy_finance.data_ingest.OpenWeatherAPIClient._load_config', return_value=self.mock_config):
                with patch('energy_finance.data_ingest.requests.get') as mock_get:
                    def fake_get(url, params=None, **kwargs):
                        if 'timemachine' in url:
                            return create_mock_response(status_code=200, json_data={'current': {'temp': 21.0}})
                        raise Exception('Unexpected URL')
                    mock_get.side_effect = fake_get
                    today = datetime.today().strftime('%Y-%m-%d')
                    tomorrow = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
                    response = self.client.get(f'/api/weather?location=48.8566,2.3522&start={today}&end={tomorrow}')
                    self.assertEqual(response.status_code, 200)
                    data = json.loads(response.content)
                    self.assertIn('dates', data)
                    self.assertIn('temperatures', data)
                    self.assertEqual(data['temperatures'][0], 21.0)

        response = self.client.get('/api/weather?location=48.8566,2.3522&start=bad-date&end=2023-01-02')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('Invalid date format', data['error'])

        response = self.client.get(f'/api/weather?location=not_a_location&start={today}&end={tomorrow}')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)

    @patch('requests.get')
    @patch('energy_finance.views.PowerPriceAPIClient.get_historical')
    def test_energy_valid_and_invalid(self, mock_get_historical, mock_requests_get):
        # Patch open to include ENTSOE_TOKEN in api_keys.yaml
        with patch('builtins.open', mock_open(read_data="""API_NINJAS_KEY: fake_key_ninja
FIN_MODELING_PREP_KEY: fake_key_fmp
COMMODITYPRICEAPI_KEY: fake_key_commodity
ENTSOE_TOKEN: fake_entsoe_token
""")):
            # Mock ENTSO-E XML response with fully qualified tag names and ns0 prefix
            entsoe_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<ns0:Publication_MarketDocument xmlns:ns0="urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0">
  <ns0:TimeSeries>
    <ns0:Period>
      <ns0:timeInterval>
        <ns0:start>2023-01-01T00:00Z</ns0:start>
      </ns0:timeInterval>
      <ns0:Point>
        <ns0:position>1</ns0:position>
        <ns0:price.amount>100.0</ns0:price.amount>
      </ns0:Point>
      <ns0:Point>
        <ns0:position>2</ns0:position>
        <ns0:price.amount>110.0</ns0:price.amount>
      </ns0:Point>
    </ns0:Period>
  </ns0:TimeSeries>
</ns0:Publication_MarketDocument>'''
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = entsoe_xml.encode('utf-8')
            mock_requests_get.return_value = mock_response

            mock_get_historical.return_value = None  # Not used anymore
            response = self.client.get(f'/api/energy?market=DE-LU&start=2023-01-01&end=2023-01-01')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertIn('dates', data)
            self.assertIn('prices', data)
            self.assertEqual(data['dates'][0], '2023-01-01T00:00Z')
            self.assertEqual(data['prices'][0], 100.0)
            self.assertEqual(data['prices'][1], 110.0)
            # Invalid date
            response = self.client.get('/api/energy?market=DE-LU&start=bad-date&end=2023-01-02')
            self.assertEqual(response.status_code, 400)
            self.assertIn('error', json.loads(response.content))
            self.assertIn('Invalid date format', json.loads(response.content)['error'])
            # (We could add more logic here if needed)

    def test_commodities_start_after_end(self):
        response = self.client.get('/api/commodities?source=api_ninjas&name=gold&start=2023-01-03&end=2023-01-01')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('Start date must be before end date.', data['error'])
        self.assertIn("start='2023-01-03', end='2023-01-01'", data['details'])

    def test_commodities_invalid_date_format(self):
        response = self.client.get('/api/commodities?source=api_ninjas&name=gold&start=bad-date&end=2023-01-01')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('Invalid date format for start or end', data['error'])
        self.assertIn("start='bad-date'", data['details'])

@pytest.fixture
def client():
    return Client()

# --- Commodities Endpoint ---
def test_commodities_success_fmp(client):
    with patch('energy_finance.data_ingest.APIClient._load_config', return_value={'FIN_MODELING_PREP_KEY': 'fake_key'}):
        resp = client.get(
            reverse('get_commodities'),
            {'source': 'fmp', 'name': 'GCUSD', 'start': '2025-05-24', 'end': '2025-05-25'}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert 'dates' in data and 'prices' in data

@pytest.mark.parametrize('params,expected_status', [
    ({'source': 'fmp', 'name': 'GCUSD', 'start': '', 'end': '2025-05-25'}, 400),
    ({'source': 'fmp', 'name': '', 'start': '2025-05-24', 'end': '2025-05-25'}, 400),
    ({'source': 'fmp', 'name': 'INVALID', 'start': '2025-05-24', 'end': '2025-05-25'}, 400),
    ({'source': 'fmp', 'name': 'GCUSD', 'start': '2025-05-25', 'end': '2025-05-24'}, 400),
])
def test_commodities_param_errors(client, params, expected_status):
    with patch('energy_finance.data_ingest.APIClient._load_config', return_value={'FIN_MODELING_PREP_KEY': 'fake_key'}):
        resp = client.get(reverse('get_commodities'), params)
        assert resp.status_code == expected_status
        data = resp.json()
        assert 'error' in data

# --- Energy Endpoint ---
def test_energy_missing_params(client):
    with patch('energy_finance.data_ingest.APIClient._load_config', return_value={'ENTSOE_API_KEY': 'fake_key'}):
        resp = client.get(reverse('get_energy'), {'market': 'DE-LU'})
        assert resp.status_code == 400 or resp.status_code == 500
        data = resp.json()
        assert 'error' in data

def test_energy_invalid_dates(client):
    with patch('energy_finance.data_ingest.APIClient._load_config', return_value={'ENTSOE_API_KEY': 'fake_key'}):
        resp = client.get(reverse('get_energy'), {'market': 'DE-LU', 'start': '2025-05-25', 'end': '2025-05-24'})
        assert resp.status_code == 400
        data = resp.json()
        assert 'error' in data

# --- Weather Endpoint ---
def test_weather_city_success(client, monkeypatch):
    with patch('energy_finance.data_ingest.APIClient._load_config', return_value={'OPENWEATHER_API_KEY': 'fake_key'}):
        def fake_get(url, params=None, **kwargs):
            if 'geo' in url:
                return type('Resp', (), {'raise_for_status': lambda self: None, 'json': lambda self: [{'lat': 48.8566, 'lon': 2.3522}]})()
            if 'timemachine' in url:
                return type('Resp', (), {'raise_for_status': lambda self: None, 'json': lambda self: {'current': {'temp': 21.0}}})()
            raise Exception('Unexpected URL')
        monkeypatch.setattr(requests, 'get', fake_get)
        resp = client.get(reverse('get_weather'), {'city': 'Paris', 'start': '2025-05-24', 'end': '2025-05-25'})
        assert resp.status_code == 200
        data = resp.json()
        assert 'temperatures' in data and data['temperatures'][0] == 21.0

def test_weather_missing_params(client):
    with patch('energy_finance.data_ingest.APIClient._load_config', return_value={'OPENWEATHER_API_KEY': 'fake_key'}):
        resp = client.get(reverse('get_weather'), {'city': 'Paris'})
        assert resp.status_code == 400
        data = resp.json()
        assert 'error' in data

def test_weather_invalid_location(client):
    with patch('energy_finance.data_ingest.APIClient._load_config', return_value={'OPENWEATHER_API_KEY': 'fake_key'}):
        resp = client.get(reverse('get_weather'), {'location': 'not_a_location', 'start': '2025-05-24', 'end': '2025-05-25'})
        assert resp.status_code == 400
        data = resp.json()
        assert 'error' in data

def test_weather_city_not_found(client, monkeypatch):
    with patch('energy_finance.data_ingest.APIClient._load_config', return_value={'OPENWEATHER_API_KEY': 'fake_key'}):
        def fake_get(url, params=None, **kwargs):
            if 'geo' in url:
                return type('Resp', (), {'raise_for_status': lambda self: None, 'json': lambda self: []})()
            raise Exception('Unexpected URL')
        monkeypatch.setattr(requests, 'get', fake_get)
        resp = client.get(reverse('get_weather'), {'city': 'Atlantis', 'start': '2025-05-24', 'end': '2025-05-25'})
        assert resp.status_code == 404
        data = resp.json()
        assert 'error' in data 