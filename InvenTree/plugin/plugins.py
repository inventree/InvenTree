# -*- coding: utf-8 -*-
"""general functions for plugin handeling"""

import inspect
import importlib
import pkgutil
import logging

# Action plugins
import plugin.builtin.action as action
from plugin.action import ActionPlugin

import plugin.samples.integration as integration
from plugin.integration import IntegrationPluginBase


logger = logging.getLogger("inventree")


def iter_namespace(pkg):
    """get all modules in a package"""
    return pkgutil.iter_modules(pkg.__path__, pkg.__name__ + ".")


def get_modules(pkg):
    """get all modules in a package"""
    return [importlib.import_module(name) for finder, name, ispkg in iter_namespace(pkg)]


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


def load_plugins(name: str, cls, module=None):
    """general function to load a plugin class

    :param name: name of the plugin for logs
    :type name: str
    :param module: module from which the plugins should be loaded
    :return: class of the to-be-loaded plugin
    """

    logger.debug("Loading %s plugins", name)

    plugins = get_plugins(module, cls)

    if len(plugins) > 0:
        logger.info("Discovered %i %s plugins:", len(plugins), name)

        for plugin in plugins:
            logger.debug(" - %s", plugin.PLUGIN_NAME)

    return plugins


def load_action_plugins():
    """
    Return a list of all registered action plugins
    """
    return load_plugins('action', ActionPlugin, module=action)


def load_integration_plugins():
    """
    Return a list of all registered integration plugins
    """
    return load_plugins('integration', IntegrationPluginBase, module=integration)


def load_barcode_plugins():
    """
    Return a list of all registered barcode plugins
    """
    from barcodes import plugins as BarcodePlugins
    from barcodes.barcode import BarcodePlugin

    return load_plugins('barcode', BarcodePlugins, module=BarcodePlugin)
