"""Plugin mixin classes for barcode plugin."""

from InvenTree.helpers import hash_barcode
from part.serializers import PartSerializer
from stock.models import StockItem
from stock.serializers import LocationSerializer, StockItemSerializer


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
