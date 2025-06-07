from django.contrib import admin
from django.urls import path, include
from energy_finance import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('api/commodities/', views.get_commodities, name='get_commodities'),
    path('api/weather/', views.get_weather, name='get_weather'),
    path('api/energy/', views.get_energy, name='get_energy'),
    path('api/commodities_list/', views.get_commodities_list, name='get_commodities_list'),
    path('api/params/', views.get_available_symbols_by_data_source, name='get_params'),
    
    # Portfolio Analytics Endpoints
    path('api/portfolio/analyze/', views.analyze_portfolio, name='analyze_portfolio'),
    path('api/portfolio/simulate/', views.simulate_portfolio, name='simulate_portfolio'),
    path('api/portfolio/optimize/', views.optimize_portfolio, name='optimize_portfolio'),
    path('api/portfolio/sample/', views.get_portfolio_sample, name='get_portfolio_sample'),
    
    # EIA (US Energy Information Administration) Endpoints
    path('api/eia/electricity/generation/', views.eia_electricity_generation, name='eia_electricity_generation'),
    path('api/eia/electricity/prices/', views.eia_electricity_prices, name='eia_electricity_prices'),
    path('api/eia/natural-gas/', views.eia_natural_gas, name='eia_natural_gas'),
    path('api/eia/renewable-energy/', views.eia_renewable_energy, name='eia_renewable_energy'),
    path('api/eia/petroleum/', views.eia_petroleum, name='eia_petroleum'),
    
    # FRED (Federal Reserve Economic Data) Endpoints
    path('api/fred/economic-indicators/', views.fred_economic_indicators, name='fred_economic_indicators'),
    path('api/fred/series/', views.fred_series_data, name='fred_series_data'),
    path('api/fred/multiple-series/', views.fred_multiple_series, name='fred_multiple_series'),
    path('api/fred/search/', views.fred_search, name='fred_search'),
] 