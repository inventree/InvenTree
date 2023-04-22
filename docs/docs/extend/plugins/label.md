---
title: Label Mixin
---

## LabelPrintingMixin

The `LabelPrintingMixin` class enables plugins to print labels directly to a connected printer. Custom plugins can be written to support any printer backend.

An example of this is the [inventree-brother-plugin](https://github.com/inventree/inventree-brother-plugin) which provides native support for the Brother QL and PT series of networked label printers.

### Web Integration

If label printing plugins are enabled, they are able to be used directly from the InvenTree web interface:

{% with id="label_print", url="plugin/print_label_select_plugin.png", description="Print label via plugin" %}
{% include 'img.html' %}
{% endwith %}

### App Integration

Label printing plugins also allow direct printing of labels via the [mobile app](../../app/stock.md#print-label)

## Implementation

Plugins which implement the `LabelPrintingMixin` mixin class must provide a `print_label` function:

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

### Available Data

The *label* data are supplied to the plugin in both `PDF` and `PNG` formats. This provides compatibility with a great range of label printers "out of the box". Conversion to other formats, if required, is left as an exercise for the plugin developer.

Other arguments provided to the `print_label` function are documented in the code sample above.
