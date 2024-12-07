---
Title: Unit Tests
---

## Unit Tests
For complicated plugins it makes sense to add unit tests the code to ensure
that plugins work correctly and are compatible with future versions too.
You can run these tests as part of your ci against the current stable and
latest tag to get notified when something breaks before it gets released as
part of stable. InvenTree offers a framework for testing. Please refer
to [Unit Tests](../../develop/contributing.md) for more information.

### Prerequisites
For plugin testing the following environment variables must be set to True:

| Name | Function | Value |
| --- | --- | --- |
| INVENTREE_PLUGINS_ENABLED | Enables the use of 3rd party plugins | True |
| INVENTREE_PLUGIN_TESTING | Enables enables all plugins no matter of their active state in the db or built-in flag | True |
| INVENTREE_PLUGIN_TESTING_SETUP | Enables the url mixin | True |

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

### do some work here... A simple Example
A simple example is shown here. Assume the plugin has a function that converts a price string
that comes from a supplier API  to a float value. The price might have the form "1.456,34 €". 
It can be different based on country and local settings.
The function in the plugin will convert it to a float 1456.34. It is in the class MySupplier
and has the following structure:

```
class MySupplier():

    def reformat_price(self, string_price):

        ...
        return float_price
```

This function needs to be tested. The test can look like this:

```
from .myplugin import MySupplier

def test_reformat_price(self):

    self.assertEqual(MySupplier.reformat_price(self, '1.456,34 €'), 1456.34)
    self.assertEqual(MySupplier.reformat_price(self, '1,45645 €'), 1.45645)
    self.assertEqual(MySupplier.reformat_price(self, '1,56 $'), 1.56)
    self.assertEqual(MySupplier.reformat_price(self, ''), 0)
    self.assertEqual(MySupplier.reformat_price(self, 'Mumpitz'), 0)
```

assertEqual flags an error in case the two arguments are not equal. In equal case
no error is flagged and the test passes. The test function tests five different
input variations. More might be added base on the requirements.
