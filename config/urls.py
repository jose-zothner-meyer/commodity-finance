"""
Main URL configuration for Portfolio Analytics Platform
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.dashboard.urls')),
    path('api/', include('apps.api.urls')),
] 