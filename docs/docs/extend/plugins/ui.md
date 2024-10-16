---
title: User Interface Mixin
---

## User Interface Mixin

The *User Interface* mixin class provides a set of methods to implement custom functionality for the InvenTree web interface.

### Enable User Interface Mixin

To enable user interface plugins, the global setting `ENABLE_PLUGINS_INTERFACE` must be enabled, in the [plugin settings](../../settings/global.md#plugin-settings).

## Plugin Context

When rendering certain content in the user interface, the rendering functions are passed a `context` object which contains information about the current page being rendered. The type of the `context` object is defined in the `PluginContext` file:

{{ includefile("src/frontend/src/components/plugins/PluginContext.tsx", title="Plugin Context", fmt="javascript") }}

## Custom Panels

Many of the pages in the InvenTree web interface are built using a series of "panels" which are displayed on the page. Custom panels can be added to these pages, by implementing the `get_ui_panels` method:

::: plugin.base.ui.mixins.UserInterfaceMixin.get_ui_panels
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      show_sources: True
      summary: False
      members: []

The custom panels can display content which is generated either on the server side, or on the client side (see below).

### Server Side Rendering

The panel content can be generated on the server side, by returning a 'content' attribute in the response. This 'content' attribute is expected to be raw HTML, and is rendered directly into the page. This is particularly useful for displaying static content.

Server-side rendering is simple to implement, and can make use of the powerful Django templating system.

Refer to the [sample plugin](#sample-plugin) for an example of how to implement server side rendering for custom panels.

**Advantages:**

- Simple to implement
- Can use Django templates to render content
- Has access to the full InvenTree database, and content not available on the client side (via the API)

**Disadvantages:**

- Content is rendered on the server side, and cannot be updated without a page refresh
- Content is not interactive

### Client Side Rendering

The panel content can also be generated on the client side, by returning a 'source' attribute in the response. This 'source' attribute is expected to be a URL which points to a JavaScript file which will be loaded by the client.

Refer to the [sample plugin](#sample-plugin) for an example of how to implement client side rendering for custom panels.

#### Panel Render Function

The JavaScript file must implement a `renderPanel` function, which is called by the client when the panel is rendered. This function is passed two parameters:

- `target`: The HTML element which the panel content should be rendered into
- `context`: A dictionary of context data which can be used to render the panel content


**Example**

```javascript
export function renderPanel(target, context) {
    target.innerHTML = "<h1>Hello, world!</h1>";
}
```

#### Panel Visibility Function

The JavaScript file can also implement a `isPanelHidden` function, which is called by the client to determine if the panel is displayed. This function is passed a single parameter, *context* - which is the same as the context data passed to the `renderPanel` function.

The `isPanelHidden` function should return a boolean value, which determines if the panel is displayed or not, based on the context data.

If the `isPanelHidden` function is not implemented, the panel will be displayed by default.

**Example**

```javascript
export function isPanelHidden(context) {
    // Only visible for active parts
    return context.model == 'part' && context.instance?.active;
}
```

## Custom UI Functions

User interface plugins can also provide additional user interface functions. These functions can be provided via the `get_ui_features` method:

::: plugin.base.ui.mixins.UserInterfaceMixin.get_ui_features
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      show_sources: True
      summary: False
      members: []

::: plugin.samples.integration.user_interface_sample.SampleUserInterfacePlugin.get_ui_features
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []


Currently the following functions can be extended:

### Template editors

The `template_editor` feature type can be used to provide custom template editors.

**Example:**

{{ includefile("src/backend/InvenTree/plugin/samples/static/plugin/sample_template.js", title="sample_template.js", fmt="javascript") }}

### Template previews

The `template_preview` feature type can be used to provide custom template previews. For an example see:

**Example:**

{{ includefile("src/backend/InvenTree/plugin/samples/static/plugin/sample_template.js", title="sample_template.js", fmt="javascript") }}

## Sample Plugin

A sample plugin which implements custom user interface functionality is provided in the InvenTree source code:

::: plugin.samples.integration.user_interface_sample.SampleUserInterfacePlugin
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []
