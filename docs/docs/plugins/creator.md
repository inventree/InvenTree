---
title: Plugin Creator
---

## Plugin Creator Tool

The plugin framework provided for InvenTree is powerful and flexible - which also means that it can be a bit complex to get started, especially for new developers.

To assist in creating a new plugin, we provide a [plugin creator command line tool](https://github.com/inventree/plugin-creator).

This tool allows developers to quickly scaffold a new InvenTree plugin, and provides a basic structure to build upon.

The plugin creator tool allows the developer to select which plugin features they wish to include, and generates a basic plugin structure with the selected features.

This page provides an overview of how to install and use the plugin creator tool, as well as some tips for creating your own plugins. The documentation here uses the "default" options as provided by the plugin creator tool, but you can customize the options to suit your needs.

### Features

The plugin creator tool provides a number of features to help you get started with plugin development:

- **Metadata Input**: Easily input metadata for your plugin, including name, description, and author information.
- **License Selection**: Choose from a variety of licenses for your plugin, with "MIT" as the default.
- **Feature Selection**: Select which plugin features you want to include, such as mixins and frontend features.
- **Devops Integration**: Optionally set up Git version control, automatic code formatting, and other development tools.
- **Deploy Support**: Generate a basic structure for your plugin that can be easily deployed to an InvenTree instance, and published to PyPI.
- **Frontend Development**: Set up a development server for frontend features, including hot reloading and build tools.

## Installation

To get started using the creator tool, you will need to install it via PIP:

```bash
pip install -U inventree-plugin-creator
```

## Create Plugin

Begin the plugin creation process by running the following command:

```bash
create-inventree-plugin
```

### Plugin Metadata

Firstly, you will enter the metadata for the plugin:

{{ image("plugin/plugin-creator-metadata.png", "Plugin Metadata") }}

### License

Select the license for your plugin. The default is "MIT", but you can choose from a variety of licenses.

{{ image("plugin/plugin-creator-license.png", "Plugin License") }}

### Plugin Features

Next, the creator tool will prompt you to select the features you wish to include in your plugin.

#### Select Mixins

Select the [plugin mixins](./index.md/#plugin-mixins) you wish to use in your plugin:

{{ image("plugin/plugin-creator-mixins.png", "Plugin Mixins") }}

#### Select Frontend Features

If you selected the  *UserInterfaceMixin* in the previous step (as we did in this example), you will be prompted to select the frontend features you wish to include in your plugin:

The available frontend features include:

- **Custom dashboard items**: Create custom dashboard widgets for the InvenTree user interface.
- **Custom panel items**: Add custom panels to the InvenTree interface.
- **Custom settings display**: Create custom settings pages for your plugin.

{{ image("plugin/plugin-creator-frontend.png", "Plugin Frontend Features") }}

### Git Setup

If you wish to include Git integration in your plugin, you can select the options here. This will set up a Git repository for your plugin, and configure automatic code formatting using [pre-commit](https://pre-commit.com/).

Additionally, you can choose to setup CI integration (for either GitHub or GitLab) to automatically run tests and checks on your plugin code.

{{ image("plugin/plugin-creator-devops.png", "Plugin DevOps Features") }}


## Install Plugin

The plugin has now been created - it will be located in the directory you specified during the creation process.

In the example above, we created a plugin called "MyCustomPlugin". We can verify that the plugin files have been created:

```bash
cd MyCustomPlugin
ls -l
```

You should see a directory structure similar to the following:

- **LICENSE**: The license file for your plugin.
- **MANIFEST.in**: A file that specifies which files should be included in the plugin package.
- **README.md**: A README file for your plugin.
- **biome.json**: Configuration file for the Biome code formatter.
- **pyproject.toml**: The project configuration file for your plugin.
- **setup.cfg**: Rules for Python code formatting and linting.
- **setup.py**: The setup script for your plugin.
- **frontend/**: A directory containing the frontend code for your plugin (if you selected frontend features).
- **my_custom_plugin/**: The main plugin directory, containing the plugin code. *(Note: the name of this directory will match the name you provided during plugin creation)*

### Editable Install

We now need to *install* the plugin (within the active Python environment) so that it can be used by InvenTree. For development purposes, we can install the plugin in [editable install](https://setuptools.pypa.io/en/latest/userguide/development_mode.html) mode, which allows us to make changes to the plugin code without needing to reinstall it.

```bash
pip install -e .
```

You should see output indicating that the plugin has been installed successfully:

{{ image("plugin/plugin-creator-install.png", "Install Editable Plugin") }}

You can also verify that the plugin has been installed by running the following command:

```bash
pip show inventree-my-custom-plugin
```

{{ image("plugin/plugin-creator-verify.png", "Verify plugin installation") }}

## Frontend Dev Server

## Build Plugin
