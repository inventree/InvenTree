---
title: Internal Barcodes
---

## Internal Barcodes

InvenTree ships with two integrated internal formats for generating barcodes for various items which are available through the built-in InvenTree Barcode plugin. The used format can be selected through the plugin settings of the InvenTree Barcode plugin.

### 1. JSON-based QR Codes

This format uses a simple JSON-style string to uniquely identify an item in the database.

Some simple examples of this format are shown below:

| Model Type | Example Barcode |
| --- | --- |
| Part | `{% raw %}{"part": 10}{% endraw %}` |
| Stock Item | `{% raw %}{"stockitem": 123}{% endraw %}` |
| Stock Location | `{% raw %}{"stocklocation": 1}{% endraw %}` |
| Supplier Part | `{% raw %}{"supplierpart": 99}{% endraw %}` |

The numerical ID value used is the *Primary Key* (PK) of the particular object in the database.

#### Downsides

1. The JSON format includes binary only characters (`{% raw %}{{% endraw %}` and `{% raw %}"{% endraw %}`) which requires unnecessary use of the binary QR code encoding which means fewer amount of chars can be encoded with the same version of QR code.
2. The model name key has not a fixed length. Some model names are longer than others. E.g. a part QR code with the shortest possible id requires 11 chars, while a stock location QR code with the same id would already require 20 chars, which already requires QR code version 2 and quickly version 3.

!!! info "QR code versions"
    There are 40 different qr code versions from 1-40. They all can encode more data than the previous version, but require more "squares". E.g. a V1 QR codes has 21x21 "squares" while a V2 already has 25x25. For more information see [QR code comparison](https://www.qrcode.com/en/about/version.html).

For a more detailed size analysis of the JSON-based QR codes refer to [this issue](https://github.com/inventree/InvenTree/issues/6612).

### 2. Short alphanumeric QR Codes

While JSON-based QR Codes encode all necessary information, they come with the described downsides. This new, short, alphanumeric only format is build to improve those downsides. The basic format uses an alphanumeric string: `INV-??x`

- `INV-` is a constant prefix. This is configurable in the InvenTree Barcode plugins settings per instance to support environments that use multiple instances.
- `??` is a two character alphanumeric (`0-9A-Z  $%*+-./:` (45 chars)) code, individual to each model.
- `x` the actual pk of the model.

Now with an overhead of 6 chars for every model, this format supports the following amount of model instances using the described QR code modes:

| QR code mode | Alphanumeric mode | Mixed mode |
| --- | --- | --- |
| v1 M ECL (15%) | `10**14` items (~3.170 items per sec for 1000 years) | `10**20` items (~3.170.979.198 items per sec for 1000 years) |
| v1 Q ECL (25%) | `10**10` items (~0.317 items per sec for 1000 years) | `10**13` items (~317 items per sec for 1000 years) |
| v1 H ECL (30%) | `10**4` items (~100 items per day for 100 days) | `10**3` items (~100 items per day for 10 days (*even worse*)) |

!!! info "QR code mixed mode"
    Normally the QR code data is encoded only in one format (binary, alphanumeric, numeric). But the data can also be split into multiple chunks using different formats. This is especially useful with long model ids, because the first 6 chars can be encoded using the alphanumeric mode and the id using the more efficient numeric mode. Mixed mode is used by default, because the `qrcode` template tag uses a default value for optimize of 1.

Some simple examples of this format are shown below:

| Model Type | Example Barcode |
| --- | --- |
| Part | `INV-PA10` |
| Stock Item | `INV-SI123` |
| Stock Location | `INV-SL1` |
| Supplier Part | `INV-SP99` |

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
