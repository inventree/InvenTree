---
title: Item Tags
---

## Tags

Several models in InvenTree can be tagged with arbitrary tags. Tags are useful for grouping items together. This can be used to mark items with a plugin or to group items together for a particular theme. Tags are meant to be used by programs and are not visible to the end user.
Tags are shared between all models that can be tagged.

The following models can be tagged:
- [Parts](../../part/part.md) and [Supplier Parts](../../order/company#supplier-parts)/[Manufacturer Part](../../order/company#manufacturer-parts)
- [Stock Items](../../stock/stock.md#stock-item) / [Stock Location](../../stock/stock.md#stock-location)


## Accessing Tags

### Plugin Access

The `tags` field can be accessed and updated directly from custom plugin code, as follows:

```python
from part.models import Part

# Show tags for a particular Part instance
part = Part.objects.get(pk=100)
print(part.tags)

> {['Tag1', 'Another Tag']}

# Tags can also be accessed via tags.all()
print(part.tags.all())

> {['Tag1', 'Another Tag']}

# Add tag
part.tags.add('Tag 2')
print(part.tags)

> {['Tag1', 'Tag 2', 'Another Tag']}

# Remove tag
part.tags.remove('Tag1')
print(part.tags)

> {['Tag 2', 'Another Tag']}

# Filter by tags
Part.objects.filter(tags__name__in=["Tag1", "Tag 2"]).distinct()
```

### API Access

For models which provide tags, access is also provided via the API. The tags are exposed via the detail endpoint for the models starting from version 111.

Tags can be cached via PATCH or POST requests. The tags are provided as a json formatted list of strings. The tags are note case sensitive and must be unique across the instance - else the existing tag gets assigned. The tags are not sorted and the order is not guaranteed.

```json
{
    "tags": '["foo", "bar"]'
}
```
