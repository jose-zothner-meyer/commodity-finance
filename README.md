# Django Commodity Tracker

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://djangoproject.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](scripts/validation/quick_validation.py)

A Django-based financial analytics platform combining technical analysis, portfolio optimization, energy market intelligence, and economic data integration. Features an 8-tab dashboard interface with analytics for commodities, energy markets, and economic indicators.

## Table of Contents
- [Project Description](#project-description)
- [Installation](#installation)
- [Usage](#usage)
- [File Structure](#file-structure)
- [License](#license)

## Project Description

### What it does
This Django web application provides financial analytics for commodities, energy markets, and portfolio management. It integrates multiple data sources to deliver analytics through an interactive dashboard interface.

### Key Features
- **Technical Analysis**: 14 oscillators based on Kaufman and Ehlers methodologies
- **Portfolio Analytics**: Monte Carlo simulations and Modern Portfolio Theory optimization
- **Energy Market Intelligence**: European (ENTSO-E) and US (EIA) energy data
- **Economic Data Integration**: Federal Reserve Economic Data (FRED) for macroeconomic analysis
- **Multi-Source Data**: Integrated APIs with failover systems

### Aim of the Project
The project aims to create a comprehensive platform that combines:
- Advanced technical analysis for financial markets
- Portfolio optimization tools using Modern Portfolio Theory
- Real-time energy market intelligence from official sources
- Economic data correlation analysis for informed decision-making

### What I Learned
This project enhanced my skills in:
- **Django Architecture**: Multi-app architecture with clean separation of concerns
- **API Integration**: Managing multiple data sources with failover mechanisms
- **Financial Mathematics**: Implementing algorithms for technical analysis and portfolio optimization
- **Data Visualization**: Creating interactive charts using Plotly.js
- **Performance Optimization**: Caching strategies and efficient data processing
- **Testing & Validation**: Test suites ensuring mathematical accuracy and system reliability

## Installation

### Prerequisites
- Python 3.9+ (Python 3.12 recommended)
- Git for version control

### Setup Instructions

1. **Clone the repository:**
```bash
git clone [repository-url]
cd commodity-tracker-1
```

2. **Create and activate virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure API keys** - Create `api_keys.yaml` in project root:
```yaml
# Core Data Sources (Required)
FIN_MODELING_PREP_KEY: your_fmp_key_here
ENTSOE_TOKEN: your_entsoe_key
EIA_API_KEY: your_eia_key
FRED_API_KEY: your_fred_key

# Optional Enhanced Sources
API_NINJAS_KEY: your_api_ninjas_key
OPENWEATHER_API_KEY: your_openweather_key
ALPHAVANTAGE_API_KEY: your_alpha_vantage_key
```

5. **Initialize database:**
```bash
python manage.py migrate
```

6. **Run tests** (verify installation):
```bash
python scripts/validation/quick_validation.py
```

7. **Start the server:**
```bash
python manage.py runserver 8000
```

8. **Access dashboard:**
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser

## Usage

### Quick Start Guide

1. **Access Dashboard**: Navigate to the local server URL
2. **Select Data Source**: Choose from FMP, API Ninjas, or other configured APIs
3. **Choose Asset**: Select commodities (Gold, Silver, Oil) or other supported assets
4. **Select Analysis**: Choose from 14 technical oscillators organized by methodology
5. **View Results**: Interactive charts with professional visualizations

### Dashboard Tabs

1. **📈 Commodities**: Technical analysis with advanced oscillators
2. **⚡ Energy Prices**: Real-time European electricity market data
3. **💼 Portfolio Analytics**: Monte Carlo simulations and portfolio optimization
4. **🇺🇸 US Energy (EIA)**: US energy market data
5. **📊 Economic Data (FRED)**: Federal Reserve economic indicators
6. **🌱 Renewables**: Renewable energy generation and analysis
7. **🌦️ Weather**: Weather data for agricultural commodity analysis
8. **🔋 Energy Analytics**: European energy market intelligence

### API Endpoints
- `/api/commodity-price/`: Fetch commodity price data
- `/api/portfolio/analyze/`: Portfolio optimization and risk analysis
- `/api/energy-data/`: European energy market data
- `/api/economic-data/`: Federal Reserve economic data

## File Structure

```
commodity-tracker-1/
├── apps/                    # Django applications
│   ├── api/                # REST API endpoints
│   ├── core/               # Business logic & data processing
│   └── dashboard/          # Web interface
├── config/                 # Django configuration
│   └── settings/           # Environment-specific configs
├── data/                   # Configuration & data files
├── docs/                   # Documentation
│   ├── api/               # API documentation
│   ├── deployment/        # Deployment guides
│   └── technical/         # Technical specifications
├── scripts/               # Utilities & validation
│   ├── demos/             # Feature demonstrations
│   ├── deployment/        # Production deployment
│   └── validation/        # System validation scripts
├── static/js/             # Frontend JavaScript
├── templates/dashboard/   # HTML templates
├── tests/                 # Test suites
│   ├── integration/       # Integration tests
│   └── unit/              # Unit tests
├── logs/                  # Application logging
├── requirements.txt       # Python dependencies
├── manage.py              # Django management script
└── README.md              # This file
```

### Key Files
- `apps/core/oscillators.py`: 14 technical oscillator implementations
- `apps/core/portfolio.py`: Portfolio optimization and Monte Carlo simulations
- `apps/core/data_ingest.py`: Multi-source data integration
- `apps/api/views.py`: API endpoint handlers
- `static/js/dashboard.js`: Frontend dashboard controller
- `scripts/validation/quick_validation.py`: System validation script

### Technology Stack
- **Backend**: Django 4.2+, Django REST Framework, Python 3.9+
- **Data Analysis**: NumPy, Pandas, SciPy
- **Visualization**: Plotly.js
- **Database**: SQLite (development)
- **API Integration**: Requests, PyYAML

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Django Commodity Tracker

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
