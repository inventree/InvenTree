---
Title: Unit Tests
---

## Unit Tests
For complicated plugins it makes sense to add unit tests to your code. InvenTree
offers a framework for testing. Please refer to [Unit Tests](../../develop/contributing.md) 
for more information.  A file called test_pluginname.py should be added to the plugin
directory:

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
invoke dev.test -r plugin_directory.test_pluginname.TestMyPlugin
```

