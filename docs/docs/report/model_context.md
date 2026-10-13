---
title: Model Context
---

## Model Context Variables

Each [report context](./context_variables.md) exposes one or more underlying model instances to the template (e.g. `order`, `part`, `item`). In addition to the explicit context variables documented on that page, templates can access any field or property of these model instances directly.

This page documents, for each reportable model type, the available:

- **Fields**: Database fields defined on the model (including those inherited from mixins / abstract base classes)
- **Properties**: `@property` attributes which have been explicitly marked with the `@report_attribute` decorator, making them discoverable here

Not every attribute or method available on a model instance is listed here - only database fields, and properties explicitly marked for discovery. For a full list of attributes and methods, refer to the source code for the particular model type.

{{ reportable_model_context() }}

## Related Model Types

Some *related* model types are not themselves directly reportable, but are referenced by a field or `@report_attribute` property on a reportable model (e.g. `PartCategory` via `part.category`, `SupplierPart` via `part.default_supplier` or `stockitem.supplier_part`).

These are discovered automatically - there is no manually-maintained list of related models here. If a reportable model gains a new field or `@report_attribute` property pointing at another model, that model will automatically appear in this section.

{{ related_model_context() }}
