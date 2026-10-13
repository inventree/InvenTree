---
title: Installing Plugins
---


## Installing a Plugin

Plugins can either be loaded from paths in the InvenTree install directory or as a plugin installed via pip. We recommend installation via pip as this enables hassle-free upgrades.

### Common Issues

Installing plugins can be complex! Some common issues are outlined below:

#### Enable Plugin Support

To enable custom plugins, plugin support must be activated in the [server configuration](../start/config.md#plugin-options). This step must be performed by a system administrator before the InvenTree server is started.

#### Restart Server

Plugins installed, updated or removed via the web interface are reloaded automatically, by both the web server and background worker. However, some changes (such as installing plugins from the command line, or updating plugin dependencies) still require both the web server and background worker to be restarted. Refer to [reloading plugins](#reloading-plugins) for further details.

#### Container Environments

In certain container environments (such as docker), plugins are installed into an *ephemeral* virtual environment which persists only for the lifetime of the container. To allow for this, InvenTree provides a configurable setting which can automatically install plugins whenever the container is loaded.

!!! tip "Check Plugins on Startup"
    Ensure the **Check Plugins on Startup** option is enabled, when running InvenTree in a container environment!

{{ image("plugin/check_on_startup.png", "Check plugins on startup") }}

### Installation Methods

#### Builtin Plugins

Builtin plugins ship in `src/backend/InvenTree/plugin/builtin`. To achieve full unit-testing for all mixins there are some sample implementations in `src/backend/InvenTree/plugin/samples`.

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
    The location of your plugin configuration file will depend on your [server configuration](../start/config.md)

#### Web Interface

Admin users can install plugins directly from the web interface, via the "Plugin Settings" view:

{{ image("plugin/plugin_install_web.png", "Install plugin via web interface") }}

Enter the package name into the form as shown below. You can add a path and a version. Leave the version field empty for the latest version. In case the package is on pypi the path can be omitted. Pip will find it automatically.

{{ image("plugin/plugin_install_git.png", "Install plugin from git") }}

!!! success "Plugin File"
    A plugin installed via the web interface is added to the [plugins.txt](#plugin-installation-file-pip) plugin file as shown below.

{{ image("plugin/plugin_install_txt.png", "Plugin.txt file") }}

!!! info "Superuser Required"
    Only users with superuser privileges can manage plugins via the web interface.

#### Local Directory

Custom plugins can be placed in the `data/plugins/` directory, where they will be automatically discovered. This can be useful for developing and testing plugins, but can prove more difficult in production (e.g. when using Docker).

!!! info "Git Tracking"
    The `data/plugins/` directory is excluded from Git version tracking - any plugin files here will be hidden from Git

!!! warning "Not Recommended For Production"
    Loading plugins via the local *plugins* directory is not recommended for production. If you cannot use PIP installation (above), specify a custom plugin directory (below) or use a [VCS](https://pip.pypa.io/en/stable/topics/vcs-support/) as a plugin install source.

#### Custom Directory

If you wish to install plugins from local source, rather than PIP, it is better to place your plugins in a directory outside the InvenTree source directory.

To achieve this, set the `INVENTREE_PLUGIN_DIR` environment variable to the directory where locally sourced plugins are located. Refer to the [configuration options](../start/config.md#plugin-options) for further information.

!!! info "Docker"
    When running InvenTree in docker, a *plugins* directory is automatically created in the mounted data volume. Any plugins can be placed there, and will be automatically loaded when the server is started.

## Reloading Plugins

When the plugin configuration is changed from within InvenTree, the plugin registry is reloaded automatically - there is no need to restart the server.

The server process which performs the change reloads its plugin registry immediately, and records the new state of the registry in the database. Every other server process (e.g. additional web server workers, and the background worker) detects this change the next time it accesses the plugin registry, and reloads its own plugins to match. As part of this reload, the code of each installed plugin package is re-imported from disk, so that every process runs the same (updated) plugin version.

### Automatic Reload

The following changes are applied automatically, without restarting the server:

| Change | Notes |
| --- | --- |
| Install a plugin package via the [web interface](#web-interface) (or API) | |
| Update a plugin package to a new version via the web interface (or API) | The plugin's own package is reloaded - see [restart required](#restart-required) if the update also changes its dependencies |
| Uninstall a plugin via the web interface (or API) | |
| Activate or deactivate a plugin | |
| Change a plugin integration setting (e.g. *Enable URL integration*) | |

!!! info "Version Number"
    Other server processes detect a change by comparing the plugin registry state - which includes the name, version and active status of each loaded plugin. If a plugin is updated *without* changing its version number (e.g. reinstalling from a git branch), other server processes may continue to run the previous code until they are restarted.

### Restart Required

The following changes are *not* detected automatically. After making any of these changes, restart both the web server and the background worker:

| Change | Reason |
| --- | --- |
| Plugins installed, updated or removed from the command line (e.g. `pip install`, `invoke plugins`, or editing the [plugins file](#plugin-installation-file-pip)) | InvenTree is not notified of changes made outside of the server |
| A plugin update which also installs or updates *other* packages (dependencies) | Only the plugin's own package is re-imported - any dependencies which were already loaded continue to run the old code |
| Plugins which include compiled (binary) extension modules | Compiled modules cannot be re-imported by a running process |
| Plugins which add or change database models (via the [AppMixin](./mixins/app.md)) | Database migrations are not run automatically - run `invoke migrate` first, then restart the server |
| Changes to plugins in a [local](#local-directory) or [custom](#custom-directory) plugin directory | Changes to plugin source files are not detected while the server is running |
| Changes to plugin options in the [server configuration](../start/config.md#plugin-options) | Server configuration is only read at startup |

### Plugin Registry Mismatch

If a server process reloads its plugins, but still cannot reproduce the plugin registry state of the other processes (for example, because it has loaded a different version of a plugin), it reports a *Plugin Registry Mismatch* error ([INVE-E20](../settings/error_codes.md#inve-e20)). This error is recorded in the [error log](../settings/logs.md), and staff users are notified.

The error data lists the plugins (and versions) which are loaded by the affected process. After reporting the error, the affected process stops reloading its plugins until the registry state changes again, which prevents an endless reload loop between processes.

To resolve this error, restart all InvenTree server and background worker processes.

!!! tip "Reload Plugins"
    The *Reload Plugins* button in the plugin settings view reloads the plugin registry for the web server process which handles the request. Other server processes only follow if the reload changes the plugin registry state (see above). If in doubt, restart the server.

!!! info "Debug Mode"
    When running the [development server](../develop/index.md) in debug mode, the server is automatically restarted whenever a loaded source file is changed - including installed plugin files. This does not apply to the background worker, or to production deployments.
