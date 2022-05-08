"""
URL lookup for setups
"""

from django.urls import re_path

from . import views

contact_wizard = views.ContactWizard.as_view(views.ContactWizard.form_list, url_name='setup_step', done_step_name='finished')

oobe_urls = [
    # Initial setup
    re_path(r'^oobe/(?P<step>.+)/$', contact_wizard, name='setup_step'),
    re_path(r'^oobe/', contact_wizard, name='setup'),
]
