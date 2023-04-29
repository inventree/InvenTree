---
title: Model Metadata
---

## Model Metadata

Plugins have access to internal database models (such at [Parts](../../part/part.md)), and any associated data associated with these models. It may be the case that a particular plugin needs to store some extra information about a particular model instance, to be able to perform custom functionality.

One way of achieving this would be to create an entirely new database model to keep track of this information, using the [app plugin mixin](./app.md). However, this is a very heavy-handed (and complicated) approach!

A much simpler and more accessible method of recording custom information against a given model instance is provided "out of the box" - using *Model Metadata*.

### MetadataMixin Class

*Most* of the models in the InvenTree database inherit from the `MetadataMixin` class, which adds the `metadata` field to each inheriting model. The `metadata` field is a [JSONField](https://docs.djangoproject.com/en/3.2/ref/models/fields/#django.db.models.JSONField) which allows for storing arbitrary JSON data against the model instance.

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

For models which provide this metadata field, access is also provided via the API. Append `/metadata/` to the detail endpoint for a particular model instance to access.

For example:

{% with id="metadata_api", url="plugin/model_metadata_api.png", description="Access model metadata via API", maxheight="400px" %}
{% include 'img.html' %}
{% endwith %}

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

The [Python API library](../../api/python/python.md) provides similar support for accessing model metadata. Use the `setMetadata` method to retrieve metadata information from the server:

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

If you need to store data which is more "structured" than JSON objects, consider using the (more complex) [app mixin](../plugins/app.md) to develop custom database tables for your data.
