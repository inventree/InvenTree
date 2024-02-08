---
title: Stock Labels
---


## Stock Item Labels

Stock Item label templates are used to generate labels for individual Stock Items.

### Creating Stock Item Label Templates

Stock Item label templates are added (and edited) via the admin interface.

### Printing Stock Item Labels

Stock Item labels can be printed using the following approaches:

To print a single stock item from the Stock Item detail view, select the *Print Label* option as shown below:

{% with id='item_label_single', url='report/label_stock_print_single.png', description='Print single stock item label' %}
{% include 'img.html' %}
{% endwith %}

To print multiple stock items from the Stock table view, select the *Print Labels* option as shown below:

{% with id='item_label_multiple', url='report/label_stock_print_multiple.png', description='Print multiple stock item labels' %}
{% include 'img.html' %}
{% endwith %}

### Context Data

The following variables are made available to the StockItem label template:

| Variable | Description |
| -------- | ----------- |
| item | The [StockItem](../context_variables.md#stockitem) object itself |
| part | The [Part](../context_variables.md#part) object which is referenced by the [StockItem](../context_variables.md#stockitem) object |
| name | The `name` field of the associated Part object |
| ipn | The `IPN` field of the associated Part object |
| revision | The `revision` field of the associated Part object |
| quantity | The `quantity` field of the StockItem object |
| serial | The `serial` field of the StockItem object |
| uid | The `uid` field of the StockItem object |
| tests | Dict object of TestResult data associated with the StockItem |
| parameters | Dict object containing the parameters associated with the base Part |

### URL-style QR code

Stock Item labels support [QR code](../barcodes.md#qr-code) containing the stock item URL, which can be
scanned and opened directly
on a portable device using the camera or a QR code scanner. To generate a URL-style QR code for stock item in the [label HTML template](../labels.md#label-templates), add the
following HTML tag:

``` html
{% raw %}
<img class='custom_qr_class' src='{% qrcode qr_url %}'>
{% endraw %}
```

Make sure to customize the `custom_qr_class` CSS class to define the position of the QR code
on the label.
