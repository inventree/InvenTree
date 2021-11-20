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


class IntegrationPluginError(Exception):
    def __init__(self, path, message):
        self.path = path
        self.message = message
    
    def __str__(self):
        return self.message


def get_plugin_error(error, do_raise: bool = False, do_log: bool = False, log_name: str = ''):
    package_path = traceback.extract_tb(error.__traceback__)[-1].filename
    install_path = sysconfig.get_paths()["purelib"]
    package_name = pathlib.Path(package_path).relative_to(install_path).parts[0]

    if do_log:
        log_kwargs = {}
        if log_name:
            log_kwargs['reference'] = log_name
        log_plugin_error({package_name: str(error)}, **log_kwargs)

    if do_raise:
        raise IntegrationPluginError(package_name, str(error))

    return package_name, str(error)
