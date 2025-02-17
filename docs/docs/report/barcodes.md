---
title: Barcode Generation
---

## Barcode Generation

Both [report](./report.md) and [label](./labels.md) templates can render custom barcode data to in-line images.

### Barcode Template Tags

To use the barcode tags inside a label or report template, you must load the `barcode` template tags at the top of the template file:

```html
{% raw %}
<!-- Load the barcode helper functions -->
{% load barcode %}
{% endraw %}
```

### Barcode Image Data

The barcode template tags will generate an image tag with the barcode data encoded as a base64 image. The image data is intended to be rendered as an `img` tag:

```html
{% raw %}
{% load barcode %}
<img class='custom_class' src='{% barcode "12345678" %}'>
{% endraw %}
```

## 1D Barcode

!!! info "python-barcode"
    One dimensional barcodes (e.g. Code128) are generated using the [python-barcode](https://pypi.org/project/python-barcode/) library.

To render a 1D barcode, use the `barcode` template tag:

::: report.templatetags.barcode.barcode
    options:
        show_docstring_description: False
        show_source: False

### Example

```html
{% raw %}

<!-- Don't forget to load the barcode helper! -->
{% load barcode %}

<img class='custom_class' src='{% barcode "12345678" %}'>

{% endraw %}
```

### Additional Options

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

## QR-Code

!!! info "qrcode"
    Two dimensional QR codes are generated using the [qrcode](https://pypi.org/project/qrcode/) library.

To render a QR code, use the `qrcode` template tag:

::: report.templatetags.barcode.qrcode
    options:
        show_docstring_description: false
        show_source: False

### Example

```html
{% raw %}
{% extends "label/label_base.html" %}

{% load l10n i18n barcode %}

{% block style %}

.qr {
    position: absolute;
    left: 0mm;
    top: 0mm;
    {% localize off %}
    height: {{ height }}mm;
    width: {{ height }}mm;
    {% endlocalize %}
}

{% endblock style %}

{% block content %}
<img class='qr' src='{% qrcode "Hello world!" fill_color="white" back_color="blue" %}'>
{% endblock content %}
{% endraw %}
```

which produces the following output:

{% with id="qrcode", url="report/qrcode.png", description="QR Code" %}
{% include 'img.html' %}
{% endwith %}


!!! tip "Documentation"
    Refer to the [qrcode library documentation](https://pypi.org/project/qrcode/) for more information


## Data Matrix

!!! info "ppf.datamatrix"
    Data Matrix codes are generated using the [ppf.datamatrix](https://pypi.org/project/ppf-datamatrix/) library.

[Data Matrix Codes](https://en.wikipedia.org/wiki/Data_Matrix) provide an alternative to QR codes for encoding data in a two-dimensional matrix. To render a Data Matrix code, use the `datamatrix` template tag:

::: report.templatetags.barcode.datamatrix
    options:
        show_docstring_description: false
        show_source: False

### Example

```html
{% raw %}
{% extends "label/label_base.html" %}

{% load l10n i18n barcode %}

{% block style %}

.qr {
    position: absolute;
    left: 0mm;
    top: 0mm;
    {% localize off %}
    height: {{ height }}mm;
    width: {{ height }}mm;
    {% endlocalize %}
}

{% endblock style %}

{% block content %}


<img class='qr' src='{% datamatrix "Foo Bar" back_color="yellow" %}'>

{% endblock content %}
{% endraw %}
```

which produces the following output:

{% with id="datamatrix", url="report/datamatrix.png", description="Datamatrix barcode" %}
{% include 'img.html' %}
{% endwith %}
