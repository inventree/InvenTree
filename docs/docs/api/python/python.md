---
title: Python Interface
---

## Python Module

A [Python module](https://github.com/inventree/inventree-python) is provided for rapid development of third party scripts or applications using the REST API. The python module handles authentication and API transactions, providing an extremely clean interface for interacting with and manipulating database data.

### Features

- Automatic authentication management using token-based authentication
- Pythonic data access
- Native file uploads
- Powerful functions for accessing related model data

### Installation

The inventree python interface can be easily installed via the [PIP package manager](https://pypi.org/project/inventree/):

```
pip3 install inventree
```

!!! tip "Upgrading"
    To upgrade to the latest version, run `pip install --upgrade inventree`

Alternatively, it can downloaded and installed from source, from [GitHub](https://github.com/inventree/inventree-python).

### Authentication

Authentication against an InvenTree server is simple:

#### Basic Auth

Connect using your username/password as follows:

```python
from inventree.api import InvenTreeAPI

SERVER_ADDRESS = 'http://127.0.0.1:8000'
MY_USERNAME = 'not_my_real_username'
MY_PASSWORD = 'not_my_real_password'

api = InvenTreeAPI(SERVER_ADDRESS, username=MY_USERNAME, password=MY_PASSWORD)
```

#### Token Auth

Alternatively, if you already have an access token:

```python
api = InvenTreeAPI(SERVER_ADDRESS, token=MY_TOKEN)
```

#### Environment Variables

Authentication variables can also be set using environment variables:

- `INVENTREE_API_HOST`
- `INVENTREE_API_USERNAME`
- `INVENTREE_API_PASSWORD`
- `INVENTREE_API_TOKEN`

And simply connect as follows:

```python
api = InvenTreeAPI()
```

### Retrieving Data

Once a connection is established to the InvenTree server, querying individual items is simple.

#### Single Item

If the primary-key of an object is already known, retrieving it from the database is performed as follows:

```python
from inventree.part import PartCategory

category = PartCategory(api, 10)
```

#### Multiple Items

Database items can be queried by using the `list` method for the given class. Note that arbitrary filter parameters can be applied (as specified by the [InvenTree API](../api.md)) to filter the returned results.

```python
from inventree.part import Part
from inventree.stock import StockItem

parts = Part.list(api, category=10, assembly=True)
items = StockItem.list(api, location=4, part=24)
```

The `items` variable above provides a list of `StockItem` objects.

#### Filtering by parent

In tree based models the child items could be filtered by using the parent keyword:

```python
from inventree.part import PartCategory

child_categories = PartCategory.list(api, parent=10)
```

The top level items can can be queried by passing empty string as a parent filter:

```python
from inventree.part import PartCategory

parent_categories = PartCategory.list(api, parent='')
```

### Item Attributes

The available model attributes are determined by introspecting [API metadata](../metadata.md). To view the fields (attributes) available for a given database model type within the python interface, use the `fieldNames` and `fieldInfo` methods, as below:

```python
from inventree.api import InvenTreeAPI
from inventree.part import Part

api = InvenTreeAPI("http://localhost:8000", username="admin", password="inventree")

fields = Part.fieldNames(api)

for field in Part.fieldNames(api):
    print(field, '->', Part.fieldInfo(field, api))
```

```
active -> {'type': 'boolean', 'required': True, 'read_only': False, 'label': 'Active', 'help_text': 'Is this part active?', 'default': True, 'max_length': None}
allocated_to_build_orders -> {'type': 'float', 'required': True, 'read_only': True, 'label': 'Allocated to build orders'}
allocated_to_sales_orders -> {'type': 'float', 'required': True, 'read_only': True, 'label': 'Allocated to sales orders'}
assembly -> {'type': 'boolean', 'required': True, 'read_only': False, 'label': 'Assembly', 'help_text': 'Can this part be built from other parts?', 'default': False, 'max_length': None}
category -> {'type': 'related field', 'required': True, 'read_only': False, 'label': 'Category', 'model': 'partcategory', 'api_url': '/api/part/category/', 'filters': {}, 'help_text': 'Part category', 'max_length': None}
component -> {'type': 'boolean', 'required': True, 'read_only': False, 'label': 'Component', 'help_text': 'Can this part be used to build other parts?', 'default': True, 'max_length': None}
default_expiry -> {'type': 'integer', 'required': True, 'read_only': False, 'label': 'Default Expiry', 'help_text': 'Expiry time (in days) for stock items of this part', 'min_value': 0, 'max_value': 2147483647, 'default': 0, 'max_length': None}
...
variant_stock -> {'type': 'float', 'required': True, 'read_only': True, 'label': 'Variant stock'}
```


### Item Methods

Once an object has been retrieved from the database, its related objects can be returned with the provided helper methods:

```python
part = Part(api, 25)
stock_items = part.getStockItems()
```

Some classes also have helper functions for performing certain actions, such as uploading file attachments or test results:

```python
stock_item = StockItem(api, 1001)
stock_item.uploadTestResult("Firmware", True, value="0x12345678", attachment="device_firmware.bin")
```

#### Discovering Methods

You can determine the available methods by either [reading the source code](https://github.com/inventree/inventree-python) or using the `dir()` function in an interactive terminal.

### Further Reading

The [InvenTree Python Interface](https://github.com/inventree/inventree-python) is open source, and well documented. The best way to learn is to read through the source code and try for yourself!
