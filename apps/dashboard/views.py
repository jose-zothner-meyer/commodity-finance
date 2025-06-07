from django.shortcuts import render
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

def dashboard(request):
    """Render the main dashboard with proper error handling context"""
    context = {
        'has_weather_api': True,  # Weather API is working
        'has_energy_api': False,  # Energy API has auth issues
        'default_city': 'London',
        'available_markets': ['DE-LU', 'FR', 'ES', 'IT'],
        'api_status': {
            'weather': 'active',
            'energy': 'auth_error',
            'commodities': 'active'
        }
    }
    return render(request, 'dashboard/index.html', context) 