## inventree-ui

User Interface (UI) elements for the [InvenTree](https://inventree.org) web interface.


### Description

This package provides a public interface allowing plugins to hook into core UI functionality. In particular, it defines a set of interface types provided by the InvenTree user interface, to be used by a custom plugin to implement some custom UI feature.

This library is intended to be used for creating plugins - any other use is outside of its scope and is not supported.

### Plugin Creator

This library is intended to be used with the [InvenTree Plugin Creator](https://github.com/inventree/plugin-creator). Read the documentation for the plugin creation tool for more information.

The plugin creation tool uses the types provided in this package at build time, but it is intended that most of the major packages are *externalized* - as these are provided as global objects by the core InvenTree UI code.

### Installation

This should be installed as a part of the plugin creator tool. If you need to install it manually, e.g. using `npm`:

```
npm i @inventreedb/ui
```

### Versioning

Each change to the plugin API will be described in the [CHANGELOG file](./CHANGELOG.md).
