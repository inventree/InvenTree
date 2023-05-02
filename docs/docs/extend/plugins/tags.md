---
title: Item Tags
---

## Tags

Several models in InvenTree can be tagged with arbitrary tags. Tags are useful for grouping items together. This can be used to mark items with a plugin or to group items together for a particular theme. Tags are meant to be used by programms and are not visible to the end user.
Tags are shared between all models that can be tagged.

The following models can be tagged:
- [Parts](../../part/part.md) and [Supplier Parts](../../order/company#supplier-parts)/[Manufacturer Part](../../order/company#manufacturer-parts)
- [Stock Items](../../stock/stock.md#stock-item) / [Stock Location](../../stock/stock.md#stock-location)

### API Access

For models which provide tags, access is also provided via the API. The tags are exposed via the detail endpoint for the models starting from version 111.

Tags can be cached via PATCH or POST requests. The tags are provided as a json formatted list of strings. The tags are note case sensitive and must be unique across the instance - else the exsisting tag gets assigned. The tags are not sorted and the order is not guaranteed.

```json
{
    "tags": '["foo", "bar"]'
}
```
