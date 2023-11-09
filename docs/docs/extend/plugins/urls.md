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

!!! info "Note"
    In this example, when an HTTP request is made to `/plugin/{plugin.slug}/increase/.../...` the function `self.view_increase` is called and returns the view to be displayed (step 4 in the Django documentation)

### Views
If your plugin will implement and host another webpage, familiarize yourself with Django views. Implementation is exactly the same.
A good place to start is the [django documentation](https://docs.djangoproject.com/en/4.2/topics/http/views/).

### Rendering Views
Rendering templated views is also supported. Templated HTML files should be placed inside a 'templates' subfolder in your plugin folder.
Placed here, the template can be called using the file name (ex: `render(request, 'test.html', context)`)

### Implementing a Page Base
Some plugins require a page with a navbar, sidebar, and content.
This can be done within a templated HTML file. Extend the file "page_base.html". This can be done by placing the following line at the top of the file.
``` HTML
{% extends "page_base.html" %}
```

Additionally, you should add the following imports after the extended line.
``` HTML
{% load static %}
{% load inventree_extras %}
{% load plugin_extras %}
{% load i18n %}
```

#### Blocks
The page_base file is split into multiple sections called blocks. This allows you to implement sections of the webpage while getting many items like navbars, sidebars, and general layout provided for you.

The current page base can be found [here](https://github.com/inventree/InvenTree/blob/master/InvenTree/templates/page_base.html). This will provide you with what blocks you can override. The [stock app](https://github.com/inventree/InvenTree/tree/master/InvenTree/stock) offers a great example of implementing these blocks.

!!! warning "Sidebar Block"
    You may notice that implementing the `sidebar` block does not work. The most likely issue is that you are not enabling the sidebar using JavaScript. To fix this, append the following code to the end of your template file.
``` HTML
{% block js_ready %}
{{ block.super }}
    enableSidebar('stocklocation');


{% endblock js_ready %}
```
