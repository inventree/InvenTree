---
title: URLs Mixin
---

## UrlsMixin

Use the class constant `URLS` for a array of URLs that should be added to InvenTrees URL paths or override the `plugin.setup_urls` function.

The array has to contain valid URL patterns as defined in the [django documentation](https://docs.djangoproject.com/en/stable/topics/http/urls/).

``` python
class MyUrlsPlugin(UrlsMixin, InvenTreePlugin):

    NAME = "UrlsMixin"

    URLS = [
        url(r'increase/(?P<location>\d+)/(?P<pk>\d+)/', self.view_increase, name='increase-level'),
    ]
```

The URLs get exposed under `/plugin/{plugin.slug}/*` and get exposed to the template engine with the prefix `plugin:{plugin.slug}:` (for usage with the [url tag](https://docs.djangoproject.com/en/stable/ref/templates/builtins/#url)).
