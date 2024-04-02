---
title: URLs Mixin
---

## UrlsMixin

Use the class constant `URLS` for a array of URLs that should be added to InvenTrees URL paths or override the `plugin.setup_urls` function.

The array has to contain valid URL patterns as defined in the [django documentation]({% include "django.html" %}/topics/http/urls/).

``` python
class MyUrlsPlugin(UrlsMixin, InvenTreePlugin):

    NAME = "UrlsMixin"

    URLS = [
        re_path(r'increase/(?P<location>\d+)/(?P<pk>\d+)/', self.view_increase, name='increase-level'),
    ]
```


The URLs get exposed under `/plugin/{plugin.slug}/*` and get exposed to the template engine with the prefix `plugin:{plugin.slug}:` (for usage with the [url tag]({% include "django.html" %}/ref/templates/builtins/#url)).

!!! info "Note"
    In this example, when an HTTP request is made to `/plugin/{plugin.slug}/increase/.../...` the function `self.view_increase` is called and returns the view to be displayed (step 4 in the Django documentation)

### Views
If your plugin will implement and host another webpage, familiarize yourself with Django views. Implementation is exactly the same.
A good place to start is the [django documentation]({% include "django.html" %}/topics/http/views/). Additional InvenTree-specific information is below.

### Rendering Views
Rendering templated views is also supported. Templated HTML files should be placed inside your plugin folder in a sub folder called `templates`.
Placed here, the template can be called using the file name and the render command.

Example in context (inside the main plugin python file):
``` py
def view_test(self, request):
    return render(request, 'test.html', context)

def setup_urls(self):
    return [
        path('test/', self.view_test, name='test')
    ]
```

### Implementing the Page Base
Some plugins require a page with a navbar, sidebar, and content similar to other InvenTree pages.
This can be done within a templated HTML file by extending the file "page_base.html". To do this, place the following line at the top of your template file.
``` HTML
{% raw %}
{% extends "page_base.html" %}
{% endraw %}
```

Additionally, add the following imports after the extended line.
``` HTML
{% raw %}
{% load static %}
{% load inventree_extras %}
{% load plugin_extras %}
{% load i18n %}
{% endraw %}
```

#### Blocks
The page_base file is split into multiple sections called blocks. This allows you to implement sections of the webpage while getting many items like navbars, sidebars, and general layout provided for you.

The current default page base can be found [here](https://github.com/inventree/InvenTree/blob/master/InvenTree/templates/page_base.html). Look through this file to determine overridable blocks. The [stock app](https://github.com/inventree/InvenTree/tree/master/InvenTree/stock) offers a great example of implementing these blocks.

!!! warning "Sidebar Block"
    You may notice that implementing the `sidebar` block doesn't initially work. Be sure to enable the sidebar using JavaScript. This can be achieved by appending the following code, replacing `label` with a label of your choosing,  to the end of your template file.
    ``` HTML
    {% raw %}
    {% block js_ready %}
    {{ block.super }}
        enableSidebar('label');
    {% endblock js_ready %}
    {% endraw %}
    ```

#### Panels
InvenTree uses bootstrap panels to display the page's content. These panels are locate inside the block `page_content`.

Example:
```html
{% raw %}
<div class='panel panel-hidden' id='panel-loans'>
    <div class='panel-heading'>
        <div class='d-flex flex-wrap'>
            <h4>{% trans "Loaning Information" %}</h4>
        </div>
    </div>
    <div class='panel-content'>
        ...
    </div>
</div>
{% endraw %}
```
Notice that this example has the panel initially hidden.
This is where the `enableSidebar('...');'` function comes back into play. Panels are enabled according to the labels of items in the sidebar. Each sidebar item must declare a label corresponding to a panel. An example of a sidebar item within with the label `loans` is below.

```html
{% raw %}
{% trans "Loaning" as text %}
{% include "sidebar_item.html" with label='loans' text=text icon="fa-sitemap" %}
{% endraw %}
```
Note: This code is assumed to be placed within the `sidebar` block.

The `enableSidebar('...');'` function will un-hide the panel with the label `panel-...` (for this example, `panel-loans`) and hide all other panels. This allows you to have multiple panels on a page, but only show the panel corresponding to the current selected sidebar item.
Whenever you click a sidebar item, it will automatically enable the panel with the corresponding label and hide all other panels.

Additionally, when a panel is loaded, the function `onPanelLoad(...)` will be called for the associated panel.
If you would like to add javascript functionality to a panel after it loads, add the function within the `{% raw %}{% block js_ready %}{% endraw %}` block of your template file.

Example:
```js
onPanelLoad('loans', function() {
    ...
});;
```
