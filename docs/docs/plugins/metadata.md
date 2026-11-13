---
title: Model Metadata
---

## Model Metadata

Plugins can access internal database models, such as [Parts](../part/index.md), and their associated data. A plugin may need to store additional information for a specific model instance.

One option is to define a [database model](./models.md) using the [app plugin mixin](./mixins/app.md). This requires some knowledge of Django models and database design.

For information that can be represented as JSON, *Model Metadata* provides a way to store data on supported model instances without defining a separate model or handling lifecycle considerations.

This page describes how to use the model metadata mechanism.

### MetadataMixin Class

*Most* of the models in the InvenTree database inherit from the `MetadataMixin` class, which adds the `metadata` field to each inheriting model. The `metadata` field is a [JSONField]({% include "django.html" %}/ref/models/fields/#django.db.models.JSONField) which allows for storing arbitrary JSON data against the model instance.

This field is provided to allow any plugins to store and retrieve arbitrary data against any item in the database.

!!! tip "External Use Only"
    It is important to note that the `metadata` field of each model instance is not used for any internal functionality. Any data stored against this field is only for use by external plugins.

## Accessing Metadata

### Plugin Access

The `metadata` field can be accessed and updated directly from custom plugin code, as follows:

```python
from part.models import Part

# Show metadata value against a particular Part instance
part = Part.objects.get(pk=100)
print(part.metadata)

> {'foo': 'bar'}

part.metadata['hello'] = 'world'
print(part.metadata)

> {'foo': 'bar', 'hello': 'world'}
```

### API Access

For models which provide this metadata field, access is also provided via the API. Use the generic `/metadata/<modelname>/<object id>/` endpoint to retrieve or update metadata information.

#### PUT vs PATCH

An important note with regard to metadata access via the API is the behaviour of a `PUT` request vs a `PATCH` request. As demonstrated in the comparison below, a `PUT` request will *overwrite* existing data, while a `PATCH` request will *merge* with existing data.

**Initial Data:**

```json
{"foo": "bar", "hello": "world"}
```

**Payload:**

```json
{"xyz": "XYZ"}
```

**Result of PUT request:**

```json
{"xyz: XYZ"}
```

**Result of PATCH request:**

```json
{"foo": "bar", "hello": "world", "xyz": "XYZ"}
```

!!! danger "Take Care"
    Take care when updating metadata via the API, especially when using a PUT request.

### Python API Access

The [Python API library](../api/python/index.md) provides similar support for accessing model metadata. Use the `setMetadata` method to retrieve metadata information from the server:

```python
from inventree.api import InvenTreeAPI
from inventree.part import Part

api = InvenTreeAPI("http://localhost:8000", username="admin", password="inventree")

part = Part(api, pk=100)

print(part.getMetadata())

> {'foo': 'bar', 'hello': 'world'}
```

Metadata can be added directly here using the `setMetadata` method:

```python
part.setMetadata("abc", "xyz")

print(part.getMetadata())

> {'abc': 'xyz', 'foo': 'bar', 'hello': 'world'}
```

!!! tip "Merge vs Overwrite"
    By default setting a metadata `key:value` pair will *merge* data in with existing data, by using a [PATCH request](#put-vs-patch).

To *overwrite* existing metadata, use the `overwrite=True` flag:

```python
part.setMetadata({"aaa": "ABC"}, overwrite=True)

print(part.getMetadata())
> {'aaa': 'ABC'}
```

## Considerations

### Data Keys

There is no guarantee that the data added to a particular model will *not* be overwritten by a different plugin. Your plugin should at least ensure that the data keys used are unique to the plugin, to ensure that they do not conflict with other plugins

### Structured Data

If you need to store data which is more "structured" than JSON objects, consider using the (more involved) [app mixin](./mixins/app.md) to develop custom database tables for your data.
