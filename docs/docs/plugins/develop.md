---
title: Developing Plugins
---

## Plugin Development Guide

This page serves as a short introductory guide for plugin beginners. It should be noted that there is an assumed level of familiarity with Python, Django, and the InvenTree source code.

### Plugin Creator

We strongly recommend that you use the [Plugin Creator](./creator.md) tool when first scaffolding your new plugin. This tool will help you to create a basic plugin structure, and will also provide you with a set of example files which can be used as a starting point for your own plugin development.

## Determine Requirements

Before starting, you should have a clear understanding of what you want your plugin to do. In particular, consider the functionality provided by the available [plugin mixins](./index.md#plugin-mixins), and whether your plugin can be built using these mixins.

Consider the use-case for your plugin and define the exact function of the plugin, maybe write it down in a short readme. Then pick the mixins you need (they help reduce custom code and keep the system reliable if internal calls change).

- Is it just a simple REST-endpoint that runs a function ([ActionMixin](./mixins/action.md)) or a parser for a custom barcode format ([BarcodeMixin](./mixins/barcode.md))?
- How does the user interact with the plugin? Is it a UI separate from the main InvenTree UI ([UrlsMixin](./mixins/urls.md)), does it need multiple pages with navigation-links ([NavigationMixin](./mixins/navigation.md)).
- Do you need to extend reporting functionality? Check out the [ReportMixin](./mixins/report.md).
- Will it make calls to external APIs ([APICallMixin](./mixins/api.md) helps there)?
- Do you need to run in the background ([ScheduleMixin](./mixins/schedule.md)) or when things in InvenTree change ([EventMixin](./mixins/event.md))?
- Does the plugin need configuration that should be user changeable ([SettingsMixin](./mixins/settings.md)) or static (just use a yaml in the config dir)?
- You want to receive webhooks? Do not code your own untested function, use the WebhookEndpoint model as a base and override the perform_action method.
- Do you need the full power of Django with custom models and all the complexity that comes with that – welcome to the danger zone and [AppMixin](./mixins/app.md). The plugin will be treated as a app by django and can maybe rack the whole instance.

### Define Metadata

Do not forget to [declare the metadata](./index.md#plugin-options) for your plugin, those will be used in the settings. At least provide a web link so users can file issues / reach you.

### Development Guidelines

If you want to make your life easier, try to follow these guidelines; break where it makes sense for your use case.

- Keep it simple - more that 1000 LOC are normally to much for a plugin
- Use mixins where possible - we try to keep coverage high for them so they are not likely to break
- Do not use internal functions - if a functions name starts with `_` it is internal and might change at any time
- Keep you imports clean - the APIs for plugins and mixins are young and evolving (see [here](./index.md#imports)). Use
```
from plugin import InvenTreePlugin, registry
from plugin.mixins import APICallMixin, SettingsMixin, ScheduleMixin, BarcodeMixin
```
- Feliver as a package (see [below](#packaging))
- If you need to use a private infrastructure, use the 'Releases' functions in GitHub or Gitlab. Point to the 'latest' release endpoint when installing to make sure the update function works
- Tag your GitHub repo with `inventree` and `inventreeplugins` to make discovery easier. A discovery mechanism using these tags is on the roadmap.
- Use GitHub actions to test your plugin regularly (you can [schedule actions](https://docs.github.com/en/actions/learn-github-actions/events-that-trigger-workflows#schedule)) against the 'latest' [docker-build](https://hub.docker.com/r/inventree/inventree) of InvenTree
- If you use the AppMixin pin your plugin against the stable branch of InvenTree, your migrations might get messed up otherwise


## Plugin Code Structure

### Plugin Base Class

Custom plugins must inherit from the [InvenTreePlugin class]({{ sourcefile("src/backend/InvenTree/plugin/plugin.py") }}). Any plugins installed via the methods outlined above will be "discovered" when the InvenTree server launches.

### Imports

As the code base is evolving import paths might change. Therefore we provide stable import targets for important python APIs.
Please read all release notes and watch out for warnings - we generally provide backports for depreciated interfaces for at least one minor release.

#### Plugins

General classes and mechanisms are provided under the `plugin` [namespaces]({{ sourcefile("src/backend/InvenTree/plugin/__init__.py") }}). These include:

```python
# Management objects
registry                    # Object that manages all plugin states and integrations

# Base classes
InvenTreePlugin             # Base class for all plugins

# Errors
MixinImplementationError    # Is raised if a mixin is implemented wrong (default not overwritten for example)
MixinNotImplementedError    # Is raised if a mixin was not implemented (core mechanisms are missing from the plugin)
```

#### Mixins

Plugin functionality is split between multiple "mixin" classes - each of which provides a specific set of features or behaviors that can be integrated into a plugin. These mixins are designed to be used in conjunction with the `InvenTreePlugin` base class, allowing developers to easily extend the functionality of their plugins. All public APIs that should be used are exposed under `plugin.mixins`. These include all built-in mixins and notification methods. An up-to-date reference can be found in the source code [can be found here]({{ sourcefile("src/backend/InvenTree/plugin/mixins/__init__.py") }}).

Refer to the [mixin documentation](#plugin-mixins) for a list of available mixins, and their usage.

#### Models and other internal InvenTree APIs

!!! warning "Danger Zone"
    The APIs outside of the `plugin` namespace are not structured for public usage and require a more in-depth knowledge of the Django framework. Please ask in GitHub discussions of the `InvenTree` org if you are not sure you are using something the intended way.

We do not provide stable interfaces to models or any other internal python APIs. If you need to integrate into these parts please make yourself familiar with the codebase. We follow general Django patterns and only stray from them in limited, special cases.
If you need to react to state changes please use the [EventMixin](./mixins/event.md).

### Plugin Options

Some metadata options can be defined as constants in the plugins class.

``` python
NAME = '' # Used as a general reference to the plugin
SLUG = None  # Used in URLs, setting-names etc. when a unique slug as a reference is needed -> the plugin name is used if not set
TITLE = None  # A nice human friendly name for the plugin -> used in titles, as plugin name etc.

AUTHOR = None  # Author of the plugin, git commit information is used if not present
PUBLISH_DATE = None  # Publishing date of the plugin, git commit information is used if not present
WEBSITE = None  # Website for the plugin, developer etc. -> is shown in plugin overview if set

VERSION = None  # Version of the plugin
MIN_VERSION = None  # Lowest InvenTree version number that is supported by the plugin
MAX_VERSION = None  # Highest InvenTree version number that is supported by the plugin
```

Refer to the [sample plugins]({{ sourcedir("src/backend/InvenTree/plugin/samples") }}) for further examples.

### Plugin Config

A *PluginConfig* database entry will be created for each plugin "discovered" when the server launches. This configuration entry is used to determine if a particular plugin is enabled.

The configuration entries must be enabled via the [InvenTree admin interface](../settings/admin.md).

!!! warning "Disabled by Default"
    Newly discovered plugins are disabled by default, and must be manually enabled (in the admin interface) by a user with staff privileges.

## Plugin Mixins

Common use cases are covered by pre-supplied modules in the form of *mixins* (similar to how [Django]({% include "django.html" %}/topics/class-based-views/mixins/) does it). Each mixin enables the integration into a specific area of InvenTree. Sometimes it also enhances the plugin with helper functions to supply often used functions out-of-the-box.

Supported mixin classes are:

| Mixin | Description |
| --- | --- |
| [ActionMixin](./mixins/action.md) | Run custom actions |
| [APICallMixin](./mixins/api.md) | Perform calls to external APIs |
| [AppMixin](./mixins/app.md) | Integrate additional database tables |
| [BarcodeMixin](./mixins/barcode.md) | Support custom barcode actions |
| [CurrencyExchangeMixin](./mixins/currency.md) | Custom interfaces for currency exchange rates |
| [DataExport](./mixins/export.md) | Customize data export functionality |
| [EventMixin](./mixins/event.md) | Respond to events |
| [LabelPrintingMixin](./mixins/label.md) | Custom label printing support |
| [LocateMixin](./mixins/locate.md) | Locate and identify stock items |
| [MachineDriverMixin](./mixins/machine.md) | Integrate custom machine drivers
| [MailMixin](./mixins/mail.md) | Send custom emails |
| [NavigationMixin](./mixins/navigation.md) | Add custom pages to the web interface |
| [NotificationMixin](./mixins/notification.md) | Send custom notifications in response to system events |
| [ReportMixin](./mixins/report.md) | Add custom context data to reports |
| [ScheduleMixin](./mixins/schedule.md) | Schedule periodic tasks |
| [SettingsMixin](./mixins/settings.md) | Integrate user configurable settings |
| [UserInterfaceMixin](./mixins/ui.md) | Add custom user interface features |
| [UrlsMixin](./mixins/urls.md) | Respond to custom URL endpoints |
| [ValidationMixin](./mixins/validation.md) | Provide custom validation of database models |

## Plugin Concepts

### Backend vs Frontend Code

InvenTree plugins can contain both backend and frontend code. The backend code is written in Python, and is used to implement server-side functionality, such as database models, API endpoints, and background tasks.

The frontend code is written in JavaScript (or TypeScript), and is used to implement user interface components, such as custom UI panels.

You can [read more about frontend integration](./frontend.md) to learn how to integrate custom UI components into the InvenTree web interface.

## Static Files

If your plugin requires static files (e.g. CSS, JavaScript, images), these should be placed in the top level `static` directory within the distributed plugin package. These files will be automatically collected by InvenTree when the plugin is installed, and copied to an appropriate location.

These files will be available to the InvenTree web interface, and can be accessed via the URL `/static/plugins/<plugin_name>/<filename>`. Static files are served by the [proxy server](../start/processes.md#proxy-server).

For example, if the plugin is named `my_plugin`, and contains a file `CustomPanel.js`, it can be accessed via the URL `/static/plugins/my_plugin/CustomPanel.js`.

### Packaging

!!! tip "Package-Discovery can be tricky"
    Most problems with packaging stem from problems with discovery. [This guide](https://setuptools.pypa.io/en/latest/userguide/package_discovery.html#automatic-discovery) by the PyPA contains a lot of information about discovery during packaging. These mechanisms generally apply to most discovery processes in InvenTree and the wider Django ecosystem.

The recommended way of distribution is as a [PEP 561](https://peps.python.org/pep-0561/) compliant package. If you can use the official Package Index (PyPi - [official website](https://pypi.org/)) as a registry.
Please follow PyPAs official [packaging guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/) to ensure your package installs correctly suing InvenTrees install mechanisms.

Your package must expose you plugin class as an [entrypoint](https://setuptools.pypa.io/en/latest/userguide/entry_point.html) with the name `inventree_plugins` to work with InvenTree.

```setup.cfg
# Example setup.cfg
[options.entry_points]
inventree_plugins =
        ShopifyIntegrationPlugin = path.to.source:ShopifyIntegrationPluginClass
```

```setup.py
# Example setup.py

import setuptools

# ...

setuptools.setup(
    name='ShopifyIntegrationPlugin'
    .# ..

    entry_points={"inventree_plugins": ["ShopifyIntegrationPlugin = path.to.source:ShopifyIntegrationPluginClass"]}
```

#### Including Extra Files

In some cases you may wish to copy across extra files when the package is installed. For example, you may have custom template files which need to be copied across to the installation directory.

In this case, you will need to include a `MANIFEST.in` file in the root directory of your plugin, and include the line `include_package_data=True` in your `setup.py` file.

!!! tip "Setuptools Documentation"
    Read more about `MANIFEST.in` in the [setuptools documentation](https://setuptools.pypa.io/en/latest/userguide/miscellaneous.html)

As an example, you have a plugin codebase with the following directory structure:

```
- my_plugin  # Core plugin code
- my_plugin/templates/  # Template files
- MANIFEST.in  # Manifest file
- setup.py  # Setuptools script
```

To ensure that the templates are copied into the installation directory, `MANIFEST.in` should look like:

```
recursive-include my_plugin/templates *
```

Other files and directories can be copied in a similar manner.

### Local Plugin Development

If you are developing a plugin (either from scratch, or making changes to an existing plugin), it can be useful to install the plugin using an [editable install](https://setuptools.pypa.io/en/latest/userguide/development_mode.html).

An *editable install* installs the plugin (via PIP) into your local python virtual environment, but does not *copy* the code into the environment. Instead, it loads the code directly from where it is located, and also monitors for live changes in the code. This means that you can make changes to the plugin on the fly, and the InvenTree development server will detect any code changes and re-load the plugin automatically.

Note that to use an *editable install*, your plugin must be installable via PIP.

#### Example

To setup an editable install:

- Download the source code for the plugin (or create a new plugin)
- Ensure that your setup file (either `setup.py` or `pyproject.toml`) is valid
- Launch a command line and activate your development virtual environment
- `cd` into the top-level directory of your plugin project, where the setup file is located
- Setup an editable install with the following command:

```bash
pip install --editable .
```

### Simple Example

This example adds a new action under `/api/action/sample` using the ActionMixin.
``` py
# -*- coding: utf-8 -*-
"""sample implementation for ActionPlugin"""
from plugin import InvenTreePlugin
from plugin.mixins import ActionMixin


class SampleActionPlugin(ActionMixin, InvenTreePlugin):
    """Use docstrings for everything."""

    NAME = "SampleActionPlugin"
    ACTION_NAME = "sample"

    # metadata
    AUTHOR = "Sample Author"
    DESCRIPTION = "A very basic plugin with one mixin"
    PUBLISH_DATE = "2222-02-22"
    VERSION = "1.2.3"  # We recommend semver and increase the major version with each new major release of InvenTree
    WEBSITE = "https://example.com/"
    LICENSE = "MIT"  # use what you want - OSI approved is &hearts;

    # Everything form here is for the ActionMixin
    def perform_action(self):
        print("Action plugin in action!")

    def get_info(self):
        return {
            "user": self.user.username,
            "hello": "world",
        }

    def get_result(self):
        return True  # This is returned to the client
```
