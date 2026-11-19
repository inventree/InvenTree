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

### API Views and Permissions

If your plugin provides API endpoints (e.g. using [Django REST Framework](https://www.django-rest-framework.org/) views), you are responsible for ensuring that these endpoints enforce the correct [user permissions](../../settings/permissions.md).

Unless a view overrides the `permission_classes` attribute, the default InvenTree permission classes are applied. These check the user's role permissions (and the [OAuth2 scopes](../../api/index.md#scopes) of the token, if applicable) against the *model* associated with the view:

- If the view's serializer defines a `Meta.model` attribute, permissions are checked against that model
- Otherwise, for write operations (`POST`, `PUT`, `PATCH`, `DELETE`), permissions are checked against the model of the view's `queryset`
- If no model can be determined, write operations are denied (for all users except superusers)

For views which use a serializer without a model (e.g. "action" endpoints), or which modify data associated with a different role, specify the required role explicitly using the `role_required` attribute. This can either be a role name (e.g. `'stock'`, in which case the permission is determined by the HTTP method), or a `role.permission` pair (e.g. `'stock.change'`):

```python
from rest_framework import serializers
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from stock.models import StockItem


class AdjustSerializer(serializers.Serializer):
    """Serializer without a model."""

    item = serializers.PrimaryKeyRelatedField(queryset=StockItem.objects.all())


class AdjustStockView(CreateAPIView):
    """Custom action which modifies stock items."""

    queryset = StockItem.objects.none()
    serializer_class = AdjustSerializer

    # Require the 'change' permission for the 'stock' role (for all HTTP methods)
    role_required = 'stock.change'

    def create(self, request, *args, **kwargs):
        ...
        return Response({'success': True})
```

!!! warning "Overriding permission classes"
    If you override the `permission_classes` attribute of a view, the default role permission checks are no longer applied, and you must implement any required permission checks yourself.

#### Additional Permission Checks

If your view reads or modifies data beyond the model associated with the view, check the user's permissions against that data as well. Use the `check_request_permission` and `check_request_role` functions, which take the API request (rather than the user) - so that the scopes of an OAuth2 token are also checked:

```python
from rest_framework.exceptions import PermissionDenied

from InvenTree.permissions import check_request_permission, check_request_role
from part.models import Part

...

def create(self, request, *args, **kwargs):
    # Check the 'change' permission against the Part model
    if not check_request_permission(request, Part, 'change'):
        raise PermissionDenied()

    # Check the 'delete' permission for the 'bom' role
    if not check_request_role(request, 'bom', 'delete'):
        raise PermissionDenied()
```

!!! info "OAuth2 Scopes"
    The `check_user_permission` and `check_user_role` functions (in `users.permissions`) only check the permissions of the user. When used within an API view, they ignore the scopes of an OAuth2 token, which may allow a token to perform actions beyond its scopes.

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
