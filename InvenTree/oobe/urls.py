"""
URL lookup for setups
"""

from django.urls import re_path

from . import views


oobe_urls = [
    # Initial setup
    re_path(r'^oobe/', views.ContactWizard.as_view(), name='part-import'),
]
