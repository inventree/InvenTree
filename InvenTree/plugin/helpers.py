"""Helpers for plugin app"""
import pathlib
import sysconfig
import traceback

from django.conf import settings


def log_plugin_error(error, reference: str = 'general'):
    # make sure the registry is set up
    if reference not in settings.INTEGRATION_ERRORS:
        settings.INTEGRATION_ERRORS[reference] = []

    # add error to stack
    settings.INTEGRATION_ERRORS[reference].append(error)

def get_plugin_error(error):
    package_path = traceback.extract_tb(error.__traceback__)[-1].filename
    install_path = sysconfig.get_paths()["purelib"]
    package_name = pathlib.Path(package_path).relative_to(install_path).parts[0]
    return package_name, str(error)
