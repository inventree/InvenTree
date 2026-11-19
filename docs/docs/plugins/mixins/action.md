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

!!! warning "Permissions"
    The `/api/action/` endpoint only requires that the user is authenticated (and the `g:write` scope, for OAuth2 tokens) - no further permission checks are performed before the action plugin is called. If your action reads or modifies data, the plugin must check the permissions of the provided `user` itself, for example using the `check_user_permission` function.

    Exceptions raised within an action plugin are logged, but are *not* returned to the client as an error response. Instead, skip the action and report the result via `get_result()` / `get_info()`:

    ```python
    from stock.models import StockItem
    from users.permissions import check_user_permission

    def has_permission(self, user) -> bool:
        return check_user_permission(user, StockItem, 'change')

    def perform_action(self, user=None, data=None):
        if not self.has_permission(user):
            return
        ...

    def get_result(self, user=None, data=None):
        return self.has_permission(user)

    def get_info(self, user=None, data=None):
        if not self.has_permission(user):
            return {'error': 'Permission denied'}
        ...
    ```

    As the action plugin receives the user (not the request), the scopes of an OAuth2 token cannot be checked within the plugin.

### Sample Plugin

A sample action plugin is provided in the `InvenTree` source code, which can be used as a template for creating custom action plugins:

::: plugin.samples.integration.simpleactionplugin.SimpleActionPlugin
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []
