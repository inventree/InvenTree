---
Title: Unit Tests
---

## Unit Tests
For complicated plugins it makes sense to add unit tests to your code. InvenTree
offers a framework for testing. Please refer to [Unit Tests](../../develop/contributing.md)
for more information.

### Prerequisites
For plugin testing the following environment variables must be set to True:

| Name | Function | Value |
| --- | --- | --- | --- |
| INVENTREE_PLUGINS_ENABLED | Add external plugins to the registry | True |
| INVENTREE_PLUGIN_TESTING | Enable testing of plugins | True |
| INVENTREE_PLUGIN_TESTING_SETUP |  | True |

### Test program

A file called test_plugin_name.py should be added to the plugin directory. It can have the
following structure:

```
# Basic unit tests for the plugin
from InvenTree.unit_test import InvenTreeTestCase

class TestMyPlugin(InvenTreeTestCase):
    def test_my_function(self):
        do some work here...
```

The test can be executed using invoke:

```
invoke dev.test -r module.file.class
```

Plugins are usually installed outside of the InventTree directory, e.g. in .local/lib/...
I that case module must be omitted.

```
invoke dev.test -r plugin_directory.test_plugin_name.TestMyPlugin
```
