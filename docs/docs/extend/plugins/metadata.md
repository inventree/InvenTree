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
