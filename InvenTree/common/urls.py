"""
URL lookup for common views
"""

from django.conf.urls import url, include

from . import views

currency_urls = [
    url(r'^new/', views.CurrencyCreate.as_view(), name='currency-create'),
]

common_urls = [
    url(r'currency/', include(currency_urls)),
]
