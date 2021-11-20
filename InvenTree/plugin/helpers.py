"""Helpers for plugin app"""
from django.conf import settings


def log_plugin_error(error, reference: str = 'general'):
    # make sure the registry is set up
    if reference not in settings.INTEGRATION_ERRORS:
        settings.INTEGRATION_ERRORS[reference] = []

    # add error to stack
    settings.INTEGRATION_ERRORS[reference].append(error)
