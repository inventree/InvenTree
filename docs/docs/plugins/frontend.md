---
title: UI Plugin Integration
---

## Frontend Integration

Plugins can inherit from the [UserInterfaceMixin](./mixins/ui.md) class to provide custom UI components that can be integrated into the InvenTree web interface.

### Plugin Creator

Note that the [InvenTree plugin creator](./creator.md) can be used to scaffold a new plugin with the necessary structure for frontend integration. This will automatically set up the necessary files and configurations to get started with frontend development.

## Frontend Architecture

When designing a frontend plugin component, it is important to have at least a basic understanding of the InvenTree frontend architecture.

### React

The frontend code is written in TypeScript, and uses React for rendering components.

### Mantine

InvenTree uses the [Mantine](https://mantine.dev/) component library for building user interfaces. Mantine provides a set of pre-built components that can be used to create responsive and accessible web applications.

### Axios

InvenTree uses [Axios](https://axios-http.com/) for making API requests to the InvenTree server.

### Lingui

InvenTree uses [Lingui](https://lingui.js.org/) for internationalization (i18n) of the user interface. Lingui provides a set of tools for managing translations and rendering localized text in the frontend.

## Calling Functions

A custom UI component is rendered by specifying a source file and method name. The filename and method name are provided to the frontend via a specification in the backend (Python) code, and fetched at runtime via an API call.

The 'static' files for each plugin are copied to the static directory when the plugin is activated. The frontend code needs to know the path to the static files for the plugin in order to load them correctly.

To assist in this, the `UserInterfaceMixin` class provides a `plugin_static_file` method. This method returns the path to the static file for the plugin, which can be used in the frontend code to load the necessary resources.

For example, when returning a list of available UI components in a given context, the "source" attribute can be specified as follows:

```python
{
    ...,
    "source": self.plugin_static_file('my_plugin.js:my_plugin_function'),
    ...,
}
```

*Note: The function name can be appended to the filename using a colon (:) separator.*

### Function Signature

The expected function signature for the frontend function is:

```javascript
function my_plugin_function(context: InvenTreePluginContext) {
    // Function implementation
}
```

The function is expected to return a React component that will be rendered in the InvenTree web interface.

### Plugin Context

When rendering certain content in the user interface, the rendering functions are passed a `context` object which contains information about the current page being rendered. The type of the `context` object is defined in the `PluginContext` file:

{{ includefile("src/frontend/src/components/plugins/PluginContext.tsx", title="Plugin Context", fmt="javascript") }}

The following properties are available in the `context` object:

| Property | Description |
| -------- | ----------- |
| `version` | An object containing the current InvenTree version information. |
| `user` | An object containing information about the currently logged-in user. |
| `host` | An object containing information about the current host (server) configuration. |
| `i18n` | An object containing internationalization (i18n) functions for translating text. |
| `locale` | The current locale being used for the user interface. |
| `api` | The Axios instance configured to communicate with the InvenTree API. |
| `queryClient` | The query client instance used for managing API calls in the frontend. |
| `navigate` | A function to navigate to a different page in the InvenTree web interface. |
| `globalSettings` | An object containing global settings for the InvenTree instance. |
| `userSettings` | An object containing user-specific settings. |
| `modelInformation` | An object containing information about the models available in the InvenTree instance. |
| `renderInstance` | A function to render a model instance |
| `theme` | The current Mantine theme being used in the InvenTree web interface. |
| `colorScheme` | The current color scheme being used in the InvenTree web interface. |
| `forms` | A set of functional components for rendering forms in the InvenTree web interface. |

This set of components is passed through at render time to the plugin function, allowing the plugin code to hook directly into the InvenTree web interface and access the necessary context for rendering.

For example, the plugin can make use of the authenticated api instance, to make calls to the InvenTree API, or use the `navigate` function to redirect the user to a different page.

## Externalized Libraries

To create a plugin which integrates natively into the InvenTree UI, it is important that the plugin is compiled in a way that allows it to run within the same React context as the InvenTree frontend code.

To achieve this, the InvenTree UI provides a number of core libraries as "externalized" libraries. This means that these libraries are not bundled with the plugin code, but are instead provided by the InvenTree frontend code at runtime.

The following libraries are externalized and provided by the InvenTree frontend:

- `react`
- `react-dom`
- `react-dom/client`
- `@mantine/core`
- `@lingui/core`
- `@lingui/react`

### Window Object

The externalized libraries are made available in the global `window` object, allowing the plugin code to access them directly without needing to import them.

This means in practice that the plugin code must be compiled in such a way that it does not include these libraries in its own bundle. Instead, it should reference them from the global `window` object.

### Vite Setup

The vite configuration for your InvenTree plugin must be confitured to correctly externalize these libraries, both in development and production builds.

This is *somewhat tricky* to get right, which is why we recommend using the [InvenTree plugin creator](./creator.md) to scaffold a new plugin. The plugin creator will automatically configure the necessary build settings to ensure that the plugin code is compatible with the InvenTree frontend architecture.

## NPM Package

When creating a UI plugin, the developer needs access to the type definitions for the [context](#plugin-context) object, as well as information on which libraries are externalized.

To support this, the InvenTree project provides a dedicated NPM package for developem
plugins: [@inventreedb/ui](https://www.npmjs.com/package/@inventreedb/ui)

### Type Definitions

The type definitions for the `context` object are provided in the `@inventreedb/ui` package. This allows the plugin code to import the necessary types and use them in the plugin function signature:

```typescript
import { InvenTreePluginContext } from '@inventreedb/ui';

function my_plugin_function(context: InvenTreePluginContext) {
    // Function implementation
}
```

### Custom Functions

The `@inventreedb/ui` package also provides a set of custom functions that can be used in the plugin code. These functions allow the plugin code to make use of some of the core InvenTree functionality, rather than having to re-implement it.

### Custom Components

Additionally, the `@inventreedb/ui` package provides a set of custom components that can be used in the plugin code. This allows the plugin to construct UI components with a consistent look and feel, and to make use of the InvenTree design system.

## Frontend Development

When developing a frontend plugin, it is useful to be able to run the plugin code in a development environment, where changes can be made and tested quickly. This allows for rapid iteration and debugging of the plugin code, instead of having to rebuild and redeploy the plugin code for every change.

To assist with this, InvenTree can be configured to allow for loading a particular plugin in "development" mode. In this mode, loading of the frontend code is redirected from the "static" directory, to a local development server.

!!! into "Plugin Creator"
    Refer to the [plugin creator docs](./creator.md#frontend-development-server) for more information on how to set up a development server for your plugin.

### Debug Mode

This facility is only available when running the backend server in [debug mode](../start/config.md#debug-mode). With debug omde enabled, a single plugin can be selected for "development" mode, allowing the frontend code to be loaded from a local development server.

### Config File

To select a plugin for development, edit the server [configuration file](../start/config.md#configuration-file), add the following entry:

```yaml
plugin_dev:
  slug: 'my-custom-plugin'  # Replace with the slug of your plugin
  host: "http://localhost:5174"  # Replace with the path to your dev server
```

### Development Server

Assuming you have set up your plugin with the [plugin creator](./creator.md), you can start the development server using the following command:

```bash
cd frontend
npm run dev
```

This will automatically launch the plugin development server on port `:5174`, and the InvenTree backend is configured to redirect static file requests for this plugin, to the development server.

## Distributing Frontend Code

InvenTree plugins are distributed as Python packages, which means that the frontend code must be bundled and included in the package.

The typical approach (as used by the plugin creator) is to build the frontend code (using [Vite](https://vitejs.dev/)) and then copy the built files into the `static` directory of the plugin.

After the static files are built into the correct location, the plugin can be packaged and distributed as a Python package, which can then be installed using PIP.

[Python packaging](https://packaging.python.org/en/latest/) is a complex topic, and there are many resources available to help with this process. The InvenTree plugin creator provides a basic setup for packaging the plugin, but it is recommended to read up on Python packaging if you are new to this topic.
