---
title: Barcode Mixin
---

## Barcode Plugins

InvenTree supports decoding of arbitrary barcode data and generation of internal barcode formats via a **Barcode Plugin** interface. Barcode data POSTed to the `/api/barcode/` endpoint will be supplied to all loaded barcode plugins, and the first plugin to successfully interpret the barcode data will return a response to the client.

InvenTree can generate native QR codes to represent database objects (e.g. a single StockItem). This barcode can then be used to perform quick lookup of a stock item or location in the database. A client application (for example the InvenTree mobile app) scans a barcode, and sends the barcode data to the InvenTree server. The server then uses the **InvenTreeBarcodePlugin** (found at `src/backend/InvenTree/plugin/builtin/barcodes/inventree_barcode.py`) to decode the supplied barcode data.

Any third-party barcodes can be decoded by writing a matching plugin to decode the barcode data. These plugins could then perform a server-side action or render a JSON response back to the client for further action.

Some examples of possible uses for barcode integration:

- Stock lookup by scanning a barcode on a box of items
- Receiving goods against a PurchaseOrder by scanning a supplier barcode
- Perform a stock adjustment action (e.g. take 10 parts from stock whenever a barcode is scanned)

Barcode data are POSTed to the server as follows:

```
POST {
    barcode_data: "[(>someBarcodeDataWhichThePluginKnowsHowToDealWith"
}
```

### Builtin Plugin

The InvenTree server includes a builtin barcode plugin which can generate and decode the QR codes. This plugin is enabled by default.

::: plugin.builtin.barcodes.inventree_barcode.InvenTreeInternalBarcodePlugin
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []


### Example Plugin

Please find below a very simple example that is used to return a part if the barcode starts with `PART-`

```python
from plugin import InvenTreePlugin
from plugin.mixins import BarcodeMixin
from part.models import Part

class InvenTreeBarcodePlugin(BarcodeMixin, InvenTreePlugin):

    NAME = "MyBarcode"
    TITLE = "My Barcodes"
    DESCRIPTION = "support for barcodes"
    VERSION = "0.0.1"
    AUTHOR = "Michael"

    def scan(self, barcode_data):
        if barcode_data.startswith("PART-"):
            try:
                pk = int(barcode_data.split("PART-")[1])
                instance = Part.objects.get(pk=pk)
                label = Part.barcode_model_type()

                return {label: instance.format_matched_response()}
            except Part.DoesNotExist:
                pass
```

To try it just copy the file to src/InvenTree/plugins and restart the server. Open the scan barcode window and start to scan codes or type in text manually. Each time the timeout is hit the plugin will execute and printout the result. The timeout can be changed in `Settings->Barcode Support->Barcode Input Delay`.

### Custom Internal Format

To implement a custom internal barcode format, the `generate(...)` method from the Barcode Mixin needs to be overridden. Then the plugin can be selected at `System Settings > Barcodes > Barcode Generation Plugin`.

```python
from InvenTree.models import InvenTreeBarcodeMixin
from plugin import InvenTreePlugin
from plugin.mixins import BarcodeMixin

class InvenTreeBarcodePlugin(BarcodeMixin, InvenTreePlugin):
    NAME = "MyInternalBarcode"
    TITLE = "My Internal Barcodes"
    DESCRIPTION = "support for custom internal barcodes"
    VERSION = "0.0.1"
    AUTHOR = "InvenTree contributors"

    def generate(self, model_instance: InvenTreeBarcodeMixin):
        return f'{model_instance.barcode_model_type()}: {model_instance.pk}'
```

!!! info "Scanning implementation required"
    The parsing of the custom format needs to be implemented too, so that the scanning of the generated QR codes resolves to the correct part.
