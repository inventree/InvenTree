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

## Example Implementations

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
from plugin.mixins import PanelMixin, UrlsMixin

class MouserCartPanel(PanelMixin, InvenTreePlugin, UrlsMixin):

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

{% with id="plugin_dataflow", url="plugin/plugin_dataflow.png", description="Dataflow between Javascript and Python" %} {% include "img.html" %} {% endwith %}

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

We start with a bit of javascript. The function JGetCart just calls the url
that has been defined in the python code above.  The url consists of a full
path `plugin:plugin-name:url-name`. The plugin-name is the SLUG that was
defined in the plugin code. order.pk is the parameter that is passed to python.

The button is defined  with `class="btn btn-info` This is an InvenTree predefined button. There a are lots of others available.
Here are some examples of available colors:

{% with id="buttons", url="plugin/buttons.png", description="Button examples" %} {% include "img.html" %} {% endwith %}

Please have a look at the css files for more options. The last line renders the value that was defined in the plugin.

!!! tip "Give it a try"
    Each time you press the button, the value will be increased.

### Handling user input

A common user case is user input that needs to be passed from the panel into
the plugin for further processing. Lets have a look at another example. We
will define two user input fields. One is an integer the other one a string.
A button will be defined to submit the data. Something like that:

{% with id="panel_with_userinput", url="plugin/panel_with_userinput.png", description="Panel with user input" %} {% include "img.html" %} {% endwith %}

Here is the plugin code:

```python
from django.urls import path
from django.http import HttpResponse

from plugin import InvenTreePlugin
from plugin.mixins import PanelMixin, UrlsMixin

class ExamplePanel(PanelMixin, InvenTreePlugin, UrlsMixin):

    NAME = "ExamplePanel"
    SLUG = "examplepanel"
    TITLE = "Example for data input"
    AUTHOR = "Michael"
    DESCRIPTION = "This plugin passes user input from the panel to the plugin"

# Create the panel that will display on build detail view
    def get_custom_panels(self, view, request):
        panels = []
        if isinstance(view, BuildDetail):
	    self.build=view.get_object()
	    panels.append({
		'title': 'Example Info',
		'icon': 'fa-industry',
		'content_template': 'example_panel/example.html',
	    })
        return panels

    def setup_urls(self):
        return [
                path("example/<int:layer>/<path:size>/",
                    self.do_something, name = 'transfer'),
        ]

# Define the function that will be called.
    def do_something(self, request, layer, size):

        print('Example panel received:', layer, size)
        return HttpResponse(f'OK')
```

The start is easy because it is the same as in the example above.
Lets concentrate on the setup_urls. This time we use
path (imported from django.urls) instead of url for definition. Using path makes it easier to
define the data types. No regular expressions. The URL takes two parameters,
layer and size, and passes them to the python function do_something for further processing.
Now the html template:

```html
{% raw %}
<script>
async function example_select(){
    const layer_number = parseInt(document.getElementById("layer_number").value)
    const size = document.getElementById("string").value
    response = inventreeFormDataUpload(url="{% url 'plugin:examplepanel:transfer' '9999' 'Size' %}"
                                          .replace("9999", layer_number)
                                          .replace("Size", size)
                                      );
}
</script>

<form>
    Number of Layers<br>
    <input id="layer_number" type="number" value="2"><br>
    Size of Board in mm<br>
    <input id="string" type="text" value="100x160">
</form>

<input type="submit" value="Save" onclick="example_select()" title='Save Data'>
{% endraw %}
```

The HTML defines the form for user input, one number and one string. Each
form has an ID that is used in the javascript code to get the input of the form.
The response URL must match the URL defined in the plugin. Here we have a number
(999999) and a string (Size). These get replaced with the content of the fields
upon execution using replace. Watch out for the ticks around the 999999 and Size. They prevent
them from being interpreted by the django template engine and replaced by
something else.

The function inventreeFormDataUpload is a helper function defined by InvenTree
that does the POST request, handles errors and the csrftoken.

!!! tip "Give it a try"
    change the values in the fields and push Save. You will see the values
    in the InvenTree log.

#### If things are getting more complicated

In the example above we code all parameters into the URL. This is easy and OK
if you transfer just a few values. But the method has at least two disadvantages:

* When you have more parameters, things will get messy.
* When you have free text input fields, the user might enter characters that are not allowed in URL.

For those cases it is better to pack the data into a json container and transfer
this in the body of the request message. The changes are simple. Lets start with
the javascript:

```html
{% raw %}
<script>
async function example_select(){
    const layer_number = parseInt(document.getElementById("layer_number").value)
    const size = document.getElementById("string").value
    const cmd_url="{% url 'plugin:examplepanel:transfer' %}";
    data = {
        layer_number: layer_number,
        size: size
    }
    response = inventreeFormDataUpload(url=cmd_url, data=JSON.stringify(data))
}
</script>
{% endraw %}
```

Here we create a json container (data). The function stringify converts this to the
proper string format for transfer. That's all. The function inventreeFormDataUpload
does the rest of the work.

The python code in the plugin also needs minor changes:

```python
from django.conf.urls import url
import json

...

    def setup_urls(self):
        return [
                url(r'example(?:\.(?P<format>json))?$', self.do_something, name='transfer'),
        ]

# Define the function that will be called.
    def do_something(self, request):

        data=json.loads(request.body)
        print('Data received:', data)
```

The URL and the called function have no parameter names any longer. All data is in the
request message and can be extracted from this using json.loads. If more data is needed
just add it to the json container. No further changes are needed. It's really simple :-)

#### Populate a drop down field

Now we add a dropdown menu and fill it with values from the InvenTree database.

{% with id="panel_with_dropwdown", url="plugin/panel_with_dropdown.png", description="Panel with dropdown menu" %}
{% include "img.html" %}
{% endwith %}


```python
from company.models import Company

...

    def get_custom_panels(self, view, request):
        panels = []
        if isinstance(view, BuildDetail):
	    self.build=view.get_object()
            self.companies=Company.objects.filter(is_supplier=True)
            panels.append({
            ...
```
Here we create self.companies and fill it with all companies that have the is_supplier flag
set to true. This is available in the context of the template. A drop down menu can be created
by looping.


```html
{% raw %}
<select id="ems">
    {% for company in plugin.companies %}
	<option value="{{ company.id }}"> {{ company.name }} </option>
    {% endfor %}
</select>
{% endraw %}
```

The value of the select is the pk of the company. It can simply be added to the
json container and transferred to the plugin.

#### Store the Data
I case you plugin needs to store data permanently, InvenTree has a nice feature called
[metadata](metadata.md). You can easily store your values using the following
code:

```python
for key in data:
    self.build.metadata[key]=data[key]
self.build.save()
```
