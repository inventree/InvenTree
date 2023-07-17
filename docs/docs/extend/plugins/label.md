---
title: Label Mixin
---

## LabelPrintingMixin

The `LabelPrintingMixin` class allows plugins to provide custom label printing functionality. The specific implementation of a label printing plugin is quite flexible, allowing for the following functions (as a starting point):

- Printing a single label to a file, and allowing user to download
- Combining multiple labels onto a single page
- Supporting proprietary label sheet formats
- Offloading label printing to an external printer

### Entry Point

When printing labels against a particular plugin, the entry point is the `print_labels` method. The default implementation of this method iterates over each of the provided items, renders a PDF, and calls the `print_label` method for each item, providing the rendered PDF data.

Both the `print_labels` and `print_label` methods may be overridden by a plugin, allowing for complex functionality to be achieved.

For example, the `print_labels` method could be reimplemented to merge all labels into a single larger page, and return a single page for printing.

### Return Type

The `print_labels` method *must* return a JsonResponse object. If the method does not return such a response, an error will be raised by the server.

### File Generation

If the label printing plugin generates a real file, it should be stored as a `LabelOutput` instance in the database, and returned in the JsonResponse result under the 'file' key.

For example, the built-in `InvenTreeLabelPlugin` plugin generates a PDF file which contains all the provided labels concatenated together. A snippet of the code is shown below (refer to the source code for full details):

```python
# Save the generated file to the database
output = LabelOutput.objects.create(
    label=output_file,
    user=request.user
)

return JsonResponse({
    'file': output.label.url,
    'success': True,
    'message': f'{len(items)} labels generated'
})
```

### Background Printing

For some label printing processes (such as offloading printing to an external networked printer) it may be preferable to utilize the background worker process, and not block the front-end server.
The plugin provides an easy method to offload printing to the background thread.

Simply override the class attribute `BLOCKING_PRINT` as follows:

```python
class MyPrinterPlugin(LabelPrintingMixin, InvenTreePlugin):
    BLOCKING_PRINT = False
```

If the `print_labels` method is not changed, this will run the `print_label` method in a background worker thread.

!!! info "Example Plugin"
    Check out the [inventree-brother-plugin](https://github.com/inventree/inventree-brother-plugin) which provides native support for the Brother QL and PT series of networked label printers

!!! tip "Custom Code"
    If your plugin overrides the `print_labels` method, you will have to ensure that the label printing is correctly offloaded to the background worker. Look at the `offload_label` method of the plugin mixin class for how this can be achieved.

### Helper Methods

The plugin class provides a number of additional helper methods which may be useful for generating labels:

| Method | Description |
| --- | --- |
| render_to_pdf | Render label template to an in-memory PDF object |
| render_to_html | Render label template to a raw HTML string |
| render_to_png | Convert PDF data to an in-memory PNG image |

!!! info "Use the Source"
    These methods are available for more complex implementations - refer to the source code for more information!

### Merging Labels

To merge (combine) multiple labels into a single output (for example printing multiple labels on a single sheet of paper), the plugin must override the `print_labels` method and implement the required functionality.

## Integration

### Web Integration

If label printing plugins are enabled, they are able to be used directly from the InvenTree web interface:

{% with id="label_print", url="plugin/print_label_select_plugin.png", description="Print label via plugin" %}
{% include 'img.html' %}
{% endwith %}

### App Integration

Label printing plugins also allow direct printing of labels via the [mobile app](../../app/stock.md#print-label)

## Implementation

Plugins which implement the `LabelPrintingMixin` mixin class can be implemented by simply providing a `print_label` method.

### Simple Example

```python
from dummy_printer import printer_backend

class MyLabelPrinter(LabelPrintingMixin, InvenTreePlugin):
    """
    A simple example plugin which provides support for a dummy printer.

    A more complex plugin would communicate with an actual printer!
    """

    NAME = "MyLabelPrinter"
    SLUG = "mylabel"
    TITLE = "A dummy printer"

    # Set BLOCKING_PRINT to false to return immediately
    BLOCKING_PRINT = False

    def print_label(self, **kwargs):
        """
        Send the label to the printer

        kwargs:
            pdf_data: An in-memory PDF file of the label
            png_file: An in-memory PIL (pillow) Image file of the label
            filename: The filename of the printed label (if applicable)
            label_instance: The Label model instance
            width: width of the label (in mm)
            height: height of the label (in mm)
            user: The user who printed this label
        """

        width = kwargs['width']
        height = kwargs['height']

        # This dummy printer supports printing of raw image files
        printer_backend.print(png_file, w=width, h=height)
```

### Default Plugin

InvenTree supplies the `InvenTreeLabelPlugin` out of the box, which generates a PDF file which is then available for immediate download by the user.

The default plugin also features a *DEBUG* mode which generates a raw HTML output, rather than PDF. This can be handy for tracking down any template rendering errors in your labels.

### Available Data

The *label* data are supplied to the plugin in both `PDF` and `PNG` formats. This provides compatibility with a great range of label printers "out of the box". Conversion to other formats, if required, is left as an exercise for the plugin developer.

Other arguments provided to the `print_label` function are documented in the code sample above.
