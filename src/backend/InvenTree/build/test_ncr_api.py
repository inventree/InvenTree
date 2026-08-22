"""Unit tests for the NonConformance (NCR) API endpoints."""

from django.urls import reverse

from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part
from stock.models import StockItem

from .models import NonConformance, NonConformanceStockItem
from .status_codes import NonConformanceDisposition, NonConformanceStatus


class NCRAPITest(InvenTreeAPITestCase):
    """Tests for the NonConformance (NCR) list/detail/transition API endpoints."""

    fixtures = ['category', 'part', 'location', 'stock']

    roles = ['ncr.view']

    def setUp(self):
        """Cache commonly used part / stock item references."""
        super().setUp()

        self.part = Part.objects.get(pk=1)
        self.other_part = Part.objects.get(pk=3)

    def test_options(self):
        """OPTIONS on the list endpoint should expose the auto-generated reference default."""
        self.assignRole('ncr.add')

        data = self.options(reverse('api-ncr-list'), expected_code=200).data
        post = data['actions']['POST']

        self.assertEqual(post['reference']['default'], 'NCR-0001')
        self.assertTrue(post['part']['required'])
        self.assertTrue(post['description']['required'])

        # status and status_text are read-only - can't be set on create
        self.assertTrue(post['status']['read_only'])

    def test_list_permission_required(self):
        """The list endpoint requires 'ncr.view' - which this test class has by default."""
        response = self.get(reverse('api-ncr-list'), expected_code=200)
        self.assertEqual(len(response.data), 0)

    def test_create_requires_permission(self):
        """Creating an NCR requires the 'ncr.add' permission."""
        url = reverse('api-ncr-list')

        data = self.post(
            url,
            {'part': self.part.pk, 'description': 'A quality issue'},
            expected_code=403,
        )

        self.assignRole('ncr.add')

        data = self.post(
            url,
            {'part': self.part.pk, 'description': 'A quality issue'},
            expected_code=201,
        ).data

        self.assertEqual(data['reference'], 'NCR-0001')
        self.assertEqual(data['status'], NonConformanceStatus.OPEN.value)

        # The user who created the NCR should be recorded automatically
        ncr = NonConformance.objects.get(pk=data['pk'])
        self.assertEqual(ncr.raised_by, self.user)

    def test_update_requires_permission(self):
        """Updating an NCR requires the 'ncr.change' permission.

        Note: created directly via the ORM (not the API) so that this test doesn't
        need the 'ncr.add' permission - which would grant 'ncr.change' too, per
        RuleSet.save()'s "can't change/delete without being able to view/change"
        cascade, and defeat the negative-permission check below.
        """
        ncr = NonConformance.objects.create(part=self.part, description='Original')

        url = reverse('api-ncr-detail', kwargs={'pk': ncr.pk})

        self.patch(url, {'description': 'Updated'}, expected_code=403)

        self.assignRole('ncr.change')
        self.patch(url, {'description': 'Updated'}, expected_code=200)

        ncr.refresh_from_db()
        self.assertEqual(ncr.description, 'Updated')

    def test_delete_requires_permission(self):
        """Deleting an NCR requires the 'ncr.delete' permission."""
        ncr = NonConformance.objects.create(part=self.part, description='Doomed')

        url = reverse('api-ncr-detail', kwargs={'pk': ncr.pk})

        self.delete(url, expected_code=403)

        self.assignRole('ncr.delete')
        self.delete(url, expected_code=204)

        self.assertFalse(NonConformance.objects.filter(pk=ncr.pk).exists())

    def test_list_filters(self):
        """Test filtering the NCR list by part / status / active."""
        self.assignRole('ncr.add')

        ncr_1 = NonConformance.objects.create(part=self.part, description='Issue 1')
        ncr_2 = NonConformance.objects.create(
            part=self.other_part, description='Issue 2'
        )
        ncr_2.investigate()

        url = reverse('api-ncr-list')

        # Filter by part
        data = self.get(url, {'part': self.part.pk}, expected_code=200).data
        self.assertEqual([r['pk'] for r in data], [ncr_1.pk])

        # Filter by status
        data = self.get(
            url, {'status': NonConformanceStatus.INVESTIGATING.value}, expected_code=200
        ).data
        self.assertEqual([r['pk'] for r in data], [ncr_2.pk])

        # 'active' filter should include both (neither is closed/cancelled)
        data = self.get(url, {'active': True}, expected_code=200).data
        self.assertEqual({r['pk'] for r in data}, {ncr_1.pk, ncr_2.pk})

    def test_investigate_endpoint(self):
        """Test the 'investigate' transition endpoint."""
        self.assignRole('ncr.add')
        ncr = NonConformance.objects.create(part=self.part, description='Issue')

        url = reverse('api-ncr-investigate', kwargs={'pk': ncr.pk})

        # No permission yet to perform the action (view-only wouldn't cover POST)
        self.clearRoles()
        self.post(url, expected_code=403)

        self.assignRole('ncr.add')
        self.post(url, expected_code=201)

        ncr.refresh_from_db()
        self.assertEqual(ncr.status, NonConformanceStatus.INVESTIGATING.value)

    def test_invalid_transition_returns_400(self):
        """Calling a transition endpoint from an invalid source state returns HTTP 400."""
        self.assignRole('ncr.add')
        ncr = NonConformance.objects.create(part=self.part, description='Issue')

        # Can't close an NCR that hasn't been dispositioned yet
        url = reverse('api-ncr-close', kwargs={'pk': ncr.pk})
        response = self.post(url, expected_code=400)

        self.assertIn('non_field_errors', response.data)

        ncr.refresh_from_db()
        self.assertEqual(ncr.status, NonConformanceStatus.OPEN.value)

    def test_transition_endpoint_404_for_unknown_pk(self):
        """Transition endpoints should 404 for a non-existent NCR (once permission is granted)."""
        self.assignRole('ncr.add')

        url = reverse('api-ncr-investigate', kwargs={'pk': 999999})
        self.post(url, expected_code=404)

    def test_disposition_endpoint_full_flow(self):
        """Exercise the full disposition workflow through the API.

        - disposition is blocked while a linked item is still PENDING
        - setting the item's disposition via PATCH unblocks it
        - disposition succeeds and moves status to DISPOSITIONED
        - close then succeeds
        """
        self.assignRole('ncr.add')
        self.assignRole('ncr.change')

        ncr = NonConformance.objects.create(part=self.part, description='Batch issue')
        item = NonConformanceStockItem.objects.create(
            ncr=ncr, stock_item=StockItem.objects.get(pk=1)
        )

        self.post(
            reverse('api-ncr-investigate', kwargs={'pk': ncr.pk}), expected_code=201
        )

        disposition_url = reverse('api-ncr-disposition', kwargs={'pk': ncr.pk})

        # Item is still PENDING - blocked. The model raises a dict-keyed
        # ValidationError here (not a bare message), so it surfaces under its
        # field name rather than 'non_field_errors'.
        response = self.post(disposition_url, expected_code=400)
        self.assertIn('disposition', response.data)

        # Set the item's disposition via the stock-item endpoint
        item_url = reverse('api-ncr-stock-item-detail', kwargs={'pk': item.pk})
        self.patch(
            item_url,
            {'disposition': NonConformanceDisposition.USE_AS_IS.value},
            expected_code=200,
        )

        # Now the disposition transition should succeed
        self.post(disposition_url, expected_code=201)

        ncr.refresh_from_db()
        self.assertEqual(ncr.status, NonConformanceStatus.DISPOSITIONED.value)

        # And now it can be closed
        self.post(reverse('api-ncr-close', kwargs={'pk': ncr.pk}), expected_code=201)

        ncr.refresh_from_db()
        self.assertEqual(ncr.status, NonConformanceStatus.CLOSED.value)
        self.assertIsNotNone(ncr.closed_date)

    def test_cancel_and_reopen_endpoints(self):
        """Test the 'cancel' and 'reopen' transition endpoints."""
        self.assignRole('ncr.add')
        ncr = NonConformance.objects.create(part=self.part, description='Issue')

        self.post(reverse('api-ncr-cancel', kwargs={'pk': ncr.pk}), expected_code=201)

        ncr.refresh_from_db()
        self.assertEqual(ncr.status, NonConformanceStatus.CANCELLED.value)

        self.post(reverse('api-ncr-reopen', kwargs={'pk': ncr.pk}), expected_code=201)

        ncr.refresh_from_db()
        self.assertEqual(ncr.status, NonConformanceStatus.OPEN.value)
        self.assertIsNone(ncr.closed_date)

    def test_status_and_disposition_code_endpoints(self):
        """The status/disposition metadata endpoints should list all known codes."""
        status_data = self.get(reverse('api-ncr-status-codes'), expected_code=200).data
        disposition_data = self.get(
            reverse('api-ncr-disposition-codes'), expected_code=200
        ).data

        status_values = {entry['key'] for entry in status_data['values'].values()}
        disposition_values = {
            entry['key'] for entry in disposition_data['values'].values()
        }

        self.assertEqual(status_values, {s.value for s in NonConformanceStatus})
        self.assertEqual(
            disposition_values, {d.value for d in NonConformanceDisposition}
        )


class NCRStockItemAPITest(InvenTreeAPITestCase):
    """Tests for the NonConformanceStockItem API endpoint."""

    fixtures = ['category', 'part', 'location', 'stock']

    roles = ['ncr.view']

    def setUp(self):
        """Create a base NCR to link stock items against."""
        super().setUp()

        self.part = Part.objects.get(pk=1)
        self.other_part = Part.objects.get(pk=3)

        # Created directly via the ORM (not the API) so no permission is needed here,
        # and each test starts from a clean permission slate.
        self.ncr = NonConformance.objects.create(
            part=self.part, description='Bad batch'
        )

    def test_create_requires_permission(self):
        """Linking a stock item requires the 'ncr.add' permission."""
        self.clearRoles()

        url = reverse('api-ncr-stock-item-list')
        data = {'ncr': self.ncr.pk, 'stock_item': 1}

        self.post(url, data, expected_code=403)

        self.assignRole('ncr.add')
        response = self.post(url, data, expected_code=201)

        self.assertEqual(
            response.data['disposition'], NonConformanceDisposition.PENDING.value
        )

    def test_part_mismatch_rejected_via_api(self):
        """Linking a stock item of the wrong part must fail with a 400, not a 500."""
        self.assignRole('ncr.add')

        url = reverse('api-ncr-stock-item-list')

        # Stock item 1234 belongs to self.other_part, not self.ncr.part
        response = self.post(
            url, {'ncr': self.ncr.pk, 'stock_item': 1234}, expected_code=400
        )

        self.assertIn('stock_item', response.data)

        self.assertEqual(
            NonConformanceStockItem.objects.filter(ncr=self.ncr).count(), 0
        )

    def test_update_disposition_requires_permission(self):
        """Updating an item's disposition requires the 'ncr.change' permission."""
        item = NonConformanceStockItem.objects.create(
            ncr=self.ncr, stock_item=StockItem.objects.get(pk=1)
        )

        url = reverse('api-ncr-stock-item-detail', kwargs={'pk': item.pk})

        self.patch(
            url,
            {'disposition': NonConformanceDisposition.SCRAP.value},
            expected_code=403,
        )

        self.assignRole('ncr.change')
        self.patch(
            url,
            {'disposition': NonConformanceDisposition.SCRAP.value},
            expected_code=200,
        )

        item.refresh_from_db()
        self.assertEqual(item.disposition, NonConformanceDisposition.SCRAP.value)

    def test_filter_by_disposition(self):
        """Test filtering the stock-item list by disposition."""
        pending = NonConformanceStockItem.objects.create(
            ncr=self.ncr, stock_item=StockItem.objects.get(pk=1)
        )
        scrapped = NonConformanceStockItem.objects.create(
            ncr=self.ncr, stock_item=StockItem.objects.get(pk=2)
        )
        scrapped.disposition = NonConformanceDisposition.SCRAP.value
        scrapped.save()

        url = reverse('api-ncr-stock-item-list')

        data = self.get(
            url,
            {'disposition': NonConformanceDisposition.PENDING.value},
            expected_code=200,
        ).data
        self.assertEqual([r['pk'] for r in data], [pending.pk])

        data = self.get(
            url,
            {'disposition': NonConformanceDisposition.SCRAP.value},
            expected_code=200,
        ).data
        self.assertEqual([r['pk'] for r in data], [scrapped.pk])

    def test_delete_requires_permission(self):
        """Unlinking a stock item requires the 'ncr.delete' permission."""
        item = NonConformanceStockItem.objects.create(
            ncr=self.ncr, stock_item=StockItem.objects.get(pk=1)
        )

        url = reverse('api-ncr-stock-item-detail', kwargs={'pk': item.pk})

        self.delete(url, expected_code=403)

        self.assignRole('ncr.delete')
        self.delete(url, expected_code=204)

        self.assertFalse(NonConformanceStockItem.objects.filter(pk=item.pk).exists())
