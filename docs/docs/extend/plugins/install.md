---
title: Installing Plugins
---


## Installing a Plugin

Plugins can either be loaded from paths in the InvenTree install directory or as a plugin installed via pip. We recommend installation via pip as this enables hassle-free upgrades.

### Common Issues

Installing plugins can be complex! Some common issues are outlined below:

#### Enable Plugin Support

To enable custom plugins, plugin support must be activated in the [server configuration](../../start/config.md#plugin-options). This step must be performed by a system administrator before the InvenTree server is started.

#### Restart Server

Plugins are discovered and loaded only when the server is started. When new plugins are installed (and activated), both the web server and background worker must be restarted.

#### Container Environments

In certain container environments (such as docker), plugins are installed into an *ephemeral* virtual environment which persists only for the lifetime of the container. To allow for this, InvenTree provides a configurable setting which can automatically install plugins whenever the container is loaded.

!!! tip "Check Plugins on Startup"
    Ensure the **Check Plugins on Startup** option is enabled, when running InvenTree in a container environment!

{% with id="check_plugins", url="plugin/check_on_startup.png", description="Check plugins on startup" %}
{% include 'img.html' %}
{% endwith %}

### Installation Methods

#### Builtin Plugins

Builtin plugins ship in `src/InvenTree/plugin/builtin`. To achieve full unit-testing for all mixins there are some sample implementations in `src/InvenTree/plugin/samples`.

!!! success "Builtin Plugins"
    Builtin plugins are always enabled, as they are required for core InvenTree functionality

!!! info "Debug Only"
    The sample plugins are not loaded in production mode.

#### Plugin Installation File (PIP)

Plugins installation can be simplified by providing a list of plugins in a plugin configuration file. This file (by default, *plugins.txt* in the same directory as the server configuration file) contains a list of required plugin packages.

Plugins can be then installed from this file by simply running the command `invoke plugins`.

Installation via PIP (using the *plugins.txt* file) provides a number of advantages:

- Any required secondary packages are installed automatically
- You can update plugins simply by specifying version numbers in *plugins.txt*
- Migrating plugins between systems is simplified
- You can install plugins via any source supported by PIP

!!! success "Auto Update"
    When the server installation is updated via the `invoke update` command, the plugins (as specified in *plugins.txt*) will also be updated automatically.

!!! info "Plugin File Location"
    The location of your plugin configuration file will depend on your [server configuration](../../start/config.md)

#### Web Interface

Admin users can install plugins directly from the web interface, via the "Plugin Settings" view:

{% with id="plugin_install", url="plugin/plugin_install_web.png", description="Install via web interface" %}
{% include 'img.html' %}
{% endwith %}

!!! success "Plugin File"
    A plugin installed via the web interface is added to the [plugins.txt](#plugin-installation-file-pip) plugin file.

#### Local Directory

Custom plugins can be placed in the `src/InvenTree/plugins/` directory, where they will be automatically discovered. This can be useful for developing and testing plugins, but can prove more difficult in production (e.g. when using Docker).

!!! info "Git Tracking"
    The `src/InvenTree/plugins/` directory is excluded from Git version tracking - any plugin files here will be hidden from Git

!!! warning "Not Recommended For Production"
    Loading plugins via the local *plugins* directory is not recommended for production. If you cannot use PIP installation (above), specify a custom plugin directory (below) or use a [VCS](https://pip.pypa.io/en/stable/topics/vcs-support/) as a plugin install source.

#### Custom Directory

If you wish to install plugins from local source, rather than PIP, it is better to place your plugins in a directory outside the InvenTree source directory.

To achieve this, set the `INVENTREE_PLUGIN_DIR` environment variable to the directory where locally sourced plugins are located. Refer to the [configuration options](../../start/config.md#plugin-options) for further information.

!!! info "Docker"
    When running InvenTree in docker, a *plugins* directory is automatically created in the mounted data volume. Any plugins can be placed there, and will be automatically loaded when the server is started.
