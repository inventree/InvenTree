---
title: Developing Plugins
---

## How to Develop a Plugin

A short introductory guide for plugin beginners.

### Should it be a plugin?
First of all figure out what your plugin / code should do.
If you want to change how InvenTree base mechanics and business logic work, a plugin will not be sufficient. Maybe fork the project or better [start a discussion](https://github.com/inventree/InvenTree/discussions) on GitHub. There might be an easier / established way to do what you want.

If you want to remove parts of the user interface -> remove the permissions for those objects / actions and the users will not see them.

If you add a lot of code (over ~1000 LOC) maybe split it into multiple plugins to make upgrading and testing simpler.

### It will be a plugin!
Great. Now please read the [plugin documentation](./plugins.md) to get an overview of the architecture. It is rather short as a the (builtin) mixins come with extensive docstrings.

### Pick your building blocks
Consider the usecase for your plugin and define the exact function of the plugin, maybe write it down in a short readme. Then pick the mixins you need (they help reduce custom code and keep the system reliable if internal calls change).

- Is it just a simple REST-endpoint that runs a function ([ActionMixin](./plugins/action.md)) or a parser for a custom barcode format ([BarcodeMixin](./plugins/barcode.md))?
- How does the user interact with the plugin? Is it a UI separate from the main InvenTree UI ([UrlsMixin](./plugins/urls.md)), does it need multiple pages with navigation-links ([NavigationMixin](./plugins/navigation.md)).
- Do you need to extend reporting functionality? Check out the [ReportMixin](./plugins/report.md).
- Will it make calls to external APIs ([APICallMixin](./plugins/api.md) helps there)?
- Do you need to run in the background ([ScheduleMixin](./plugins/schedule.md)) or when things in InvenTree change ([EventMixin](./plugins/event.md))?
- Does the plugin need configuration that should be user changeable ([SettingsMixin](./plugins/settings.md)) or static (just use a yaml in the config dir)?
- You want to receive webhooks? Do not code your own untested function, use the WebhookEndpoint model as a base and override the perform_action method.
- Do you need the full power of Django with custom models and all the complexity that comes with that – welcome to the danger zone and [AppMixin](./plugins/app.md). The plugin will be treated as a app by django and can maybe rack the whole instance.

### Define the metadata
Do not forget to [declare the metadata](./plugins.md#plugin-options) for your plugin, those will be used in the settings. At least provide a weblink so users can file issues / reach you.

### Development guidelines
If you want to make your life easier, try to follow these guidelines; break where it makes sense for your use case.

- keep it simple - more that 1000 LOC are normally to much for a plugin
- use mixins where possible - we try to keep coverage high for them so they are not likely to break
- do not use internal functions - if a functions name starts with `_` it is internal and might change at any time
- keep you imports clean - the APIs for plugins and mixins are young and evolving (see [here](plugins.md#imports)). Use
```
from plugin import InvenTreePlugin, registry
from plugin.mixins import APICallMixin, SettingsMixin, ScheduleMixin, BarcodeMixin
```
- deliver as a package (see [below](#packaging))
- if you need to use a private infrastructure, use the 'Releases' functions in GitHub or Gitlab. Point to the 'latest' release endpoint when installing to make sure the update function works
- tag your GitHub repo with `inventree` and `inventreeplugins` to make discovery easier. A discovery mechanism using these tags is on the roadmap.
- use GitHub actions to test your plugin regularly (you can [schedule actions](https://docs.github.com/en/actions/learn-github-actions/events-that-trigger-workflows#schedule)) against the 'latest' [docker-build](https://hub.docker.com/r/inventree/inventree) of InvenTree
- if you use the AppMixin pin your plugin against the stable branch of InvenTree, your migrations might get messed up otherwise

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


### A simple example
This example adds a new action under `/api/action/sample` using the ActionMixin.
``` py
# -*- coding: utf-8 -*-
"""sample implementation for ActionPlugin"""
from plugin import InvenTreePlugin
from plugin.mixins import ActionMixin


class SampleActionPlugin(ActionMixin, InvenTreePlugin):
    """
    Use docstrings for everything... pls
    """

    NAME = "SampleActionPlugin"
    ACTION_NAME = "sample"

    # metadata
    AUTHOR = "Sample Author"
    DESCRIPTION = "A very basic plugin with one mixin"
    PUBLISH_DATE = "22.02.2222"
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
