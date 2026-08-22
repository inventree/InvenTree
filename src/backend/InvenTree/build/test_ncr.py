"""Unit tests for the NonConformance (NCR) models."""

from datetime import timedelta

from django.core.exceptions import ValidationError

import InvenTree.helpers
from InvenTree.unit_test import InvenTreeTestCase
from part.models import Part
from stock.models import StockItem

from .models import NonConformance, NonConformanceStockItem
from .status_codes import (
    NonConformanceDisposition,
    NonConformanceStatus,
    NonConformanceStatusGroups,
)


class NonConformanceModelTest(InvenTreeTestCase):
    """Tests for the NonConformance model itself (excluding state transitions)."""

    fixtures = ['category', 'part', 'location', 'stock']

    def test_reference_generation(self):
        """Newly created NCRs should get sequential, correctly formatted references."""
        part = Part.objects.get(pk=1)

        ncr_1 = NonConformance.objects.create(part=part, description='First issue')
        ncr_2 = NonConformance.objects.create(part=part, description='Second issue')

        self.assertEqual(ncr_1.reference, 'NCR-0001')
        self.assertEqual(ncr_2.reference, 'NCR-0002')
        self.assertEqual(str(ncr_1), 'NCR-0001')

    def test_default_status(self):
        """A freshly created NCR should default to OPEN status and PENDING-free of a disposition."""
        part = Part.objects.get(pk=1)
        ncr = NonConformance.objects.create(part=part, description='Some problem')

        self.assertEqual(ncr.status, NonConformanceStatus.OPEN.value)
        self.assertEqual(ncr.status_text, 'Open')

        # The NCR itself no longer carries a disposition field - it lives on
        # NonConformanceStockItem instead
        self.assertFalse(hasattr(ncr, 'disposition'))

    def test_target_date_validation(self):
        """The target date must not be before the creation date, once the NCR exists."""
        part = Part.objects.get(pk=1)
        ncr = NonConformance.objects.create(part=part, description='Some problem')

        # Creation date is auto-set to 'today'
        ncr.target_date = ncr.creation_date - timedelta(days=1)

        with self.assertRaises(ValidationError) as exc:
            ncr.full_clean()

        self.assertIn('target_date', exc.exception.message_dict)

        # A target date on or after the creation date is fine
        ncr.target_date = ncr.creation_date
        ncr.full_clean()

    def test_overdue_filter(self):
        """The overdue filter should only match open NCRs with a target date in the past."""
        part = Part.objects.get(pk=1)
        today = InvenTree.helpers.current_date()

        overdue = NonConformance.objects.create(
            part=part,
            description='Overdue issue',
            target_date=today - timedelta(days=1),
        )
        not_overdue = NonConformance.objects.create(
            part=part, description='Not overdue', target_date=today + timedelta(days=1)
        )
        no_target_date = NonConformance.objects.create(
            part=part, description='No target date set'
        )

        overdue_qs = NonConformance.objects.filter(NonConformance.get_overdue_filter())

        self.assertIn(overdue, overdue_qs)
        self.assertNotIn(not_overdue, overdue_qs)
        self.assertNotIn(no_target_date, overdue_qs)

        # Closing the overdue NCR should remove it from the overdue queryset,
        # even though its target date is still in the past
        overdue.investigate()
        overdue.disposition_ncr()
        overdue.close()

        overdue_qs = NonConformance.objects.filter(NonConformance.get_overdue_filter())
        self.assertNotIn(overdue, overdue_qs)


class NonConformanceStockItemModelTest(InvenTreeTestCase):
    """Tests for the NonConformanceStockItem link model."""

    fixtures = ['category', 'part', 'location', 'stock']

    def setUp(self):
        """Create a NonConformance to link stock items against."""
        super().setUp()

        self.part = Part.objects.get(pk=1)
        self.other_part = Part.objects.get(pk=3)

        self.ncr = NonConformance.objects.create(
            part=self.part, description='Bad batch of widgets'
        )

    def test_matching_part_allowed(self):
        """A stock item of the same part as the NCR may be linked."""
        stock_item = StockItem.objects.get(pk=1)
        self.assertEqual(stock_item.part, self.part)

        link = NonConformanceStockItem(ncr=self.ncr, stock_item=stock_item)
        link.full_clean()
        link.save()

        self.assertEqual(link.disposition, NonConformanceDisposition.PENDING.value)
        self.assertEqual(link.disposition_text, 'Pending')

    def test_mismatched_part_rejected(self):
        """A stock item of a *different* part than the NCR must be rejected."""
        stock_item = StockItem.objects.get(pk=1234)
        self.assertEqual(stock_item.part, self.other_part)
        self.assertNotEqual(stock_item.part, self.ncr.part)

        link = NonConformanceStockItem(ncr=self.ncr, stock_item=stock_item)

        with self.assertRaises(ValidationError) as exc:
            link.full_clean()

        self.assertIn('stock_item', exc.exception.message_dict)

        # And the link must not have been persisted
        self.assertEqual(
            NonConformanceStockItem.objects.filter(
                ncr=self.ncr, stock_item=stock_item
            ).count(),
            0,
        )

    def test_duplicate_link_rejected(self):
        """The same stock item cannot be linked to the same NCR twice."""
        stock_item = StockItem.objects.get(pk=1)

        NonConformanceStockItem.objects.create(ncr=self.ncr, stock_item=stock_item)

        duplicate = NonConformanceStockItem(ncr=self.ncr, stock_item=stock_item)

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_negative_quantity_rejected(self):
        """A negative affected quantity is not valid."""
        stock_item = StockItem.objects.get(pk=1)

        link = NonConformanceStockItem(ncr=self.ncr, stock_item=stock_item, quantity=-5)

        with self.assertRaises(ValidationError) as exc:
            link.full_clean()

        self.assertIn('quantity', exc.exception.message_dict)

    def test_disposition_choices(self):
        """A disposition can be set to any valid NonConformanceDisposition value."""
        stock_item = StockItem.objects.get(pk=1)
        link = NonConformanceStockItem.objects.create(
            ncr=self.ncr, stock_item=stock_item
        )

        link.disposition = NonConformanceDisposition.SCRAP.value
        link.full_clean()
        link.save()

        link.refresh_from_db()
        self.assertEqual(link.disposition_text, 'Scrap')


class NonConformanceTransitionTest(InvenTreeTestCase):
    """Tests for the NonConformance status state machine.

    Disposition is recorded per-linked-item (NonConformanceStockItem.disposition), but the
    NCR's own status transitions (OPEN -> INVESTIGATING -> DISPOSITIONED -> CLOSED, plus
    CANCELLED / reopening) live on the NonConformance model itself and are exercised here.
    """

    fixtures = ['category', 'part', 'location', 'stock']

    def setUp(self):
        """Create a fresh OPEN NonConformance for each test."""
        super().setUp()

        self.part = Part.objects.get(pk=1)
        self.ncr = NonConformance.objects.create(
            part=self.part, description='Bad batch of widgets'
        )

    def link_item(self, stock_pk, disposition=None):
        """Helper to link a stock item to self.ncr, optionally with a disposition."""
        link = NonConformanceStockItem.objects.create(
            ncr=self.ncr, stock_item=StockItem.objects.get(pk=stock_pk)
        )

        if disposition is not None:
            link.disposition = disposition
            link.save()

        return link

    def test_investigate(self):
        """OPEN -> INVESTIGATING is a valid transition."""
        self.assertEqual(self.ncr.status, NonConformanceStatus.OPEN.value)

        self.ncr.investigate()

        self.assertEqual(self.ncr.status, NonConformanceStatus.INVESTIGATING.value)

        # Refresh from DB to make sure the transition was actually persisted
        self.ncr.refresh_from_db()
        self.assertEqual(self.ncr.status, NonConformanceStatus.INVESTIGATING.value)

    def test_investigate_invalid_source(self):
        """INVESTIGATING -> INVESTIGATING (or from any closed state) is not a valid transition."""
        self.ncr.investigate()

        with self.assertRaises(ValidationError):
            self.ncr.investigate()

        self.assertEqual(self.ncr.status, NonConformanceStatus.INVESTIGATING.value)

    def test_disposition_blocked_by_pending_item(self):
        """disposition_ncr() must refuse to run while any linked item is still PENDING."""
        self.link_item(1, disposition=NonConformanceDisposition.SCRAP.value)
        self.link_item(2)  # left at the PENDING default

        self.ncr.investigate()

        with self.assertRaises(ValidationError) as exc:
            self.ncr.disposition_ncr()

        self.assertIn('disposition', exc.exception.message_dict)

        # Status must not have moved
        self.ncr.refresh_from_db()
        self.assertEqual(self.ncr.status, NonConformanceStatus.INVESTIGATING.value)

    def test_disposition_succeeds_once_all_items_dispositioned(self):
        """disposition_ncr() succeeds once every linked item has a non-PENDING disposition."""
        self.link_item(1, disposition=NonConformanceDisposition.SCRAP.value)
        self.link_item(2, disposition=NonConformanceDisposition.USE_AS_IS.value)

        self.ncr.investigate()
        self.ncr.disposition_ncr()

        self.assertEqual(self.ncr.status, NonConformanceStatus.DISPOSITIONED.value)

    def test_disposition_succeeds_with_no_linked_items(self):
        """An NCR with no linked stock items has nothing to check, and dispositions freely."""
        self.assertEqual(self.ncr.stock_items.count(), 0)

        self.ncr.investigate()
        self.ncr.disposition_ncr()

        self.assertEqual(self.ncr.status, NonConformanceStatus.DISPOSITIONED.value)

    def test_disposition_directly_from_open(self):
        """disposition_ncr() is also valid directly from OPEN (investigation is optional)."""
        self.ncr.disposition_ncr()

        self.assertEqual(self.ncr.status, NonConformanceStatus.DISPOSITIONED.value)

    def test_close_requires_dispositioned(self):
        """close() is only valid from DISPOSITIONED."""
        with self.assertRaises(ValidationError):
            self.ncr.close()

        self.ncr.investigate()

        with self.assertRaises(ValidationError):
            self.ncr.close()

        self.ncr.disposition_ncr()
        self.assertIsNone(self.ncr.closed_date)

        self.ncr.close()

        self.assertEqual(self.ncr.status, NonConformanceStatus.CLOSED.value)
        self.assertEqual(self.ncr.closed_date, InvenTree.helpers.current_date())

    def test_cancel_from_open_states(self):
        """cancel() is valid from OPEN, INVESTIGATING, and DISPOSITIONED."""
        for status in NonConformanceStatusGroups.OPEN_CODES:
            ncr = NonConformance.objects.create(
                part=self.part, description=f'Cancel test from {status}'
            )
            ncr.status = status
            ncr.save()

            ncr.cancel()

            self.assertEqual(ncr.status, NonConformanceStatus.CANCELLED.value)
            self.assertIsNotNone(ncr.closed_date)

    def test_cancel_from_closed_states_invalid(self):
        """cancel() is not valid once an NCR is already CLOSED or CANCELLED."""
        self.ncr.investigate()
        self.ncr.disposition_ncr()
        self.ncr.close()

        with self.assertRaises(ValidationError):
            self.ncr.cancel()

    def test_reopen_from_closed(self):
        """reopen() moves a CLOSED (or CANCELLED) NCR back to OPEN, clearing closed_date."""
        self.ncr.investigate()
        self.ncr.disposition_ncr()
        self.ncr.close()
        self.assertIsNotNone(self.ncr.closed_date)

        self.ncr.reopen()

        self.assertEqual(self.ncr.status, NonConformanceStatus.OPEN.value)
        self.assertIsNone(self.ncr.closed_date)

    def test_reopen_from_cancelled(self):
        """reopen() also works from CANCELLED."""
        self.ncr.cancel()
        self.ncr.reopen()

        self.assertEqual(self.ncr.status, NonConformanceStatus.OPEN.value)
        self.assertIsNone(self.ncr.closed_date)

    def test_reopen_invalid_source(self):
        """reopen() is not valid from an already-open state."""
        with self.assertRaises(ValidationError):
            self.ncr.reopen()

        self.ncr.investigate()

        with self.assertRaises(ValidationError):
            self.ncr.reopen()

    def test_full_lifecycle(self):
        """Walk an NCR through its entire lifecycle end-to-end."""
        self.link_item(1)

        self.assertEqual(self.ncr.status, NonConformanceStatus.OPEN.value)

        self.ncr.investigate()
        self.assertEqual(self.ncr.status, NonConformanceStatus.INVESTIGATING.value)

        # Can't disposition yet - the linked item is still PENDING
        with self.assertRaises(ValidationError):
            self.ncr.disposition_ncr()

        item = self.ncr.stock_items.get()
        item.disposition = NonConformanceDisposition.REWORK.value
        item.save()

        self.ncr.disposition_ncr()
        self.assertEqual(self.ncr.status, NonConformanceStatus.DISPOSITIONED.value)

        self.ncr.close()
        self.assertEqual(self.ncr.status, NonConformanceStatus.CLOSED.value)
        self.assertIsNotNone(self.ncr.closed_date)
