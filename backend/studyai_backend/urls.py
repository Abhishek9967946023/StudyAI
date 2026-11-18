"""
=============================================================================
StudyAI — Main Project URL Configuration
=============================================================================
Routes URLs to the Django admin and the StudyAI API.
Allows administrative URL path obfuscation via DJANGO_ADMIN_URL_PATH.
=============================================================================
"""

import os
from django.contrib import admin
from django.urls import path, include

admin_path = os.environ.get('DJANGO_ADMIN_URL_PATH', 'admin/').strip('/') + '/'

urlpatterns = [
    # Built-in Django Admin Interface (configurable path for security)
    path(admin_path, admin.site.urls),

    # StudyAI REST API Endpoints
    path('api/', include('api.urls')),
]
