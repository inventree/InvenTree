---
title: WellKnownMixin
---

## WellKnownMixin



``` python
class MyWellKnownPlugin(WellKnownMixin, InvenTreePlugin):

    NAME = "WellKnownMixin"

    URLS = [
        re_path(r'increase/(?P<location>\d+)/(?P<pk>\d+)/', self.view_increase, name='increase-level'),
    ]
```


The URLs get exposed under `/plugin/{plugin.slug}/*` and get exposed to the template engine with the prefix `plugin:{plugin.slug}:` (for usage with the [url tag]({% include "django.html" %}/ref/templates/builtins/#url)).

### Sample Plugin

The following real world example demonstrates how to use the `WellKnownMixin` class to provide well-known endpoints. This plugin is shipped as part of InvenTree and is mandatory. It shows how a single plugin can define and expose a well-known endpoint.

::: plugin.builtin.integration.core_wellknown.InvenTreeWellKnown
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []
