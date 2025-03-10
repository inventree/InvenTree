---
title: User Interface Mixin
---

## User Interface Mixin

The `UserInterfaceMixin` class provides a set of methods to implement custom functionality for the InvenTree web interface.

### Enable User Interface Mixin

To enable user interface plugins, the global setting `ENABLE_PLUGINS_INTERFACE` must be enabled, in the [plugin settings](../../settings/global.md#plugin-settings).

## Custom UI Features

The InvenTree user interface functionality can be extended in various ways using plugins. Multiple types of user interface *features* can be added to the InvenTree user interface.

The entrypoint for user interface plugins is the `UserInterfaceMixin` class, which provides a number of methods which can be overridden to provide custom functionality. The `get_ui_features` method is used to extract available user interface features from the plugin:

::: plugin.base.ui.mixins.UserInterfaceMixin.get_ui_features
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      show_sources: True
      summary: False
      members: []

Note here that the `get_ui_features` calls other methods to extract the available features from the plugin, based on the requested feature type. These methods can be overridden to provide custom functionality.

!!! info "Implementation"
    Your custom plugin does not need to override the `get_ui_features` method. Instead, override one of the other methods to provide custom functionality.

### UIFeature Return Type

The `get_ui_features` method should return a list of `UIFeature` objects, which define the available user interface features for the plugin. The `UIFeature` class is defined as follows:

::: plugin.base.ui.mixins.UIFeature
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      show_sources: True
      summary: False
      members: []

Note that the *options* field contains fields which may be specific to a particular feature type - read the documentation below on each feature type for more information.

### Dynamic Feature Loading

Each of the provided feature types can be loaded dynamically by the plugin, based on the information provided in the API request. For example, the plugin can choose to show or hide a particular feature based on the user permissions, or the current state of the system.

For examples of this dynamic feature loading, refer to the [sample plugin](#sample-plugin) implementation which demonstrates how to dynamically load custom panels based on the provided context.

### Javascript Source Files

The rendering function for the custom user interface features expect that the plugin provides a Javascript source file which contains the necessary code to render the custom content. The path to this file should be provided in the `source` field of the `UIFeature` object.

Note that the `source` field can include the name of the function to be called (if this differs from the expected default function name).

For example:

```
"source": "/static/plugins/my_plugin/my_plugin.js:my_custom_function"
```

## Available UI Feature Types

The following user interface feature types are available:

### Dashboard Items

The InvenTree dashboard is a collection of "items" which are displayed on the main dashboard page. Custom dashboard items can be added to the dashboard by implementing the `get_ui_dashboard_items` method:

::: plugin.base.ui.mixins.UserInterfaceMixin.get_ui_dashboard_items
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      show_sources: True
      summary: False
      members: []

#### Dashboard Item Options

The *options* field in the returned `UIFeature` object can contain the following properties:

::: plugin.base.ui.mixins.CustomDashboardItemOptions
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      show_sources: True
      summary: False
      members: []

#### Source Function

The frontend code expects a path to a javascript file containing a function named `renderDashboardItem` which will be called to render the custom dashboard item. Note that this function name can be overridden by appending the function name in the `source` field of the `UIFeature` object.

#### Example

Refer to the [sample plugin](#sample-plugin) for an example of how to implement server side rendering for custom panels.

### Panels

Many of the pages in the InvenTree web interface are built using a series of "panels" which are displayed on the page. Custom panels can be added to these pages, by implementing the `get_ui_panels` method:

::: plugin.base.ui.mixins.UserInterfaceMixin.get_ui_panels
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      show_sources: True
      summary: False
      members: []

#### Panel Options

The *options* field in the returned `UIFeature` object can contain the following properties:

::: plugin.base.ui.mixins.CustomPanelOptions
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      show_sources: True
      summary: False
      members: []

#### Source Function

The frontend code expects a path to a javascript file containing a function named `renderPanel` which will be called to render the custom panel. Note that this function name can be overridden by appending the function name in the `source` field of the `UIFeature` object.

#### Example

Refer to the [sample plugin](#sample-plugin) for an example of how to implement server side rendering for custom panels.

### Template Editors

The `get_ui_template_editors` feature type can be used to provide custom template editors.

::: plugin.base.ui.mixins.UserInterfaceMixin.get_ui_template_editors
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      show_sources: True
      summary: False
      members: []

### Template previews

The `get_ui_template_previews` feature type can be used to provide custom template previews:

::: plugin.base.ui.mixins.UserInterfaceMixin.get_ui_template_previews
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      show_sources: True
      summary: False
      members: []

## Plugin Context

When rendering certain content in the user interface, the rendering functions are passed a `context` object which contains information about the current page being rendered. The type of the `context` object is defined in the `PluginContext` file:

{{ includefile("src/frontend/src/components/plugins/PluginContext.tsx", title="Plugin Context", fmt="javascript") }}

This context data can be used to provide additional information to the rendering functions, and can be used to dynamically render content based on the current state of the system.

### Additional Context

Note that additional context can be passed to the rendering functions by adding additional key-value pairs to the `context` field in the `UIFeature` return type (provided by the backend via the API). This field is optional, and can be used at the discretion of the plugin developer.

## File Distribution

When distributing a custom UI plugin, the plugin should include the necessary frontend code to render the custom content. This frontend code should be included in the plugin package, and should be made available to the InvenTree frontend when the plugin is installed.

The simplest (and recommended) way to achieve this is to distribute the compiled javascript files with the plugin package, in a top-level `static` directory. This directory will be automatically collected by InvenTree when the plugin is installed, and the files will be copied to the appropriate location.

Read more about [static plugin files](../plugins.md#static-files) for more information.

## Sample Plugin

A (very simple) sample plugin which implements custom user interface functionality is provided in the InvenTree source code, which provides a full working example of how to implement custom user interface functionality.

::: plugin.samples.integration.user_interface_sample.SampleUserInterfacePlugin
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []

### More Examples

Some more complex examples of user interface plugins can be found on the InvenTree GitHub repository:

- [inventree-test-statistics](https://github.com/inventree/inventree-test-statistics)
- [inventree-order-history](https://github.com/inventree/inventree-order-history)

## Consistent Theming

When developing a custom UI plugin for InvenTree, the plugin should aim to match the existing InvenTree theme as closely as possible. This will help to ensure that the custom content fits seamlessly into the existing user interface.

To achieve this, we strongly recommend that you use the same framework as the InvenTree frontend - which is built using [React](https://react.dev) on top of the [Mantine](https://mantine.dev) UI component library.

### Mantine

The Mantine UI component library is used throughout the InvenTree frontend, and provides a consistent look and feel to the user interface. By using Mantine components in your custom UI plugin, you can ensure that your custom content fits seamlessly into the existing InvenTree theme.

### InvenTree Component Library

We are working to develop and distribute a library of custom InvenTree components which can be used to build custom UI plugins. This library will be made available to plugin developers in the near future.

### Examples

Refer to some of the existing InvenTree plugins linked above for examples of building custom UI plugins using the Mantine component library for seamless integration.
