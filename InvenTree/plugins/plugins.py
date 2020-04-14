# -*- coding: utf-8 -*-

import inspect
import importlib
import pkgutil

# Barcode plugins
import plugins.barcode as barcode
from plugins.barcode.barcode import BarcodePlugin


def iter_namespace(pkg):

    return pkgutil.iter_modules(pkg.__path__, pkg.__name__ + ".")


def get_modules(pkg):
    # Return all modules in a given package
    return [importlib.import_module(name) for finder, name, ispkg in iter_namespace(barcode)]


def get_classes(module):
    # Return all classes in a given module
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
            if plugin.__class__ is type(baseclass) and plugin.PLUGIN_NAME:
                plugins.append(plugin)

    return plugins


def load_barcode_plugins():
    """
    Return a list of all registered barcode plugins
    """

    return get_plugins(barcode, BarcodePlugin)
