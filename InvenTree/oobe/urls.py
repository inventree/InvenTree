"""
URL lookup for setups
"""

from django.urls import re_path

from . import views


setup_wizard = views.SetupWizard.as_view(url_name='dynamic_setup_step')

oobe_urls = [
    # Dynamic setup
    re_path(r'^(?P<setup>.+)/(?P<step>.+)/$', setup_wizard, name='dynamic_setup_step'),
    re_path(r'^(?P<setup>.+)/', setup_wizard, name='dynamic_setup'),
]
