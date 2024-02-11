---
title: Bulk Deletion
---

## Bulk Deletion

While deleting items individually via the API is supported, it can prove inefficient (time consuming) when multiple items are to be deleted sequentially.

For example, if the user wishes to delete a large number items (such as lines from a [Bill of Materials](../build/bom.md)), these items are deleted sequentially, with each `DELETE` separate request requiring network transfer, database access, cleanup, etc.

A much more efficient approach is to allow for "bulk deletion" of multiple database items in a single transaction. This means that only one network request is required, and only a single database access request.

So, InvenTree supports a custom "bulk deletion" endpoint which is available for some database models.

## Item Filtering

In a "regular" `DELETE` action, the pk (primary key) of the target object is provided, to designate which object is going to be removed from the database:

`DELETE /api/part/10/`

However this approach does not work if we wish to delete multiple items. To determine which items are to be deleted, additional data can be added to the query (as you would do with a normal `POST` request, for example).

### Primary Key Values

The request can specify a list of individual pk (primary key) values to delete, using the `items` variable:

```json
{
    "items": [1, 10, 50, 99]
}
```

### Filters

The request can also specify a list of filters to be applied to the database query. Any items which match the filters will be deleted. Here, use the `filters` variable:

```
{
    "filters": {
        "active": False,
        "category": 7.
    }
}
```
