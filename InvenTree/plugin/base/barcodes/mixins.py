"""Plugin mixin classes for barcode plugin."""

import hashlib
import string

from part.serializers import PartSerializer
from stock.models import StockItem
from stock.serializers import LocationSerializer, StockItemSerializer


def hash_barcode(barcode_data):
    """Calculate an MD5 hash of barcode data.

    HACK: Remove any 'non printable' characters from the hash,
          as it seems browers will remove special control characters...

    TODO: Work out a way around this!
    """
    barcode_data = str(barcode_data).strip()

    printable_chars = filter(lambda x: x in string.printable, barcode_data)

    barcode_data = ''.join(list(printable_chars))

    result_hash = hashlib.md5(str(barcode_data).encode())
    return str(result_hash.hexdigest())


class BarcodeMixin:
    """Mixin that enables barcode handeling.

    Custom barcode plugins should use and extend this mixin as necessary.
    """

    ACTION_NAME = ""

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'Barcode'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('barcode', 'has_barcode', __class__)

    @property
    def has_barcode(self):
        """Does this plugin have everything needed to process a barcode."""
        return True

    def init(self, barcode_data):
        """Initialize the BarcodePlugin instance.

        Args:
            barcode_data: The raw barcode data
        """
        self.data = barcode_data

    def getStockItem(self):
        """Attempt to retrieve a StockItem associated with this barcode.

        Default implementation returns None
        """
        return None  # pragma: no cover

    def getStockItemByHash(self):
        """Attempt to retrieve a StockItem associated with this barcode, based on the barcode hash."""
        try:
            item = StockItem.objects.get(uid=self.hash())
            return item
        except StockItem.DoesNotExist:
            return None

    def renderStockItem(self, item):
        """Render a stock item to JSON response."""
        serializer = StockItemSerializer(item, part_detail=True, location_detail=True, supplier_part_detail=True)
        return serializer.data

    def getStockLocation(self):
        """Attempt to retrieve a StockLocation associated with this barcode.

        Default implementation returns None
        """
        return None  # pragma: no cover

    def renderStockLocation(self, loc):
        """Render a stock location to a JSON response."""
        serializer = LocationSerializer(loc)
        return serializer.data

    def getPart(self):
        """Attempt to retrieve a Part associated with this barcode.

        Default implementation returns None
        """
        return None  # pragma: no cover

    def renderPart(self, part):
        """Render a part to JSON response."""
        serializer = PartSerializer(part)
        return serializer.data

    def hash(self):
        """Calculate a hash for the barcode data.

        This is supposed to uniquely identify the barcode contents,
        at least within the bardcode sub-type.

        The default implementation simply returns an MD5 hash of the barcode data,
        encoded to a string.

        This may be sufficient for most applications, but can obviously be overridden
        by a subclass.
        """
        return hash_barcode(self.data)

    def validate(self):
        """Default implementation returns False."""
        return False  # pragma: no cover
