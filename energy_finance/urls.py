from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('api/commodities', views.get_commodities, name='get_commodities'),
    path('api/weather', views.get_weather, name='get_weather'),
    path('api/energy', views.get_energy, name='get_energy'),
    path('api/commodities_list', views.get_commodities_list, name='get_commodities_list'),
    path('api/params', views.get_available_symbols_by_data_source, name='get_params'),
] 