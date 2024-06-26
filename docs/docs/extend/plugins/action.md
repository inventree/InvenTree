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

### Sample Plugin

A sample action plugin is provided in the `InvenTree` source code, which can be used as a template for creating custom action plugins:

::: plugin.samples.integration.simpleactionplugin.SimpleActionPlugin
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []
