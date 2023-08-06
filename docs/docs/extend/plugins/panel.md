---
title: Panel Mixin
---

## PanelMixin

The `PanelMixin` enables plugins to render custom content to "panels" on individual pages in the web interface.

Most pages in the web interface support multiple panels, which are selected via the sidebar menu on the left side of the screen:

{% with id="panels", url="plugin/panels.png", description="Display panels" %}
{% include 'img.html' %}
{% endwith %}

Each plugin which implements this mixin can return zero or more custom panels for a particular page. The plugin can decide (at runtime) which panels it wishes to render. This determination can be made based on the page routing, the item being viewed, the particular user, or other considerations.

### Panel Content

Panel content can be rendered by returning HTML directly, or by rendering from a template file.


Each plugin can register templates simply by providing a 'templates' directory in its root path.

The convention is that each 'templates' directory contains a subdirectory with the same name as the plugin (e.g. `templates/myplugin/my_template.html`)


In this case, the template can then be loaded (from any plugin!) by loading `myplugin/my_template.html`.


### Javascript

Custom code can be provided which will run when the particular panel is first loaded (by selecting it from the side menu).

To add some javascript code, you can add a reference to a function that will be called when the panel is loaded with the 'javascript' key in the panel description:

```python
{
    'title': "Updates",
    'description': "Latest updates for this part",
    'javascript': 'alert("You just loaded this panel!")',
}
```

Or to add a template file that will be rendered as javascript code, from the plugin template folder, with the 'javascript_template' key in the panel description:

```python
{
    'title': "Updates",
    'description': "Latest updates for this part",
    'javascript_template': 'pluginTemplatePath/myJavascriptFile.js',
}
```

Note : see convention for template directory above.

## Example Implementation

Refer to the `CustomPanelSample` example class in the `./plugin/samples/integration/` directory, for a fully worked example of how custom UI panels can be implemented.

### An example with button and parameter

Let's have a look at another example. We like to have a new panel that contains a button.
Each time the button is clicked, a python function in our plugin shall be executed and
a parameter shall be transferred . The result will look like that:

{% with id="mouser", url="plugin/mouser.png", description="Panel example with button" %} {% include "img.html" %} {% endwith %}


First we need to write the plugin code, similar as in the example above.

```python
from django.conf.urls import url
from django.http import HttpResponse

from order.views import PurchaseOrderDetail
from plugin import InvenTreePlugin
from plugin.mixins import PanelMixin, SettingsMixin, UrlsMixin

class MouserCartPanel(PanelMixin, SettingsMixin, InvenTreePlugin, UrlsMixin):

    value=1

    NAME = "MouserCart"
    SLUG = "mousercart"
    TITLE = "Create Mouser Cart"
    DESCRIPTION = "An example plugin demonstrating a button calling a python function."
    VERSION = "0.1"

    def get_custom_panels(self, view, request):
        panels = []

        # This panel will *only* display on the PurchaseOrder view,
        if isinstance(view, PurchaseOrderDetail):
            panels.append({
                'title': 'Mouser Actions',
                'icon': 'fa-user',
                'content_template': 'mouser/mouser.html',
            })
        return panels

    def setup_urls(self):
        return [
            url(r'transfercart/(?P<pk>\d+)/', self.TransferCart, name='get-cart')
        ]

#----------------------------------------------------------------------------
    def TransferCart(self,request,pk):

        print('User,pk:',request.user,pk)
        self.value=self.value+1
        return HttpResponse(f'OK')
```

The code is simple and really stripped down to the minimum. In the plugin class we first define the plugin metadata.
Afterwards we define the custom panel. Here we use a html template to describe the content of the panel. We need to
add the path here because the template resides in the subdirectory templates/mouser.
Then we setup the url. This is important. The url connects the http request with the function to be executed.
May be it is worth to leave a few more words on this because the string looks a bit like white noise.
*transfercart* is the url which can be chosen freely. The ? is well known for parameters. In this case we
get just one parameter, the orders primary key.* \d+* is a regular expression that limits the parameters
to a digital number with n digits. Let's have a look on the names and how they belong together:

{% with id="plugin_dataflow", url="plugin/plugin_dataflow.png", description="Dataflow between Javescript and Python" %} {% include "img.html" %} {% endwith %}

Finally we define the function. This is a simple increment of a class value.

Now lets have a look at the template file mouser.html

```html
{% raw %}
{% load i18n %}

<script>
async function JGetCart(){
    response = await fetch( '{% url "plugin:mousercart:get-cart" order.pk %}');
    location.reload();
}
</script>

<button type='button' class='btn btn-info' onclick="JGetCart()" title='{% trans "Get Mouser shopping Cart" %}'>
<span class='fas fa-redo-alt'></span> {% trans "Get Cart" %}
</button>

<br>
{{ order.description }}
{{ plugin.value }}
{% endraw %}
```

We start with a bit of javascript. The function JGetCart just calls the url that has been defined in the python code above.
The url consists of a full path `plugin:plugin-name:url-name`. The plugin-name is the SLUG that was defined in the plugin code.
order.pk is the parameter that is passed to python. 

The button is defined  with `class="btn btn-info` This is an InvenTree predefined button. There a are lots of others available.
Here are some examples of available colors:

{% with id="buttons", url="plugin/buttons.png", description="Button examples" %} {% include "img.html" %} {% endwith %}

Please have a look at the css files for more options. The last line renders the value that was defined in the plugin.

!!! tip "Give it a try"
    Each time you press the button, the value will be increased.
