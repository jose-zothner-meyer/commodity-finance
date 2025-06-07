from django.urls import path
from apps.api import views

urlpatterns = [
    path('commodities/', views.get_commodities, name='get_commodities'),
    path('weather/', views.get_weather, name='get_weather'),
    path('energy/', views.get_energy, name='get_energy'),
    path('commodities_list/', views.get_commodities_list, name='get_commodities_list'),
    path('params/', views.get_available_symbols_by_data_source, name='get_params'),
    
    # Portfolio Analytics Endpoints
    path('portfolio/analyze/', views.analyze_portfolio, name='analyze_portfolio'),
    path('portfolio/simulate/', views.simulate_portfolio, name='simulate_portfolio'),
    path('portfolio/optimize/', views.optimize_portfolio, name='optimize_portfolio'),
    path('portfolio/sample/', views.get_portfolio_sample, name='get_portfolio_sample'),
    
    # EIA (US Energy Information Administration) Endpoints
    path('eia/electricity/generation/', views.eia_electricity_generation, name='eia_electricity_generation'),
    path('eia/electricity/prices/', views.eia_electricity_prices, name='eia_electricity_prices'),
    path('eia/natural-gas/', views.eia_natural_gas, name='eia_natural_gas'),
    path('eia/renewable-energy/', views.eia_renewable_energy, name='eia_renewable_energy'),
    path('eia/petroleum/', views.eia_petroleum, name='eia_petroleum'),
    
    # FRED (Federal Reserve Economic Data) Endpoints
    path('fred/economic-indicators/', views.fred_economic_indicators, name='fred_economic_indicators'),
    path('fred/series/', views.fred_series_data, name='fred_series_data'),
    path('fred/multiple-series/', views.fred_multiple_series, name='fred_multiple_series'),
    path('fred/search/', views.fred_search, name='fred_search'),
] 