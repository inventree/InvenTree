---
title: Barcode Mixin
---

### Barcode Plugins

InvenTree supports decoding of arbitrary barcode data via a **Barcode Plugin** interface. Barcode data POSTed to the `/api/barcode/` endpoint will be supplied to all loaded barcode plugins, and the first plugin to successfully interpret the barcode data will return a response to the client.

InvenTree can generate native QR codes to represent database objects (e.g. a single StockItem). This barcode can then be used to perform quick lookup of a stock item or location in the database. A client application (for example the InvenTree mobile app) scans a barcode, and sends the barcode data to the InvenTree server. The server then uses the **InvenTreeBarcodePlugin** (found at `/InvenTree/plugins/barcode/inventree.py`) to decode the supplied barcode data.

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

### Example
Please find below a very simple example that is executed each time a barcode is scanned.

```python
from django.utils.translation import gettext_lazy as _

from InvenTree.models import InvenTreeBarcodeMixin
from plugin import InvenTreePlugin
from plugin.mixins import BarcodeMixin

class InvenTreeBarcodePlugin(BarcodeMixin, InvenTreePlugin):

    NAME = "MyBarcode"
    TITLE = "My Barcodes"
    DESCRIPTION = "support for barcodes"
    VERSION = "0.0.1"
    AUTHOR = "Michael"

    status = 0

    def scan(self, barcode_data):

        self.status = self.status+1
        print('Started barcode plugin', self.status)
        print(barcode_data)
        response = {}
        return response

```

To try it just copy the file to src/InvenTree/plugins and restart the server. Open the scan barcode window and start to scan codes or type in text manually. Each time the timeout is hit the plugin will execute and printout the result. The timeout can be changed in `Settings->Barcode Support->Barcode Input Delay`.
