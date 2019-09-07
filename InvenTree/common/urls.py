"""
URL lookup for common views
"""

from django.conf.urls import url, include

from . import views

currency_urls = [
    url(r'^new/', views.CurrencyCreate.as_view(), name='currency-create'),

    url(r'^(?P<pk>\d+)/edit/', views.CurrencyEdit.as_view(), name='currency-edit'),
    url(r'^(?P<pk>\d+)/delete/', views.CurrencyDelete.as_view(), name='currency-delete'),
]

common_urls = [
    url(r'currency/', include(currency_urls)),
]
