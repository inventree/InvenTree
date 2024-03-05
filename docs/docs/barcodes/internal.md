---
title: Internal Barcodes
---

## Internal Barcodes

InvenTree defines an internal format for generating barcodes for various items. This format uses a simple JSON-style string to uniquely identify an item in the database.

Some simple examples of this format are shown below:

| Model Type | Example Barcode |
| --- | --- |
| Part | `{% raw %}{"part": 10}{% endraw %}` |
| Stock Item | `{% raw %}{"stockitem": 123}{% endraw %}` |
| Supplier Part | `{% raw %}{"supplierpart": 99}{% endraw %}` |

The numerical ID value used is the *Primary Key* (PK) of the particular object in the database.

## Report Integration

This barcode format can be used to generate 1D or 2D barcodes (e.g. for [labels and reports](../report/barcodes.md))

To access the raw barcode information string within a template, use the `.barcode` attribute, and pass it into a barcode generation method.

### Example: QR Code

For example, to render a QR-Code image for a part instance:

```html
{% raw %}
<img src='{% qrcode part.barcode %}'>
{% endraw %}
```

!!! info "Barcode Formatting"
    Refer to the [report documentation](../report/barcodes.md) for further information on formatting barcode data
