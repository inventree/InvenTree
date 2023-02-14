"""URL lookup for supplier plugin."""

from django.urls import re_path

from . import views

plugin_supplier_urls = [
    re_path(r'.*$', views.PluginSupplierIndex.as_view(), name='plugin-supplier-index'),
]
