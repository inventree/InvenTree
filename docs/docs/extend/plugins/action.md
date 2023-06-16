---
title: Action Plugins
---

## ActionMixin

Arbitrary "actions" can be called by POSTing data to the `/api/action/` endpoint. The POST request must include the name of the action to be performed, and a matching ActionPlugin plugin must be loaded by the server. Arbitrary data can also be provided to the action plugin via the POST data:

```
POST {
    action: "MyCustomAction",
    data: {
        foo: "bar",
    }
}
```

For an example of a very simple action plugin, refer to `/InvenTree/plugin/samples/integratoni/simpleactionplugin.py`
