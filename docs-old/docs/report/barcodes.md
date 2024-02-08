---
title: Barcode Generation
---

## Barcode Generation

Both [report](./report.md) and [label](./labels.md) templates can render custom barcode data to in-line images.

!!! info "img"
    Barcode data must be rendered inside an `<img>` tag.

Inside the template file (whether it be for printing a label or generating a custom report), the following code will need to be included at the top of the template file:

```html
{% raw %}
<!-- Load the barcode helper functions -->
{% load barcode %}
{% endraw %}
```

### 1D Barcode

!!! info "python-barcode"
    One dimensional barcodes (e.g. Code128) are generated using the [python-barcode](https://pypi.org/project/python-barcode/) library.

To render a 1D barcode, use the `barcode` template tag, as shown in the example below:

```html
{% raw %}

<!-- Don't forget to load the barcode helper! -->
{% load barcode %}

<img class='custom_class' src='{% barcode "12345678" %}'>

{% endraw %}
```

The default barcode renderer will generate a barcode using [Code128](https://en.wikipedia.org/wiki/Code_128) rendering. However [other barcode formats](https://python-barcode.readthedocs.io/en/stable/supported-formats.html) are also supported:

```html
{% raw %}

{% load barcode %}

<img class='custom_class' src='{% barcode "12345678" barcode_class="Code39" %}>
{% endraw %}
```

You can also pass further [python-barcode](https://python-barcode.readthedocs.io/en/stable/writers.html#common-writer-options) supported parameters as well:

```html
{% raw %}

{% load barcode %}

<img class='barcode' src='{% barcode part.IPN barcode_class="Code128" write_text=0 background="red" %}'>
{% endraw %}
```

### QR-Code

!!! info "qrcode"
    Two dimensional QR codes are generated using the [qrcode](https://pypi.org/project/qrcode/) library.

To render a QR code, use the `qrcode` template tag:

```html
{% raw %}

{% load barcode %}

<img class='custom_qr_class' src='{% qrcode "Hello world!" %}'>
{% endraw %}
```

Additional parameters can be passed to the `qrcode` function for rendering:

```html
{% raw %}
<img class='custom_qr_class' src='{% qrcode "Hello world!" fill_color="green" back_color="blue" %}'>
{% endraw %}
```

!!! tip "Documentation"
    Refer to the [qrcode library documentation](https://pypi.org/project/qrcode/) for more information
