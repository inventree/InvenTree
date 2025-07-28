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
pip install inventree-plugin-creator
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

#### Frontend Features

If the UI mixin is selected, you will be prompted to select the frontend features you wish to include in your plugin:

{{ image("plugin/plugin-creator-frontend.png", "Plugin Frontend Features") }}

### Git Setup

If you wish to include Git integration in your plugin, you can select the options here:

{{ image("plugin/plugin-creator-devops.png", "Plugin DevOps Features") }}

## Install Plugin

The plugin has now been created - it will be located in the directory you specified during the creation process.

In the example above, we created a plugin called "MyCustomPlugin".

```bash
cd MyCustomPlugin
```



## Frontend Dev Server

## Build Plugin
