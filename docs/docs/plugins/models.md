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

A typical Django model class is based on `django.db.models.Model`, which provides the core functionality for defining database models in Django. Alternatively, `InvenTree.models.InvenTreeModel` comes with a few additional core integrations (content type association, [plugin validation](./mixins/validation.md)) or `InvenTree.models.InvenTreeMetadataModel` which also includes [model metadata](./metadata.md) support for the model instances.

## Generic Model Mixins

### MetadataMixin

Adds support for [model metadata](./metadata.md) support, allowing additional information to be attached to model instances. This metadata can be accessed and manipulated through the InvenTree API or by other plugins.

### InvenTreeParameterMixin

Adds support for [parameters](../concepts/parameters.md), allowing your models to use the parameter mechanism including proper permission checks and integration with the InvenTree API.
