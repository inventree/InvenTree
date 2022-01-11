# -*- coding: utf-8 -*-
"""general functions for plugin handeling"""

import inspect
import pkgutil

from django.core.exceptions import AppRegistryNotReady


def get_modules(pkg):
    """get all modules in a package"""
    from plugin.helpers import log_error

    context = {}
    for loader, name, ispkg in pkgutil.walk_packages(pkg.__path__):
        try:
            module = loader.find_module(name).load_module(name)
            pkg_names = getattr(module, '__all__', None)
            for k, v in vars(module).items():
                if not k.startswith('_') and (pkg_names is None or k in pkg_names):
                    context[k] = v
            context[name] = module
        except AppRegistryNotReady:
            pass
        except Exception as error:
            # this 'protects' against malformed plugin modules by more or less silently failing

            # log to stack
            log_error({name: str(error)}, 'discovery')

    return [v for k, v in context.items()]


def get_classes(module):
    """get all classes in a given module"""
    return inspect.getmembers(module, inspect.isclass)


def get_plugins(pkg, baseclass):
    """
    Return a list of all modules under a given package.

    - Modules must be a subclass of the provided 'baseclass'
    - Modules must have a non-empty PLUGIN_NAME parameter
    """

    plugins = []

    modules = get_modules(pkg)

    # Iterate through each module in the package
    for mod in modules:
        # Iterate through each class in the module
        for item in get_classes(mod):
            plugin = item[1]
            if issubclass(plugin, baseclass) and plugin.PLUGIN_NAME:
                plugins.append(plugin)

    return plugins
