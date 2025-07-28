---
title: Plugin Creator
---

## Plugin Creator Tool

The plugin framework provided for InvenTree is powerful and flexible - which also means that it can be a bit complex to get started, especially for new developers.

To assist in creating a new plugin, we provide a [plugin creator command line tool](https://github.com/inventree/plugin-creator).

This tool allows developers to quickly scaffold a new InvenTree plugin, and provides a basic structure to build upon.

The plugin creator tool allows the developer to select which plugin features they wish to include, and generates a basic plugin structure with the selected features.

### Features

The plugin creator tool provides a number of features to help you get started with plugin development:

- **Metadata Input**: Easily input metadata for your plugin, including name, description, and author information.
- **License Selection**: Choose from a variety of licenses for your plugin, with "MIT" as the default.
- **Feature Selection**: Select which plugin features you want to include, such as mixins and frontend features.
- **Devops Integration**: Optionally set up Git version control, automatic code formatting, and other development tools.
- **Deploy Support**: Generate a basic structure for your plugin that can be easily deployed to an InvenTree instance, and published to PyPI.
- **Frontend Development**: Set up a development server for frontend features, including hot reloading and build tools.

### Requirements

This page provides an overview of how to install and use the plugin creator tool, as well as some tips for creating your own plugins. The documentation here uses the "default" options as provided by the plugin creator tool, but you can customize the options to suit your needs.

It is assumed that you have a working InvenTree instance, and you have a development environment setup using our [devcontainer guide](../develop/devcontainer.md).

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
ls -al
```

You should see a directory structure similar to the following:

| File | Description |
| ---- | ----------- |
| **.git** | The Git repository for your plugin (if you selected Git integration). |
| **.github** | GitHub configuration files (if you selected GitHub integration). |
| **.gitlab-ci.yml** | GitLab CI configuration file (if you selected GitLab integration). |
| **.gitignore** | Git ignore file, specifying which files should be ignored by Git. |
| **.pre-commit-config.yaml** | Configuration file for pre-commit hooks (if you selected pre-commit integration). |
| **.editorconfig** | Editor configuration file
| **LICENSE** | The license file for your plugin. |
| **MANIFEST.in** | A file that specifies which files should be included in the plugin package. |
| **README.md** | A README file for your plugin. |
| **biome.json** | Configuration file for the Biome code formatter. |
| **pyproject.toml** | The project configuration file for your plugin. |
| **setup.cfg** | Rules for Python code formatting and linting. |
| **setup.py** | The setup script for your plugin. |
| **frontend/** | A directory containing the frontend code for your plugin (if you selected frontend features). |
| **my_custom_plugin/** | The main plugin directory, containing the plugin code. *(Note: the name of this directory will match the name you provided during plugin creation)* |

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

## Activate Plugin

Now that the plugin has been installed, you can activate it in your InvenTree instance. If the InvenTree server is not already running, start it with:

```bash
invoke dev.server
```

Then, navigate to the [plugin management page](http://localhost:8000/web/settings/admin/plugin) in your InvenTree instance. You can activate the plugin by clicking the "Activate" button next to your plugin in the list.

{{ image("plugin/plugin-creator-activate.png", "Activate Plugin") }}

!!! success "Plugin Activated"
    Your plugin should now be active, and you can start developing it further!

## Frontend Development

In this example we have configured the plugin to include frontend features. In production, the frontend code will be built and served as static files. However, during development, it is often useful to run a development server which provides hot reloading and other features.

### Backend Configuration

To facilitate frontend plugin development, the InvenTree backend server needs to be configured to redirect requests for the plugin frontend to the development server. To achieve this, you need to add the following lines to your server configuration file (e.g. `./dev/config.yaml`, if you are using the default devcontainer setup):

```yaml
plugin_dev:
  slug: 'my-custom-plugin'  # Replace with your plugin slug
  host: "http://localhost:5174"
```

!!! warning "Restart Required"
    After making changes to the configuration file, you will need to restart the InvenTree server for the changes to take effect.

This configuration tells the InvenTree server to redirect static file requests (for this particular plugin) to the development server running on port `5174`. This is only available in development mode, and will not be used in production.

### Frontend Development Server

The plugin creator tool provides a development setup to allow you to run a frontend development server. To install the required libraries and start the development server, run the following commands:

```bash
cd frontend
npm install
npm run dev
```

You should see output indicating that the development server is running on port `5174`:

{{ image("plugin/plugin-creator-dev.png", "Frontend dev server") }}

Let's test this out! The default plugin code has provided a custom "panel" which is display on the "part detail" page. Navigate to a part detail page in your InvenTree instance, and you should see the following custom panel displayed:

{{ image("plugin/plugin-creator-panel.png", "Custom Panel") }}

!!! success "Frontend Running"
    Your frontend development server is now running, and you can start developing your plugin's frontend features!

## Plugin Editing

### Backend Code

The backend code for your plugin is located in the `my_custom_plugin` directory. You can edit the Python files in this directory to implement the backend functionality of your plugin.

Refer to the `./my_custom_plugin/core.py` file as a starting point. This is where the main plugin logic is implemented. If you selected other mixin types during the plugin creation process, you may find additional files in the `my_custom_plugin` directory that correspond to those mixins.

As you have installed the plugin in editable mode, any changes you make to the backend code will be immediately reflected in your InvenTree instance without needing to reinstall the plugin.

!!! info "Debug Server"
    Note that live reload of the backend code only works when the InvenTree server is running in debug mode. If you are running the server in production mode, you will need to restart the server to see changes.

### Frontend Code

The frontend code for your plugin is located in the `frontend/src` directory. You can edit the provided `.tsx` files to adjust the frontend functionality of your plugin.

Refer to the `./frontend/src/Panel.tsx` file as a starting point. This is where the custom panel for the part detail page is implemented. You can modify this file to change the content and behavior of the panel.

While the `npm dev` server is running, any changes you make to the frontend code will be automatically reloaded allowing for rapid development and testing of your plugin's frontend features. This avoids the need to rebuild the frontend code every time you make a change.

!!! info "Page Reload"
    Due to the way the InvenTree frontend is structured, you will need to manually refresh the page in your browser to see changes to the frontend code. The development server will automatically reload the frontend code, but the InvenTree server needs to be aware of the changes.

## Build Plugin

The documentation provided above relates to the development of a plugin. Once you have completed your plugin development, you should build the plugin for distribution.

!!! info "CI Build"
    If you have configured CI integration during the plugin creation process, the CI server will automatically build your plugin when you push changes to your repository. This is the recommended way to build and distribute your plugin.

### Compile Frontend Assets

The frontend assets for your plugin need to be compiled before the plugin can be distributed. The compiled assets (primarily `.js` files) need to be distributed with the plugin, so that they can be statically served by the InvenTree server. To achieve this, the compiled files need to be placed in the `./my_custom_plugin/static` directory. The frontend `build` step will automatically place the compiled files in this directory:

```bash
cd frontend
npm run build
```

{{ image("plugin/plugin-creator-npm-build.png", "Build Frontend") }}

### Build Plugin

Now that the frontend assets have been compiled, you can build the plugin for distribution. This will create a distributable Python package that can be installed in other InvenTree instances.

!!! info "Top Level Directory"
    Ensure you are in the top-level directory of your plugin (the directory containing `setup.py`) before running the build command.

```bash
python -m build
```

You should see output indicating that the Python package has been built successfully.

### Publish Plugin

The plugin package can now be published (e.g. to PyPI), allowing it to be remotely installed into other InvenTree installations.

Publishing to PyPI is outside the scope of this documentation, but you can refer to the [Python Packaging User Guide](https://packaging.python.org/tutorials/packaging-projects/) for more information on how to publish your plugin package.

!!! info "Automated PyPI Publishing"
    If you have configured CI integration during the plugin creation process, the CI server will automatically publish your plugin to PyPI when you create a new release. You just need to ensure that you have set up the necessary credentials in your CI environment.

## Further Reading

For a more complex walkthrough of developing a plugin, check out our [basic plugin walkthrough](../plugins/walkthrough.md).
