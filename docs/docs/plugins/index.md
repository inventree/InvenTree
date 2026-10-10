---
title: Plugins
---

## InvenTree Plugin Architecture

The InvenTree server code supports an extensible plugin architecture, allowing custom plugins to be integrated directly into the InvenTree installation. This allows development of complex behaviors which are decoupled from core InvenTree code.

Plugins can be added from multiple sources:

- Plugins can be installed using the PIP Python package manager
- Plugins can be placed in the external [plugins directory](../start/config.md#plugin-options)
- InvenTree [built-in](./builtin/index.md) plugins are located within the InvenTree source code

For further information, read more about [installing plugins](./install.md).

### Configuration Options

Plugin behaviour can be controlled via the InvenTree configuration options. Refer to the [configuration guide](../start/config.md#plugin-options) for the available plugin configuration options.

## Developing a Plugin

If you are interested in developing a custom plugin for InvenTree, refer to the [plugin development guide](./develop.md). This guide provides an overview of the plugin architecture, and how to create a new plugin.

### Plugin Creator

To assist in creating a new plugin, we provide a [plugin creator command line tool](./creator.md). This allows developers to quickly scaffold a new InvenTree plugin, and provides a basic structure to build upon.

### Plugin Walkthrough

Check out our [plugin development walkthrough](./walkthrough.md) to learn how to create an example plugin. This guide will take you through the steps to add a new part panel that displays an image carousel from images attached to the selected part.

## Available Plugins

InvenTree plugins can be provided from a variety of sources, including built-in plugins, sample plugins, mandatory plugins, and third-party plugins.

### Built-in Plugins

InvenTree comes with a number of built-in plugins that provide additional functionality. These plugins are included in the InvenTree source code, and can be enabled or disabled via the configuration options.

Refer to the [built-in plugins documentation](./builtin/index.md) for more information on the available built-in plugins.

### Sample Plugins

If the InvenTree server is running in [debug mode](../start/config.md#debug-mode), an additional set of *sample* plugins are available. These plugins are intended to demonstrate some of the available capabilities provided by the InvenTree plugin architecture, and can be used as a starting point for developing your own plugins.

!!! info "Debug Mode Only"
    Sample plugins are only available when the InvenTree server is running in debug mode. This is typically used during development, and is not recommended for production environments.

### Third Party Plugins

A list of known third-party InvenTree extensions is provided [on our website](https://inventree.org/extend/integrate/) If you have an extension that should be listed here, contact the InvenTree team on [GitHub](https://github.com/inventree/). Refer to the [InvenTree website](https://inventree.org/plugins.html) for a (non exhaustive) list of plugins that are available for InvenTree. This includes both official and third-party plugins.

### PyPI

There are a number of third-party InvenTree plugins available via the [Python Package Index](https://pypi.org/) (PyPI). These plugins can be installed using the PIP package manager.

These plugins are discoverable via the `Framekwork :: InvenTree` classifier tag. To view all available InvenTree plugins on PyPI, visit the [InvenTree PyPi page](https://pypi.org/search/?c=Framework+%3A%3A+InvenTree).

!!! warning "Third-Party Plugins"
    Third-party plugins are developed and maintained by independent developers. InvenTree does not provide support for third-party plugins, and cannot guarantee their quality or security. Use third-party plugins at your own risk!

## Mandatory Plugins

Some plugins are mandatory for InvenTree to function correctly. These plugins are included in the InvenTree source code, and cannot be disabled. They provide essential functionality that is required for the core InvenTree features to work.

### Mandatory Third-Party Plugins

It may be desirable to mark a third-party plugin as mandatory, meaning that once installed, it is automatically enabled and cannot be disabled. This is useful in situations where a particular plugin is required for crucial functionality and it it imperative that it cannot be disabled by user interaction.

In such as case, the plugin(s) should be marked as "mandatory" at run-time in the [configuration file](../start/config.md#plugin-options). This will ensure that these plugins are always enabled, and cannot be disabled by the user.
