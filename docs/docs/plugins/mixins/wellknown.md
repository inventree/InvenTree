---
title: WellKnownMixin
---

## WellKnownMixin

Can be used to define well-known endpoints that are exposed on the root of the instance. These are always redirects and generally are available without authentication. Well-Known endpoints are a common discovery mechanism for web services and were originally defined in [RFC 5785](https://www.rfc-editor.org/rfc/rfc5785). IANA runs [a registry](https://www.iana.org/assignments/well-known-uris) with commonly acknowledged endpoints but generally one can define their own (this is not recommended by the RFC and technically one needs to register a name to be considered well-known).

The Mixin does not validate the endpoint names and does not enforce acceptable schemes or authorisation as these details depend on the service being advertised. The RFC is very liberal about these details.

!!! warning "Warning"
    The index of well-known names and endpoints is always available without authentication. The advertised endpoints themselves are not required to be available without authentication but it is a common pattern. `InvenTree.permissions.auth_exempt` can be used as a decorator to achieve that. Exposing endpoints without authentication is a security risk and should be done with care and only for selected endpoints.

Collection of endpoints is done by implementing the `get_well_known_urls` collector method which returns a list of tuples of the form `(name, url)` where `name` is the well-known name and `url` is the URL to redirect to. The URL might be lazy but must be resolvable to a string - which will be treated as a url.

``` python
from django.urls import path, reverse_lazy

class MyWellKnownPlugin(WellKnownMixin, InvenTreePlugin):

    NAME = "WellKnownMixin"

    def get_well_known_urls(
        self, request = None
    ):
        """Return well-known entries."""
        return [('abc-method', reverse_lazy('url-pattern-name'))]
```


The defined well-known URLs get exposed under `/.well-known/` so above example would make available a redirect to the view name 'url-pattern-name' at `/.well-known/abc-method/` and list the method in the unauthenticated, public `/.well-known/` index.

# Security considerations

The request object is passed to the collector method when it is available (during some operations like initialisation that is not the case) so that the plugin could potentially decide to hide itself on the index from unauthenticated users or based on other request parameters. The urlpattern might still be registered, that needs to be considered when implementing the views authentication response.

Due to (D)DOS concerns it is recommended to keep the `collector` function as lightweight as possible and especially to avoid database trips or other expensive operations. Default rate limits do not apply to the index as this is outside of the API surface!

### Sample Plugin

The following real world example demonstrates how to use the `WellKnownMixin` class to provide well-known endpoints. This plugin is shipped as part of InvenTree and is mandatory. It shows how a single plugin can define and expose a well-known endpoint.

::: plugin.builtin.integration.core_wellknown.InvenTreeWellKnown
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []
