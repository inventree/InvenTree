from django.test import TestCase

from part.models import Part

class OrderTest(TestCase):
    """
    Tests to ensure that the order models are functioning correctly.
    """

    fixtures = [
        'company',
        'supplier_part',
        'category',
        'part',
        'location',
        'stock',
        'order'
    ]

    def test_on_order(self):
        """ There should be 3 separate items on order for the M2x4 LPHS part """

        part = Part.objects.get(name='M2x4 LPHS')

        open_orders = []

        for supplier in part.supplier_parts.all():
            open_orders += supplier.open_orders()

        self.assertEqual(len(open_orders), 3)

        # Test the total on-order quantity
        self.assertEqual(part.on_order, 400)
