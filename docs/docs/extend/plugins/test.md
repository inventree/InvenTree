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
that comes from a supplier API to a float value. The price might have the form "1.456,34 €".
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

The function assertEqual flags an error in case the two arguments are not equal. In equal case
no error is flagged and the test passes. The test function tests five different
input variations. More might be added based on the requirements.

### Involve the database
Now we test a function that uses InvenTree database objects. The function checks if a part
should be updated with latest data from a supplier. Parts that are not purchasable or inactive
should not be updated. The function in the plugin has the following form:

```
class MySupplier():

    def should_be_updated(self, my_part):

        ...
        return True/False
```

To test this function, parts are needed in the database. The test framework creates
a dummy database for each run which is empty. Parts for testing need to be added.
This is done in the test function which looks like:

```
from part.models import Part, PartCategory


def test_should_be_updated(self):
        test_cat = PartCategory.objects.create(name='test_cat')
        active_part = Part.objects.create(
            name='Part1',
            IPN='IPN1',
            category=test_cat,
            active=True,
            purchaseable=True,
            component=True,
            virtual=False)
        inactive_part = Part.objects.create(
            name='Part2',
            IPN='IPN2',
            category=test_cat,
            active=False,
            purchaseable=True,
            component=True,
            virtual=False)
        non_purchasable_part = Part.objects.create(
            name='Part3',
            IPN='IPN3',
            category=test_cat,
            active=True,
            purchaseable=False,
            component=True,
            virtual=False)

        self.assertEqual(MySupplier.should_be_updated(self, active_part, True, 'Active part')
        self.assertEqual(MySupplier.should_be_updated(self, inactive_part, False, 'Inactive part')
        self.assertEqual(MySupplier.should_be_updated(self, non_purchasable_part, False, 'Non purchasable part')
```

A category and three parts are created. One part is active, one is inactive and one is not
purchasable. The function should_be_updated is tested with all
three parts. The first test should return True, the others False. A message was added to the assert
function for better clarity of test results.

The dummy database is completely separate from the one that you might use for development
and it is deleted after the test. There is no danger for your development database.

In case everything is OK, the result looks like:

```
----------------------------------------------------------------------
Ran 1 tests in 0.809s

OK
Destroying test database for alias 'default'...
```

In case of a problem you will see something like:

```
======================================================================
FAIL: test_should_be_updated (inventree_supplier_sync.test_supplier_sync.TestSyncPlugin)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/michael/.local/lib/python3.10/site-packages/inventree_supplier_sync/test_supplier_sync.py", line 73, in test_should_be_updated
    self.assertEqual(SupplierSyncPlugin.should_be_updated(self, non_purchasable_part,), False, 'Non purchasable part')
AssertionError: True != False : Non purchasable part

----------------------------------------------------------------------
Ran 3 tests in 0.679s

FAILED (failures=1)
Destroying test database for alias 'default'...

```

In the AssertionError the message appears that was added to the assertEqual function.
