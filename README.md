# Energy & Commodity Data Analytics Platform

A Django-based platform for analyzing energy prices, commodity markets, and weather data with real-time updates and technical analysis capabilities.

## Table of Contents
- [Energy \& Commodity Data Analytics Platform](#energy--commodity-data-analytics-platform)
  - [Table of Contents](#table-of-contents)
  - [Description](#description)
  - [Features](#features)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Project Structure](#project-structure)
  - [API Integration](#api-integration)
  - [Technical Analysis](#technical-analysis)
  - [License](#license)

## Description
This project provides a comprehensive platform for analyzing energy prices, commodity markets, and weather data. It integrates multiple data sources to provide real-time insights and technical analysis for various financial instruments. The platform was developed to help users make informed decisions about energy and commodity investments by providing a unified interface for accessing and analyzing market data.

Key features include:
- Real-time commodity price tracking
- Weather impact analysis
- Energy market data visualization
- Technical analysis indicators
- Multiple data source integration

## Features
- Multiple data source integration (FMP, Alpha Vantage, OpenWeather, ENTSO-E)
- Real-time data updates
- Technical analysis indicators (RSI, MACD, Stochastic, CCI, Williams %R)
- Caching system for improved performance
- Error handling and validation
- Responsive UI with Bootstrap
- Interactive data visualization with Plotly

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd energy_project
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create an `api_keys.yaml` file in the project root with your API keys:
```yaml
FIN_MODELING_PREP_KEY: your_fmp_key
ALPHAVANTAGE_API_KEY: your_alpha_vantage_key
OPENWEATHER_API_KEY: your_openweather_key
ENTSOE_TOKEN: your_entsoe_key
API_NINJAS_KEY: your_api_ninjas_key
COMMODITYPRICEAPI_KEY: your_commodity_price_api_key
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Start the development server:
```bash
python manage.py runserver
```

## Usage

1. Access the main dashboard at `http://localhost:8000`
2. Select a data source from the dropdown menu
3. Choose a commodity or energy market to analyze
4. View real-time data and technical analysis indicators
5. Use the interactive charts to explore price trends and patterns
6. Monitor weather impacts on energy markets
7. Track European energy market prices through ENTSO-E integration

## Project Structure
```
energy_project/
├── energy_finance/          # Main application directory
│   ├── __init__.py
│   ├── constants.py         # Data source enums and supported names
│   ├── data_ingest.py      # API client implementations
│   ├── oscillators.py      # Technical analysis indicators
│   ├── urls.py            # URL routing
│   └── views.py           # View functions
├── dashboard/              # Dashboard application
├── templates/             # HTML templates
├── static/               # Static files (CSS, JS, images)
├── api_keys.yaml         # API key configuration
├── requirements.txt      # Project dependencies
├── manage.py            # Django management script
└── db.sqlite3           # SQLite database
```

## API Integration

The platform integrates with multiple data sources:

1. **Financial Modeling Prep (FMP)**
   - Commodity market data
   - Historical price data
   - Symbol information

2. **Alpha Vantage**
   - Additional commodity data
   - Real-time price updates

3. **OpenWeather API**
   - Current weather data
   - Weather impact analysis

4. **ENTSO-E**
   - European energy market prices
   - Day-ahead pricing

## Technical Analysis

The platform includes several technical analysis indicators:
- Relative Strength Index (RSI)
- Moving Average Convergence Divergence (MACD)
- Stochastic Oscillator
- Commodity Channel Index (CCI)
- Williams %R

## License
This project is licensed under the MIT License - see the LICENSE file for details.
