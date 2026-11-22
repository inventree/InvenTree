---
title: Defining Models
---

[App Mixins](./mixins/app.md) allow the usage of most Django features - amongst the most important use cases is the ability to freely design custom database models for a plugin. While almost all Django model features are supported, it is beneficial to use the built-in abstractions and generic features provided by InvenTree as those are well supported by the platform and come with good API integration.

## The apps module

The `apps` module in a plugin defines the general configuration of the registered Django app and its models.

A typical `apps.py` file in a plugin might look like this:

```python
from django.apps import AppConfig

class MyPluginConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'my_plugin'  # this is important for Django to identify the app correctly, ensure this name does not change once users have installed the plugin
    label = 'my_plugin'
```

This configuration ensures that Django recognizes the plugin as a valid application and allows it to integrate seamlessly with the InvenTree server. Adding any code in the AppConfig should be carefully considered as it can introduce significant startup overhead.

## Base classes

A typical Django model class is based on `django.db.models.Model`, which provides the core functionality for defining database models in Django.


Alternatively, `generic.models.base`contains a few base classes that plugins can also use.

### InvenTreeModel

Add support for content type association and [plugin validation](./mixins/validation.md).

### InvenTreeMetadataModel

Adds everything in InvenTreeModel, and adds support for [model metadata](./metadata.md).

### InvenTreeTree

For Tree models using django-mptt for hierarchies, also include content type association.

## Generic Model Mixins

Most common mechanisms contained in InvenTree's own models are exposed in the `generic.models` module as a set of mixins that often also have detection for frontend components to provide functions automatically.

### InvenTreeAttachmentMixin

TODO


### InvenTreeAuditMixin

TODO

### InvenTreeBarcodeMixin

Adds fields and functions for linking a [barcode](../barcodes/index.md) against model instances including lookup, assignment, and validation of barcodes against the API.

### InvenTreeImageMixin

Adds a `image` field to the model and automatic thumbnail generation for the uploaded images. This image can also be referenced in [reports](../report/report.md).

You must define a constant `IMAGE_RENAME` on the model class pointing to the function in your model that handles renaming uploaded images.

### InvenTreeMetadataMixin

Adds support for [model metadata](./metadata.md) support, allowing additional information to be attached to model instances. This metadata can be accessed and manipulated through the InvenTree API or by other plugins.

### InvenTreeNoteMixin

Adds support for defining and managing [notes](../concepts/notes.md) against model instances.

### InvenTreeParameterMixin

Adds support for [parameters](../concepts/parameters.md), allowing your models to use the parameter mechanism including proper permission checks and integration with the InvenTree API.


### InvenTreePathStringMixin

TODO

### InvenTreePluginValidationMixin

TODO

### InvenTreeReferenceIndexingMixin

TODO

### InvenTreeTagsMixin

Adds the required mechanism for defining [tags](../concepts/tags.md) for model instances.
