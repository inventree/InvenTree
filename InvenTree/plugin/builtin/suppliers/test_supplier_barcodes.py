"""Tests barcode parsing for all suppliers."""

from django.urls import reverse

from company.models import Company, ManufacturerPart, SupplierPart
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part


class SupplierBarcodeTests(InvenTreeAPITestCase):
    """Tests barcode parsing for all suppliers."""

    @classmethod
    def setUpTestData(cls):
        """Create supplier parts for barcodes."""
        super().setUpTestData()

        part = Part.objects.create(name="Test Part", description="Test Part")

        manufacturer = Company.objects.create(
            name="Test Manufacturer", is_manufacturer=True)

        mpart1 = ManufacturerPart.objects.create(
            part=part, manufacturer=manufacturer, MPN="MC34063ADR")
        mpart2 = ManufacturerPart.objects.create(
            part=part, manufacturer=manufacturer, MPN="LDK320ADU33R")

        supplier = Company.objects.create(name="Supplier", is_supplier=True)
        mouser = Company.objects.create(name="Mouser Test", is_supplier=True)

        supplier_parts = [
            SupplierPart(
                SKU="296-LM358BIDDFRCT-ND", part=part, supplier=supplier),
            SupplierPart(
                SKU="1", part=part, manufacturer_part=mpart1, supplier=mouser),
            SupplierPart(
                SKU="2", part=part, manufacturer_part=mpart2, supplier=mouser),
            SupplierPart(
                SKU="C312270", part=part, supplier=supplier)
        ]

        SupplierPart.objects.bulk_create(supplier_parts)

    def test_digikey_barcode(self):
        """Test digikey barcode."""

        url = reverse("api-barcode-scan")
        result = self.post(url, data={"barcode": DIGIKEY_BARCODE})

        supplier_part_data = result.data.get("supplierpart")
        assert "pk" in supplier_part_data
        supplier_part = SupplierPart.objects.get(pk=supplier_part_data["pk"])
        assert supplier_part.SKU == "296-LM358BIDDFRCT-ND"

    def test_mouser_barcode(self):
        """Test mouser barcode with custom order number."""

        url = reverse("api-barcode-scan")
        result = self.post(url, data={"barcode": MOUSER_BARCODE})

        supplier_part_data = result.data.get("supplierpart")
        assert "pk" in supplier_part_data
        supplier_part = SupplierPart.objects.get(pk=supplier_part_data["pk"])
        assert supplier_part.SKU == "1"

    def test_old_mouser_barcode(self):
        """Test old mouser barcode with messed up header."""

        url = reverse("api-barcode-scan")
        result = self.post(url, data={"barcode": MOUSER_BARCODE_OLD})

        supplier_part_data = result.data.get("supplierpart")
        assert "pk" in supplier_part_data
        supplier_part = SupplierPart.objects.get(pk=supplier_part_data["pk"])
        assert supplier_part.SKU == "2"

    def test_lcsc_barcode(self):
        """Test LCSC barcode."""

        url = reverse("api-barcode-scan")
        result = self.post(url, data={"barcode": LCSC_BARCODE})

        supplier_part_data = result.data.get("supplierpart")
        assert supplier_part_data is not None

        assert "pk" in supplier_part_data
        supplier_part = SupplierPart.objects.get(pk=supplier_part_data["pk"])
        assert supplier_part.SKU == "C312270"


DIGIKEY_BARCODE = (
    "[)>\x1e06\x1dP296-LM358BIDDFRCT-ND\x1d1PLM358BIDDFR\x1dK\x1d1K72991337\x1d"
    "10K85781337\x1d11K1\x1d4LPH\x1dQ10\x1d11ZPICK\x1d12Z15221337\x1d13Z361337"
    "\x1d20Z0000000000000000000000000000000000000000000000000000000000000000000"
    "00000000000000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000"
)

MOUSER_BARCODE = (
    "[)>\x1e06\x1dKP0-1337\x1d14K011\x1d1PMC34063ADR\x1dQ3\x1d11K073121337\x1d4"
    "LMX\x1d1VTI\x1e\x04"
)

MOUSER_BARCODE_OLD = (
    ">[)>06\x1dK21421337\x1d14K033\x1d1PLDK320ADU33R\x1dQ32\x1d11K060931337\x1d"
    "4LCN\x1d1VSTMicro"
)

LCSC_BARCODE = (
    "{pbn:PICK2009291337,on:SO2009291337,pc:C312270,pm:ST-1-102-A01-T000-RS,qty"
    ":2,mc:,cc:1,pdi:34421807}"
)
