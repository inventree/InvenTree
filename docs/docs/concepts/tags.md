---
title: Tags
---

## Tags

*Tags* are short, arbitrary labels that can be attached to InvenTree objects to group or classify them in flexible ways that don't require changes to the underlying data model. Unlike [parameters](./parameters.md), tags carry no typed value — they are simply names. A tag can be applied to objects of any supported model type, and tags are shared across the entire InvenTree instance.

!!! note "Shared Tag Namespace"
    Tags are global: a tag named `prototype` applied to a Part and the same tag applied to a Build Order refer to the same underlying tag record. Renaming or deleting a tag affects every object to which it is attached.

### Supported Models

Tags can be attached to the following InvenTree objects:

- [Parts](../part/index.md)
- [Supplier Parts](../purchasing/supplier.md#supplier-parts)
- [Manufacturer Parts](../purchasing/manufacturer.md#manufacturer-parts)
- [Companies](./company.md)
- [Stock Items](../stock/index.md#stock-item)
- [Stock Locations](../stock/index.md#stock-location)
- [Build Orders](../manufacturing/build.md)
- [Purchase Orders](../purchasing/purchase_order.md)
- [Sales Orders](../sales/sales_order.md)
- [Return Orders](../sales/return_order.md)
- [Sales Order Shipments](../sales/sales_order.md#shipments)

## Managing Tags

### Adding and Removing Tags

Any object that supports tags will expose a *Tags* field in its detail and edit forms. Tags are entered as a comma-separated list of names and can be freely added or removed at any time. Tag names are case-insensitive — `Prototype`, `prototype`, and `PROTOTYPE` all refer to the same tag.

### Tag Names

Tag names must be unique within the InvenTree instance (case-insensitively). If you type a name that already exists under a different capitalisation, the existing tag is assigned rather than a new one created. Tag names may contain spaces, but leading and trailing whitespace is stripped automatically.

## Filtering by Tags

Tables that support tags can be filtered by one or more tag names. When multiple tags are specified, only objects that carry **all** of the specified tags are returned (AND logic).

For example, filtering a Parts table by the tags `approved` and `prototype` returns only parts tagged with both.

## API Access

### Tag Endpoints

The tag list is available at `/api/tag/`. Individual tags can be retrieved, updated, or deleted at `/api/tag/<id>/`.

The `model_type` query parameter narrows the tag list to tags currently applied to a specific model type:

```
GET /api/tag/?model_type=part
```

### Tags on Model Endpoints

For models that support tags, the `tags` field is returned in the detail endpoint response as a list of tag name strings:

```json
{
  "pk": 42,
  "name": "Widget",
  "tags": ["approved", "prototype"]
}
```

Tags can be updated via a `PATCH` or `POST` request by supplying a JSON-encoded list of tag name strings. The full list of tags replaces the previous set — omitting a tag removes it:

```json
{
  "tags": ["approved", "production"]
}
```

Tags can also be used as a filter parameter on list endpoints. Supply a comma-separated list of tag names to the `tags` query parameter:

```
GET /api/part/?tags=approved,prototype
```

This returns only parts tagged with **both** `approved` and `prototype`.
