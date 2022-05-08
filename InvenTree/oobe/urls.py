"""
URL lookup for setups
"""

from django.urls import re_path

from . import views


setup_wizard = views.SetupWizard.as_view(views.SetupWizard.form_list, url_name='setup_step', done_step_name='finished')

oobe_urls = [
    # Initial setup
    re_path(r'^oobe/(?P<step>.+)/$', setup_wizard, name='setup_step'),
    re_path(r'^oobe/', setup_wizard, name='setup'),
]
