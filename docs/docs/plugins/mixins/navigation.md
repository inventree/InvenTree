---
title: Navigation Mixin
---

## NavigationMixin

!!! warning "Legacy Mixin"
    The navigation links provided by this mixin are not displayed in the current user interface, and the `ENABLE_PLUGINS_NAVIGATION` setting has been removed. To add custom navigation items to the user interface, use the [UserInterfaceMixin](./ui.md) and implement the `get_ui_navigation_items` method.

Use the class constant `NAVIGATION` for a array of links that should be added to InvenTrees navigation header.
The array must contain at least one dict that at least define a name and a link for each element. The link must be formatted for a URL pattern name lookup - links to external sites are not possible directly. The optional icon must be a class reference to an icon.

``` python
class MyNavigationPlugin(NavigationMixin, InvenTreePlugin):

    NAME = "NavigationPlugin"

    NAVIGATION = [
        {'name': 'SampleIntegration', 'link': 'plugin:sample:hi', 'icon': 'ti ti-box'},
    ]

    NAVIGATION_TAB_NAME = "Sample Nav"
    NAVIGATION_TAB_ICON = 'ti ti-plus-circle'
```

The optional class constants `NAVIGATION_TAB_NAME` and `NAVIGATION_TAB_ICON` can be used to change the name and icon for the parent navigation node.
