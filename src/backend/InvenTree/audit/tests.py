"""Unit tests for the audit app.

No production models are audited yet, so these tests temporarily register
PurchaseOrder (parent) and PurchaseOrderLineItem (child) with the audit log.
"""

import contextlib
from base64 import b64encode
from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from auditlog.registry import auditlog

import audit.context
from audit.helpers import write_batched
from audit.models import MASKED_VALUE, AuditLogEntry, mask_changes
from audit.registry import BASE_EXCLUDE_FIELDS, audited_models, register_model
from audit.serializers import AuditLogEntrySerializer
from audit.tasks import delete_old_audit_entries
from common.settings import set_global_setting
from company.models import Company, SupplierPart
from InvenTree.unit_test import InvenTreeAPITestCase
from order.models import PurchaseOrder, PurchaseOrderLineItem
from part.models import Part

TEST_MODELS = [PurchaseOrder, PurchaseOrderLineItem]


def setting_content_type():
    """Return the ContentType for global settings."""
    from common.models import InvenTreeSetting

    return ContentType.objects.get_for_model(InvenTreeSetting)


def audited_entries():
    """Return all audit entries, except for changes to global settings.

    Changes to the audit log settings are always recorded,
    even when the audit log is disabled.
    """
    return AuditLogEntry.objects.exclude(content_type=setting_content_type())


class AuditTestMixin:
    """Ensure that the test models are registered with the audit log.

    Models which are already audited (in production) are left registered as they are -
    only models registered here are unregistered again afterwards.
    """

    @classmethod
    def setUpClass(cls):
        """Register test models before any test data is created."""
        cls.parent_patch = mock.patch.object(
            PurchaseOrderLineItem,
            'get_audit_parent',
            lambda self: self.order,
            create=True,
        )
        cls.parent_patch.start()

        cls.registered_models = [
            model for model in TEST_MODELS if not auditlog.contains(model)
        ]

        for model in cls.registered_models:
            register_model(model)

        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        """Unregister test models."""
        super().tearDownClass()

        for model in cls.registered_models:
            auditlog.unregister(model)

        cls.parent_patch.stop()

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super().setUpTestData()

        cls.supplier = Company.objects.create(name='Audit Supplier', is_supplier=True)
        cls.part = Part.objects.create(
            name='Audit Part', description='A part', purchaseable=True
        )
        cls.supplier_part = SupplierPart.objects.create(
            part=cls.part, supplier=cls.supplier, SKU='AUDIT-SKU'
        )
        cls.po = PurchaseOrder.objects.create(
            reference='PO-88880001', supplier=cls.supplier, description='Original'
        )

    def entries_for(self, instance, **kwargs):
        """Return audit entries recorded directly against the provided instance."""
        return AuditLogEntry.objects.get_for_object(instance).filter(**kwargs)


class AuditRegistryTest(TestCase):
    """Tests for model registration."""

    def test_audited_models(self):
        """Only the expected production models opt in to the audit log."""
        self.assertEqual(
            [model._meta.label_lower for model in audited_models()],
            [
                'build.build',
                'common.attachment',
                'common.customunit',
                'common.inventreesetting',
                'common.parameter',
                'common.parametertemplate',
                'common.projectcode',
                'company.address',
                'company.company',
                'company.contact',
                'company.manufacturerpart',
                'company.supplierpart',
                'company.supplierpricebreak',
                'order.purchaseorder',
                'order.purchaseorderextraline',
                'order.purchaseorderlineitem',
                'order.returnorder',
                'order.returnorderextraline',
                'order.returnorderlineitem',
                'order.salesorder',
                'order.salesorderextraline',
                'order.salesorderlineitem',
                'order.salesordershipment',
                'order.transferorder',
                'order.transferorderlineitem',
                'part.bomitem',
                'part.bomitemsubstitute',
                'part.part',
                'part.partcategory',
                'pricing.partinternalpricebreak',
                'pricing.partpricing',
                'pricing.partsellpricebreak',
                'stock.stockitem',
            ],
        )

        for model in audited_models():
            self.assertTrue(auditlog.contains(model))

    def test_register_model(self):
        """Registration applies the base excluded fields."""
        from common.models import NotificationEntry

        # Note: a model which is *not* audited in production
        self.assertFalse(auditlog.contains(NotificationEntry))

        register_model(NotificationEntry, exclude_fields=['notes'])

        try:
            self.assertTrue(auditlog.contains(NotificationEntry))
            exclude = auditlog.get_model_fields(NotificationEntry)['exclude_fields']

            for field in [*BASE_EXCLUDE_FIELDS, 'notes']:
                self.assertIn(field, exclude)
        finally:
            auditlog.unregister(NotificationEntry)

    def test_mask_changes(self):
        """All values are replaced when masking changes."""
        changes = {
            'value': ['old-secret', 'new-secret'],
            'tags': {'type': 'm2m', 'operation': 'add', 'objects': ['a', 'b']},
        }

        masked = mask_changes(changes)

        self.assertEqual(masked['value'], [MASKED_VALUE, MASKED_VALUE])
        self.assertEqual(masked['tags']['objects'], [MASKED_VALUE, MASKED_VALUE])
        self.assertEqual(masked['tags']['operation'], 'add')
        self.assertNotIn('secret', str(masked))


class AuditModelTest(AuditTestMixin, TestCase):
    """Tests for audit entry creation."""

    def test_create_update_delete(self):
        """Basic create / update / delete operations are recorded."""
        self.assertEqual(
            self.entries_for(self.po, action=AuditLogEntry.Action.CREATE).count(), 1
        )

        self.po.description = 'Updated'
        self.po.save()

        entry = self.entries_for(self.po, action=AuditLogEntry.Action.UPDATE).first()
        self.assertEqual(entry.changes_dict['description'], ['Original', 'Updated'])
        self.assertIsNone(entry.parent_content_type)

        # Excluded fields are not recorded
        self.assertNotIn('reference_int', entry.changes_dict)
        self.assertNotIn('metadata', entry.changes_dict)

    def test_empty_values_equivalent(self):
        """Changing a field between None and '' is not recorded as a change."""
        Part.objects.filter(pk=self.part.pk).update(IPN=None)
        self.part.refresh_from_db()

        # Saving an empty value from a form ('') over NULL
        self.part.IPN = ''
        self.part.description = 'Updated'
        self.part.save()

        entry = self.entries_for(self.part, action=AuditLogEntry.Action.UPDATE).last()
        self.assertEqual(entry.changes_dict, {'description': ['A part', 'Updated']})

        # No entry is created if the only "change" is between empty values
        self.part.IPN = None
        self.part.save()

        self.assertEqual(
            self.entries_for(self.part, action=AuditLogEntry.Action.UPDATE).count(), 1
        )

        # A real change to or from an empty value is still recorded
        self.part.IPN = 'IPN-001'
        self.part.save()
        self.part.IPN = ''
        self.part.save()

        entries = self.entries_for(self.part, action=AuditLogEntry.Action.UPDATE)
        self.assertEqual(
            [e.changes_dict['IPN'] for e in entries.order_by('pk')[1:]],
            [[None, 'IPN-001'], ['IPN-001', '']],
        )

    def test_parent_link(self):
        """Child entries are linked to the parent - and are retained after deletion."""
        line = PurchaseOrderLineItem.objects.create(
            order=self.po, part=self.supplier_part, quantity=5
        )
        line_pk = line.pk

        line.quantity = 10
        line.save()
        line.delete()

        entries = AuditLogEntry.objects.filter(
            parent_content_type=self.po.get_content_type(),
            parent_object_pk=str(self.po.pk),
        )

        self.assertEqual(entries.count(), 3)
        self.assertEqual(
            {e.action for e in entries},
            {
                AuditLogEntry.Action.CREATE,
                AuditLogEntry.Action.UPDATE,
                AuditLogEntry.Action.DELETE,
            },
        )

        for entry in entries:
            self.assertEqual(entry.object_pk, str(line_pk))
            self.assertEqual(entry.parent_model_type, 'order.purchaseorder')

    def test_masked_instance(self):
        """Row-level masking is applied before the entry is written."""
        with mock.patch.object(
            PurchaseOrder, 'is_audit_masked', lambda self: True, create=True
        ):
            self.po.description = 'top-secret-value'
            self.po.save()

        entry = self.entries_for(self.po, action=AuditLogEntry.Action.UPDATE).first()

        self.assertEqual(entry.changes_dict['description'], [MASKED_VALUE] * 2)
        self.assertIsNone(entry.serialized_data)

        # Ensure the raw value is not stored anywhere in the entry
        for field in ['changes', 'changes_text', 'additional_data', 'object_repr']:
            self.assertNotIn('top-secret-value', str(getattr(entry, field)))

    def test_audit_source(self):
        """Changes made outside of a request are tagged with their source."""
        with audit.context.audit_source('task:test_task'):
            cid = audit.context.get_cid()
            self.po.description = 'From task'
            self.po.save()

        entry = self.entries_for(self.po, action=AuditLogEntry.Action.UPDATE).first()

        self.assertIsNone(entry.actor)
        self.assertEqual(entry.additional_data, {'source': 'task:test_task'})
        self.assertIsNotNone(cid)
        self.assertEqual(entry.cid, cid)

        # Context is reset afterwards
        self.assertIsNone(audit.context.get_source())
        self.assertIsNone(audit.context.get_cid())

    def test_batch_cid(self):
        """The correlation ID is resolved once for an audit batch."""
        with audit.context.audit_source('task:test_task'):
            cid = audit.context.get_cid()

            with (
                mock.patch.object(
                    audit.context, 'resolve_cid', wraps=audit.context.resolve_cid
                ) as resolve,
                transaction.atomic(),
                write_batched(),
            ):
                for idx in range(3):
                    self.po.description = f'Batched {idx}'
                    self.po.save()

            self.assertEqual(resolve.call_count, 1)

        entries = self.entries_for(self.po, action=AuditLogEntry.Action.UPDATE)

        self.assertEqual(entries.count(), 3)
        self.assertEqual({entry.cid for entry in entries}, {cid})

        # Context is reset afterwards
        self.assertIsNone(audit.context.get_cid())

    def test_disabled(self):
        """No entries are recorded when the audit log is disabled."""
        set_global_setting('AUDIT_LOG_ENABLED', False)
        self.addCleanup(set_global_setting, 'AUDIT_LOG_ENABLED', True)

        self.po.description = 'Not recorded'
        self.po.save()

        self.assertFalse(
            self.entries_for(self.po, action=AuditLogEntry.Action.UPDATE).exists()
        )

    def test_retention(self):
        """Old entries are removed by the scheduled task (only when enabled)."""
        old = timezone.now() - timedelta(days=100)

        AuditLogEntry.objects.update(timestamp=old)

        self.po.description = 'Recent'
        self.po.save()

        n = AuditLogEntry.objects.count()
        self.assertGreater(n, 1)

        # Disabled by default
        delete_old_audit_entries()
        self.assertEqual(AuditLogEntry.objects.count(), n)

        set_global_setting('AUDIT_LOG_DELETE_OLD_ENTRIES', True)
        set_global_setting('AUDIT_LOG_DELETE_DAYS', 30)
        set_global_setting('AUDIT_LOG_DELETE_KEEP_SUMMARY', False)
        self.addCleanup(set_global_setting, 'AUDIT_LOG_DELETE_OLD_ENTRIES', False)
        self.addCleanup(set_global_setting, 'AUDIT_LOG_DELETE_DAYS', 365)
        self.addCleanup(set_global_setting, 'AUDIT_LOG_DELETE_KEEP_SUMMARY', True)

        with mock.patch('audit.tasks.DELETE_BATCH_SIZE', 1):
            delete_old_audit_entries()

        # Only the recent entries remain (including the settings changes above)
        self.assertEqual(
            AuditLogEntry.objects.exclude(content_type=setting_content_type()).count(),
            1,
        )

    def test_retention_keep_summary(self):
        """With 'keep summary' enabled, the creation and latest entry of each object are kept."""
        # An object with multiple updates
        for description in ['First', 'Second', 'Third']:
            self.po.description = description
            self.po.save()

        # A deleted object
        line = PurchaseOrderLineItem.objects.create(
            order=self.po, part=self.supplier_part, quantity=5
        )
        line_pk = line.pk
        line.quantity = 10
        line.save()
        line.delete()

        # Everything is "old"
        AuditLogEntry.objects.update(timestamp=timezone.now() - timedelta(days=100))

        set_global_setting('AUDIT_LOG_DELETE_OLD_ENTRIES', True)
        set_global_setting('AUDIT_LOG_DELETE_DAYS', 30)
        self.addCleanup(set_global_setting, 'AUDIT_LOG_DELETE_OLD_ENTRIES', False)
        self.addCleanup(set_global_setting, 'AUDIT_LOG_DELETE_DAYS', 365)

        with mock.patch('audit.tasks.DELETE_BATCH_SIZE', 1):
            delete_old_audit_entries()

        po_entries = self.entries_for(self.po).order_by('pk')
        self.assertEqual(
            [e.action for e in po_entries],
            [AuditLogEntry.Action.CREATE, AuditLogEntry.Action.UPDATE],
        )
        self.assertEqual(po_entries.last().changes_dict['description'][1], 'Third')

        line_entries = AuditLogEntry.objects.filter(
            content_type=PurchaseOrderLineItem.get_content_type(),
            object_pk=str(line_pk),
        ).order_by('pk')
        self.assertEqual(
            [e.action for e in line_entries],
            [AuditLogEntry.Action.CREATE, AuditLogEntry.Action.DELETE],
        )


class AuditAPITest(AuditTestMixin, InvenTreeAPITestCase):
    """Tests for the audit log API endpoints."""

    roles = ['purchase_order.view', 'purchase_order.change']
    is_staff = True

    def list_url(self):
        """Return the list endpoint URL."""
        return reverse('api-audit-log-list')

    def po_history(self, expected_code=200, **params):
        """Return the audit history for the test purchase order."""
        params = {'model_type': 'order.purchaseorder', 'model_id': self.po.pk, **params}
        return self.get(self.list_url(), params, expected_code=expected_code).data

    def patch_po(self, description, **kwargs):
        """Edit the test purchase order via the API."""
        url = reverse('api-po-detail', kwargs={'pk': self.po.pk})
        self.patch(url, {'description': description}, **kwargs)

    def test_actor(self):
        """The authenticated user is recorded as the actor (session auth)."""
        self.patch_po('Session edit')

        entry = self.entries_for(self.po, action=AuditLogEntry.Action.UPDATE).first()

        self.assertEqual(entry.actor, self.user)
        self.assertEqual(entry.remote_addr, '127.0.0.1')
        self.assertIsNotNone(entry.cid)

        data = self.po_history()
        self.assertEqual(data[0]['actor'], self.user.pk)
        self.assertEqual(data[0]['actor_detail']['username'], self.user.username)
        self.assertEqual(data[0]['model_type'], 'order.purchaseorder')
        self.assertEqual(data[0]['model_label'], 'Purchase Order')
        self.assertEqual(data[0]['changes']['description'][1], 'Session edit')

    def test_correlation_id(self):
        """The correlation ID matches the request ID (as used by structlog)."""
        url = reverse('api-po-detail', kwargs={'pk': self.po.pk})

        # Request ID provided by the client / reverse proxy
        self.patch(url, {'description': 'One'}, HTTP_X_REQUEST_ID='req-abc-123')

        entry = self.entries_for(self.po, action=AuditLogEntry.Action.UPDATE).get()
        self.assertEqual(entry.cid, 'req-abc-123')

        # Otherwise a unique ID is generated per request
        self.patch(url, {'description': 'Two'})
        self.patch(url, {'description': 'Three'})

        cids = list(
            self
            .entries_for(self.po, action=AuditLogEntry.Action.UPDATE)
            .exclude(cid='req-abc-123')
            .values_list('cid', flat=True)
        )

        self.assertEqual(len(cids), 2)
        self.assertTrue(all(cids))
        self.assertNotEqual(cids[0], cids[1])

    def test_basic_auth_actor(self):
        """Users authenticated by DRF (not middleware) are recorded as the actor."""
        self.logout()

        auth = b64encode(f'{self.username}:{self.password}'.encode()).decode()
        self.client.credentials(HTTP_AUTHORIZATION=f'Basic {auth}')

        self.patch_po('Basic auth edit')

        entry = self.entries_for(self.po, action=AuditLogEntry.Action.UPDATE).first()
        self.assertEqual(entry.actor, self.user)

    def test_spoofed_remote_addr(self):
        """An invalid forwarded address does not break saving, and is not recorded."""
        self.patch_po('Spoofed', HTTP_X_FORWARDED_FOR='not-an-ip-address')

        entry = self.entries_for(self.po, action=AuditLogEntry.Action.UPDATE).first()
        self.assertIsNone(entry.remote_addr)

    def test_children(self):
        """The history of a parent includes child entries (unless excluded)."""
        line = PurchaseOrderLineItem.objects.create(
            order=self.po, part=self.supplier_part, quantity=5
        )
        line.delete()

        data = self.po_history()
        models = [entry['model_type'] for entry in data]

        self.assertIn('order.purchaseorderlineitem', models)
        self.assertEqual(models.count('order.purchaseorderlineitem'), 2)

        data = self.po_history(include_children=False)
        self.assertEqual(
            {entry['model_type'] for entry in data}, {'order.purchaseorder'}
        )

        # Short model names are also accepted
        data = self.get(self.list_url(), {'model_type': 'purchaseorderlineitem'}).data
        self.assertEqual(len(data), 2)

    def test_filter_validation(self):
        """Invalid filter combinations are rejected."""
        self.get(self.list_url(), {'model_id': 1}, expected_code=400)
        self.get(self.list_url(), {'model_type': 'not_a_model'}, expected_code=400)

    def test_read_only(self):
        """Audit entries cannot be modified via the API."""
        entry = self.entries_for(self.po).first()
        url = reverse('api-audit-log-detail', kwargs={'pk': entry.pk})

        self.get(url)
        self.patch(url, {'object_repr': 'x'}, expected_code=405)
        self.delete(url, expected_code=405)
        self.post(self.list_url(), {}, expected_code=405)

    def test_permissions(self):
        """Entries are only visible with 'view' permission on the audited model."""
        entry = self.entries_for(self.po).first()
        detail_url = reverse('api-audit-log-detail', kwargs={'pk': entry.pk})

        self.assertGreater(len(self.po_history()), 0)

        # Remove all roles
        self.clearRoles()

        self.assertEqual(len(self.po_history()), 0)
        self.assertEqual(len(self.get(self.list_url()).data), 0)
        self.get(detail_url, expected_code=404)

    def test_child_without_parent_permission(self):
        """Child entries without 'view' permission on the parent model.

        - The child entry itself is still visible (permission on the child model)
        - It is *not* returned when querying the history of the parent
        - The parent reference is removed from the response
        """
        PurchaseOrderLineItem.objects.create(
            order=self.po, part=self.supplier_part, quantity=5
        )

        def line_entries(params=None):
            return [
                e
                for e in self.get(self.list_url(), params or {}).data
                if e['model_type'] == 'order.purchaseorderlineitem'
            ]

        [entry] = line_entries()
        self.assertEqual(entry['parent_model_type'], 'order.purchaseorder')
        self.assertEqual(entry['parent_object_pk'], str(self.po.pk))
        self.assertEqual(len(line_entries({'model_type': 'purchaseorder'})), 1)

        # Line item visible, but parent (order) not
        def can_view(user, model, groups=None):
            return model is not PurchaseOrder

        with (
            mock.patch('audit.api.user_can_view_audit_model', can_view),
            mock.patch('audit.permissions.user_can_view_audit_model', can_view),
        ):
            [entry] = line_entries()
            self.assertIsNone(entry['parent_model_type'])
            self.assertIsNone(entry['parent_object_pk'])

            # Not available when querying through the parent
            self.assertEqual(
                line_entries({'model_type': 'purchaseorder', 'model_id': self.po.pk}),
                [],
            )
            self.assertEqual(line_entries({'model_type': 'purchaseorder'}), [])

            # Still available when querying the child model directly
            self.assertEqual(
                len(line_entries({'model_type': 'purchaseorderlineitem'})), 1
            )

    def test_non_staff(self):
        """Non-staff users can view entries for models they have permission to view."""
        self.patch_po('Edit')

        entry = self.entries_for(self.po).first()
        detail_url = reverse('api-audit-log-detail', kwargs={'pk': entry.pk})

        # Staff users can see entries (including the remote address)
        data = self.po_history()
        self.assertEqual(data[0]['remote_addr'], '127.0.0.1')
        self.get(detail_url)

        self.user.is_staff = False
        self.user.save()

        # Non-staff users can view the entries - but not the remote address
        data = self.po_history()
        self.assertGreater(len(data), 0)
        self.assertNotIn('remote_addr', data[0])
        self.assertNotIn('remote_addr', self.get(detail_url).data)

        # ...but not without view permission on the audited model
        self.clearRoles()

        self.assertEqual(self.po_history(), [])
        self.get(detail_url, expected_code=404)

        # Anonymous users are denied
        self.client.logout()
        self.get(self.list_url(), expected_code=401)

    def test_view_restriction(self):
        """Models with a view restriction are hidden from users without that status."""
        self.assertGreater(len(self.po_history()), 0)

        with mock.patch.object(
            PurchaseOrder, 'AUDIT_VIEW_RESTRICTION', 'superuser', create=True
        ):
            # Staff, but not superuser
            self.assertEqual(len(self.po_history(include_children=False)), 0)

            self.user.is_superuser = True
            self.user.save()

            self.assertGreater(len(self.po_history(include_children=False)), 0)

    def test_model_type_filter_options(self):
        """The model type filter choices are provided via the OPTIONS metadata."""
        response = self.options(self.list_url())

        filters = response.data['filters']

        # Model-backed filters (e.g. 'actor') are never exposed
        self.assertNotIn('actor', filters)

        choices = {
            c['value']: c['display_name'] for c in filters['model_type']['choices']
        }

        self.assertEqual(choices['order.purchaseorder'], 'Purchase Order')
        self.assertIn('order.purchaseorderlineitem', choices)

        # Only models which the user can view are provided
        self.assertNotIn('part.part', choices)
        self.assertNotIn('build.build', choices)

        # The chosen value filters the entries
        data = self.get(self.list_url(), {'model_type': 'order.purchaseorder'}).data
        self.assertGreater(len(data), 0)

        for entry in data:
            self.assertEqual(entry['model_type'], 'order.purchaseorder')

    def test_superuser(self):
        """Superusers can view all entries."""
        self.clearRoles()
        self.assertEqual(len(self.po_history()), 0)

        get_user_model().objects.filter(pk=self.user.pk).update(is_superuser=True)

        self.assertGreater(len(self.po_history()), 0)

    def get_change_rows(self, field_name: str) -> list:
        """Return the 'changes_detail' rows for the given field, across the PO history."""
        data = self.po_history(
            changes_detail=True,
            include_children=False,
            action=AuditLogEntry.Action.UPDATE,
        )

        return [
            row
            for entry in data
            for row in entry['changes_detail']
            if row['field'] == field_name
        ]

    def test_changes_detail_fk(self):
        """Foreign key changes are resolved for display, if the related model can be viewed."""
        old_supplier = self.supplier
        new_supplier = Company.objects.create(name='Other Supplier', is_supplier=True)

        self.po.supplier = new_supplier
        self.po.save()

        [row] = self.get_change_rows('supplier')

        self.assertEqual(row['type'], 'fk')
        self.assertEqual(row['model_type'], 'company.company')
        self.assertEqual(row['old'], old_supplier.pk)
        self.assertEqual(row['new'], new_supplier.pk)
        self.assertEqual(row['old_display'], str(old_supplier))
        self.assertEqual(row['new_display'], str(new_supplier))

        # Deleted related objects are marked as such
        new_supplier.delete()
        [row] = self.get_change_rows('supplier')
        self.assertEqual(row['new_display'], 'Deleted')

        # Without permission on the related model, only the PK is returned
        with mock.patch.object(
            AuditLogEntrySerializer,
            'can_view_model',
            lambda self, model: model is PurchaseOrder,
        ):
            [row] = self.get_change_rows('supplier')

        self.assertEqual(row['old'], old_supplier.pk)
        self.assertIsNone(row['old_display'])
        self.assertIsNone(row['new_display'])

    def test_changes_detail_value(self):
        """Plain value changes include the field label."""
        self.po.description = 'New description'
        self.po.save()

        [row] = self.get_change_rows('description')

        self.assertEqual(row['type'], 'value')
        self.assertEqual(row['label'], 'Description')
        self.assertFalse(row['numeric'])

        # Primary key and automatically updated fields are not shown
        data = self.po_history(changes_detail=True, include_children=False)
        fields = {row['field'] for entry in data for row in entry['changes_detail']}

        self.assertNotIn('id', fields)
        self.assertNotIn('updated_at', fields)
        self.assertEqual(row['old'], 'Original')
        self.assertEqual(row['new'], 'New description')

    def test_m2m_objects_hidden(self):
        """M2M object names are removed if the related model cannot be viewed."""
        AuditLogEntry.objects.create(
            content_type=self.po.get_content_type(),
            object_pk=str(self.po.pk),
            object_repr=str(self.po),
            action=AuditLogEntry.Action.UPDATE,
            changes={
                'tags': {'type': 'm2m', 'operation': 'add', 'objects': ['hidden-tag']}
            },
        )

        with mock.patch.object(
            AuditLogEntrySerializer,
            'can_view_model',
            lambda self, model: model is PurchaseOrder,
        ):
            response = self.get(
                self.list_url(),
                {
                    'model_type': 'order.purchaseorder',
                    'model_id': self.po.pk,
                    'changes_detail': True,
                },
            )

        self.assertNotIn('hidden-tag', str(response.content))

        with mock.patch.object(
            AuditLogEntrySerializer, 'can_view_model', lambda self, model: True
        ):
            [row] = self.get_change_rows('tags')

        self.assertEqual(row['type'], 'm2m')
        self.assertEqual(row['operation'], 'add')
        self.assertEqual(row['objects'], ['hidden-tag'])

    def test_stale_model(self):
        """Entries for models which no longer exist can still be serialized."""
        get_user_model().objects.filter(pk=self.user.pk).update(is_superuser=True)

        ct = ContentType.objects.create(app_label='removed_app', model='removedmodel')

        AuditLogEntry.objects.create(
            content_type=ct,
            object_pk='1',
            object_repr='Removed object',
            action=AuditLogEntry.Action.UPDATE,
            changes={'name': ['a', 'b']},
        )

        data = self.get(
            self.list_url(), {'model_type': ct.pk, 'changes_detail': True}
        ).data

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['changes_detail'][0]['label'], 'Name')
        self.assertEqual(data[0]['changes_detail'][0]['new'], 'b')


class AuditMiddlewareConfigTest(TestCase):
    """Tests for ensuring the audit middleware is always configured."""

    AUDIT = 'audit.middleware.InvenTreeAuditlogMiddleware'
    STRUCTLOG = 'django_structlog.middlewares.RequestMiddleware'

    def test_installed(self):
        """The audit middleware is present in the active configuration."""
        from django.conf import settings

        self.assertIn(self.AUDIT, settings.MIDDLEWARE)

        # Placed after the structlog middleware (shares the request ID)
        self.assertGreater(
            settings.MIDDLEWARE.index(self.AUDIT),
            settings.MIDDLEWARE.index(self.STRUCTLOG),
        )

    def test_ensure_middleware(self):
        """Missing middleware is added (after the specified middleware, if present)."""
        from InvenTree.config import ensure_middleware

        # Already present - unchanged
        middleware = ['a', self.AUDIT, 'b']
        self.assertEqual(ensure_middleware(middleware, self.AUDIT), middleware)

        # Missing - inserted after the specified middleware (with a warning)
        with self.assertLogs('inventree', level='WARNING') as logs:
            result = ensure_middleware(
                ['a', self.STRUCTLOG, 'b'], self.AUDIT, after=self.STRUCTLOG
            )

        self.assertEqual(result, ['a', self.STRUCTLOG, self.AUDIT, 'b'])
        self.assertIn('INVE-W17', logs.output[0])

        # Missing (and the 'after' middleware is not present) - appended
        with self.assertLogs('inventree', level='WARNING'):
            result = ensure_middleware(['a', 'b'], self.AUDIT, after=self.STRUCTLOG)

        self.assertEqual(result, ['a', 'b', self.AUDIT])


class AuditAdminTest(AuditTestMixin, InvenTreeAPITestCase):
    """Tests for the AuditLogEntry admin class."""

    superuser = True

    def test_admin_registration(self):
        """The custom admin class replaces the upstream one."""
        from django.contrib import admin

        from audit.admin import AuditLogEntryAdmin

        model_admin = admin.site._registry[AuditLogEntry]

        self.assertIsInstance(model_admin, AuditLogEntryAdmin)

        # Remains read-only
        self.assertFalse(model_admin.has_add_permission(None))
        self.assertFalse(model_admin.has_change_permission(None))

    @override_settings(
        SITE_URL='http://testserver', CSRF_TRUSTED_ORIGINS=['http://testserver']
    )
    def test_filter_by_user(self):
        """The admin changelist can be filtered by the user who made the change."""
        other = get_user_model().objects.create_user(username='other_user')

        with audit.context.audit_source('test'):
            from auditlog.context import set_actor

            with set_actor(self.user):
                self.po.description = 'By test user'
                self.po.save()

            with set_actor(other):
                self.po.description = 'By other user'
                self.po.save()

        url = reverse('admin:audit_auditlogentry_changelist')

        # The filter lists users with recorded entries
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'other_user')

        response = self.client.get(url, {'actor__id__exact': other.pk})
        self.assertEqual(response.status_code, 200)

        entries = list(response.context['cl'].result_list)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].actor, other)


def audit_task_helper(pk: int, description: str):
    """Background task used to test the audit source of task changes."""
    company = Company.objects.get(pk=pk)
    company.description = description
    company.save()


class AuditSourceTest(InvenTreeAPITestCase):
    """Tests for the context recorded against programmatic (non-request) changes."""

    roles = ['purchase_order.change']

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super().setUpTestData()

        cls.company = Company.objects.create(name='Source Company', is_supplier=True)

    def last_update(self):
        """Return the most recent UPDATE entry for the test company."""
        return (
            AuditLogEntry.objects
            .get_for_object(self.company)
            .filter(action=AuditLogEntry.Action.UPDATE)
            .order_by('pk')
            .last()
        )

    def test_programmatic_update(self):
        """A plain ORM change (no request, no task) is recorded without any request context."""
        self.company.description = 'Programmatic'
        self.company.save()

        entry = self.last_update()

        self.assertEqual(entry.changes_dict['description'], ['', 'Programmatic'])
        self.assertIsNone(entry.actor)
        self.assertIsNone(entry.remote_addr)
        self.assertIsNone(entry.additional_data)

    def test_programmatic_bulk_create(self):
        """Entries for a programmatic bulk create have no actor."""
        from audit.helpers import audited_bulk_create
        from common.models import Parameter, ParameterTemplate

        template = ParameterTemplate.objects.create(name='Source Template')

        [parameter] = audited_bulk_create(
            Parameter,
            [
                Parameter(
                    model_type=Part.get_content_type(),
                    model_id=Part.objects.create(name='P', description='P').pk,
                    template=template,
                    data='X',
                )
            ],
        )

        entry = AuditLogEntry.objects.get_for_object(parameter).get()

        self.assertEqual(entry.action, AuditLogEntry.Action.CREATE)
        self.assertIsNone(entry.actor)
        self.assertIsNone(entry.remote_addr)

    def test_actor_not_retained(self):
        """The actor of a request is not attributed to later programmatic changes."""
        self.patch(
            reverse('api-company-detail', kwargs={'pk': self.company.pk}),
            {'description': 'Via API'},
        )

        api_entry = self.last_update()
        self.assertEqual(api_entry.actor, self.user)

        self.company.refresh_from_db()
        self.company.description = 'Programmatic'
        self.company.save()

        entry = self.last_update()

        self.assertNotEqual(entry.pk, api_entry.pk)
        self.assertIsNone(entry.actor)
        self.assertIsNone(entry.remote_addr)
        self.assertNotEqual(entry.cid, api_entry.cid)

    def run_task(self, description: str, **kwargs):
        """Run the test task (synchronously) via offload_task."""
        from InvenTree.tasks import offload_task

        offload_task(
            'audit.tests.audit_task_helper',
            self.company.pk,
            description,
            force_sync=True,
            **kwargs,
        )

    def test_sync_task(self):
        """Changes made by a (synchronous) task are tagged with the task name."""
        self.run_task('From task')

        entry = self.last_update()

        self.assertEqual(entry.changes_dict['description'], ['', 'From task'])
        self.assertEqual(
            entry.additional_data, {'source': 'task:audit.tests.audit_task_helper'}
        )
        self.assertIsNone(entry.actor)
        self.assertIsNotNone(entry.cid)

        # Context is reset afterwards
        self.assertIsNone(audit.context.get_source())
        self.assertIsNone(audit.context.get_cid())

    def test_sync_task_in_request(self):
        """A task run synchronously within a request is attributed to the request."""
        request = mock.Mock(user=self.user)

        with audit.context.audit_request(request):
            self.run_task('From request')

        entry = self.last_update()

        self.assertEqual(entry.actor, self.user)
        self.assertIsNone(entry.additional_data)

    def test_worker_task(self):
        """Changes made by a task executed by the background worker are tagged with the task name."""
        from django_q.tasks import AsyncTask

        task = AsyncTask(
            'audit.tests.audit_task_helper', self.company.pk, 'From worker', sync=True
        )
        task.run()

        entry = self.last_update()

        self.assertEqual(entry.changes_dict['description'], ['', 'From worker'])
        self.assertEqual(
            entry.additional_data, {'source': 'task:audit.tests.audit_task_helper'}
        )
        self.assertIsNone(entry.actor)
        self.assertIsNotNone(entry.cid)

        # Context is reset afterwards
        self.assertIsNone(audit.context.get_source())
        self.assertIsNone(audit.context.get_cid())

    def test_worker_task_failure(self):
        """The audit context is reset even if a worker task fails."""
        from django_q.tasks import AsyncTask

        task = AsyncTask('audit.tests.audit_task_helper', -1, 'Missing', sync=True)

        with contextlib.suppress(Exception):
            task.run()

        self.assertIsNone(audit.context.get_source())
        self.assertIsNone(audit.context.get_cid())


class AuditDisabledTest(InvenTreeAPITestCase):
    """No audit entries are recorded (via any write path) when auditing is disabled.

    Each path is tested both with the AUDIT_LOG_ENABLED setting disabled,
    and within the django-auditlog disable_auditlog() context.
    """

    roles = ['part.add', 'part.change', 'part.view', 'purchase_order.change']

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        from common.models import ParameterTemplate

        super().setUpTestData()

        cls.company = Company.objects.create(name='Disabled Company', is_supplier=True)
        cls.part = Part.objects.create(name='Disabled Part', description='A part')
        cls.template = ParameterTemplate.objects.create(name='Disabled Template')

    @contextlib.contextmanager
    def setting_disabled(self):
        """Disable auditing via the global setting."""
        set_global_setting('AUDIT_LOG_ENABLED', False)

        try:
            yield
        finally:
            set_global_setting('AUDIT_LOG_ENABLED', True)

    def check_disabled(self, operation):
        """Check that the operation is recorded when enabled - and not when disabled."""
        from auditlog.context import disable_auditlog

        for name, context in [
            ('setting', self.setting_disabled),
            ('context', disable_auditlog),
        ]:
            with self.subTest(disabled_by=name):
                n = audited_entries().count()

                with context():
                    operation()

                self.assertEqual(audited_entries().count(), n)

        # Sanity check: the same operation *is* recorded when enabled
        n = audited_entries().count()
        operation()
        self.assertGreater(audited_entries().count(), n)

    def test_create_update_delete(self):
        """Model create / update / delete operations."""
        counter = iter(range(100))

        def create():
            Company.objects.create(name=f'New {next(counter)}')

        def update():
            self.company.description = f'Description {next(counter)}'
            self.company.save()

        def delete():
            Company.objects.create(name=f'Delete {next(counter)}').delete()

        for operation in [create, update, delete]:
            with self.subTest(operation=operation.__name__):
                self.check_disabled(operation)

    def test_child_model(self):
        """Changes to child models (linked to a parent)."""
        from company.models import Address

        counter = iter(range(100))

        self.check_disabled(
            lambda: Address.objects.create(
                company=self.company, title=f'Address {next(counter)}', line1='1'
            )
        )

    def test_expression_update(self):
        """Deferred (F() expression) updates."""
        from django.db.models import F

        from build.models import Build

        build = Build.objects.create(
            part=Part.objects.create(
                name='Assembly', description='An assembly', assembly=True
            ),
            reference='BO-9901',
            quantity=10,
        )

        def update():
            build.priority = F('priority') + 1
            build.save(update_fields=['priority'])
            build.refresh_from_db()

        self.check_disabled(update)

    def test_audited_update(self):
        """The audited_update() helper."""
        from audit.helpers import audited_update

        counter = iter(range(100))

        self.check_disabled(
            lambda: audited_update(
                Company.objects.filter(pk=self.company.pk),
                description=f'Update {next(counter)}',
            )
        )

    def test_audited_bulk_update(self):
        """The audited_bulk_update() helper."""
        from audit.helpers import audited_bulk_update

        counter = iter(range(100))

        def update():
            self.company.description = f'Bulk {next(counter)}'
            audited_bulk_update(Company, [self.company], ['description'])

        self.check_disabled(update)

    def test_audited_bulk_create(self):
        """The audited_bulk_create() helper."""
        from audit.helpers import audited_bulk_create
        from common.models import Parameter

        counter = iter(range(100))

        self.check_disabled(
            lambda: audited_bulk_create(
                Parameter,
                [
                    Parameter(
                        model_type=Part.get_content_type(),
                        model_id=Part.objects.create(
                            name=f'P{next(counter)}', description='P'
                        ).pk,
                        template=self.template,
                        data='X',
                    )
                ],
            )
        )

    def test_api(self):
        """API requests (including batched bulk creation)."""
        counter = iter(range(100))

        def update():
            self.patch(
                reverse('api-company-detail', kwargs={'pk': self.company.pk}),
                {'description': f'API {next(counter)}'},
            )

        def bulk_create():
            parts = [
                Part.objects.create(name=f'API {next(counter)}', description='P')
                for _ in range(2)
            ]

            self.post(
                reverse('api-parameter-list'),
                [
                    {
                        'model_type': 'part',
                        'model_id': part.pk,
                        'template': self.template.pk,
                        'data': 'Y',
                    }
                    for part in parts
                ],
                format='json',
            )

        for operation in [update, bulk_create]:
            with self.subTest(operation=operation.__name__):
                # Note: disable_auditlog() is not propagated to the request thread,
                # so only the global setting is tested here
                n = audited_entries().count()

                with self.setting_disabled():
                    operation()

                self.assertEqual(audited_entries().count(), n)

                operation()
                self.assertGreater(audited_entries().count(), n)


class AuditRetentionTest(InvenTreeAPITestCase):
    """Audit entries are retained when related objects are removed."""

    roles = ['purchase_order.change', 'purchase_order.view']

    def test_stale_parent_content_type(self):
        """Removing a stale (parent) content type does not delete child entries."""
        from django.core.management import call_command

        company = Company.objects.create(name='Child Company')
        entry = AuditLogEntry.objects.get_for_object(company).get()

        stale = ContentType.objects.create(app_label='removed_app', model='removed')

        entry.parent_content_type = stale
        entry.parent_object_pk = '1'
        entry.save()

        call_command(
            'remove_stale_contenttypes',
            '--include-stale-apps',
            '--no-input',
            verbosity=0,
        )

        self.assertFalse(ContentType.objects.filter(pk=stale.pk).exists())

        entry.refresh_from_db()
        self.assertIsNone(entry.parent_content_type)

    def test_deleted_user(self):
        """The username of the actor is retained if the user is deleted."""
        user = get_user_model().objects.create_user(
            username='leaver', password='password', is_staff=True
        )
        self.client.force_login(user)

        company = Company.objects.create(name='Edited Company', is_supplier=True)

        # Grant the user permission to edit the company
        for group in self.user.groups.all():
            user.groups.add(group)

        self.patch(
            reverse('api-company-detail', kwargs={'pk': company.pk}),
            {'description': 'Edited by leaver'},
        )

        entry = (
            AuditLogEntry.objects
            .get_for_object(company)
            .filter(action=AuditLogEntry.Action.UPDATE)
            .get()
        )

        self.assertEqual(entry.actor, user)
        self.assertEqual(entry.actor_username, 'leaver')

        user.delete()
        entry.refresh_from_db()

        self.assertIsNone(entry.actor)
        self.assertEqual(entry.actor_username, 'leaver')

        # The username is provided via the API
        self.client.force_login(self.user)
        url = reverse('api-audit-log-detail', kwargs={'pk': entry.pk})

        data = self.get(url).data
        self.assertIsNone(data['actor'])
        self.assertEqual(data['actor_username'], 'leaver')


class AuditTestEvents(models.IntegerChoices):
    """Event types used for testing named audit events."""

    MOVED = 10, 'Moved'
    COUNTED = 20, 'Counted'


class AuditEventTest(InvenTreeAPITestCase):
    """Tests for named audit events (see audit.helpers.audit_event)."""

    roles = ['purchase_order.view', 'purchase_order.change']

    @classmethod
    def setUpClass(cls):
        """Define event types for the Company model."""
        cls.events_patch = mock.patch.object(
            Company, 'AUDIT_EVENT_TYPES', AuditTestEvents
        )
        cls.events_patch.start()

        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        """Remove event types from the Company model."""
        super().tearDownClass()
        cls.events_patch.stop()

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super().setUpTestData()

        cls.company = Company.objects.create(name='Event Company', is_supplier=True)
        cls.part = Part.objects.create(name='Event Part', description='A part')

    def entries(self):
        """Return all entries for the test company (oldest first)."""
        return AuditLogEntry.objects.get_for_object(self.company).order_by('pk')

    def test_event_with_changes(self):
        """The event is attached to the entry recorded when the instance is saved."""
        from audit.helpers import audit_event

        n = self.entries().count()

        with audit_event(
            self.company,
            AuditTestEvents.MOVED,
            notes='Moved company',
            deltas={'part': self.part, 'quantity': Decimal('1.5')},
        ):
            self.company.description = 'Moved'
            self.company.save()

        # A single entry, which records both the changes and the event
        self.assertEqual(self.entries().count(), n + 1)

        entry = self.entries().last()

        self.assertEqual(entry.event_type, AuditTestEvents.MOVED)
        self.assertEqual(entry.event_label, 'Moved')
        self.assertEqual(entry.notes, 'Moved company')
        self.assertEqual(entry.changes_dict['description'], ['', 'Moved'])
        self.assertEqual(
            entry.additional_data['deltas'],
            {
                'part': {
                    'model_type': 'part.part',
                    'pk': self.part.pk,
                    'str': str(self.part),
                },
                'quantity': 1.5,
            },
        )

    def test_event_without_changes(self):
        """An event is recorded even if no fields are changed."""
        from audit.helpers import audit_event, log_event

        n = self.entries().count()

        # Saved, but not changed
        with audit_event(self.company, AuditTestEvents.COUNTED, notes='Counted'):
            self.company.save()

        # Not saved at all
        log_event(self.company, AuditTestEvents.COUNTED, deltas={'quantity': 5})

        entries = list(self.entries()[n:])

        self.assertEqual(len(entries), 2)

        for entry in entries:
            self.assertEqual(entry.action, AuditLogEntry.Action.UPDATE)
            self.assertEqual(entry.event_type, AuditTestEvents.COUNTED)
            self.assertEqual(entry.changes_dict, {})

        self.assertEqual(entries[0].notes, 'Counted')
        self.assertEqual(entries[1].additional_data['deltas'], {'quantity': 5})

    def test_unnamed_event(self):
        """Notes (without an event type) are attached to an entry - but do not create one."""
        from audit.helpers import audit_event

        n = self.entries().count()

        # No changes - no entry
        with audit_event(self.company, None, notes='Nothing changed'):
            self.company.save()

        self.assertEqual(self.entries().count(), n)

        with audit_event(self.company, None, notes='Changed'):
            self.company.description = 'Unnamed'
            self.company.save()

        [entry] = list(self.entries()[n:])

        self.assertIsNone(entry.event_type)
        self.assertIsNone(entry.event_label)
        self.assertEqual(entry.notes, 'Changed')

    def test_no_changes_without_event(self):
        """Saving an instance without changes (and without an event) is not recorded."""
        n = self.entries().count()
        self.company.save()
        self.assertEqual(self.entries().count(), n)

    def test_multiple_instances(self):
        """Events can be recorded against multiple instances (one entry each)."""
        from audit.helpers import audit_event

        other = Company.objects.create(name='Other Company')

        with (
            audit_event(self.company, AuditTestEvents.MOVED, deltas={'to': other}),
            audit_event(other, AuditTestEvents.COUNTED, deltas={'from': self.company}),
        ):
            self.company.description = 'A'
            self.company.save()

        entry = self.entries().last()
        self.assertEqual(entry.event_type, AuditTestEvents.MOVED)
        self.assertEqual(entry.additional_data['deltas']['to']['pk'], other.pk)

        # The other instance was not saved - so an entry is created for the event
        other_entry = AuditLogEntry.objects.get_for_object(other).order_by('pk').last()
        self.assertEqual(other_entry.event_type, AuditTestEvents.COUNTED)
        self.assertEqual(other_entry.changes_dict, {})

    def test_nested_events_same_instance(self):
        """Nested events for the same (unsaved) instance each create an entry."""
        from contextlib import ExitStack

        from audit.helpers import audit_event

        n = self.entries().count()

        # Contexts exit in reverse order (newest event first)
        with ExitStack() as stack:
            for quantity in [1, 2]:
                stack.enter_context(
                    audit_event(
                        self.company,
                        AuditTestEvents.COUNTED,
                        deltas={'quantity': quantity},
                    )
                )

        entries = list(self.entries()[n:])

        self.assertEqual(len(entries), 2)
        self.assertEqual(
            sorted(entry.additional_data['deltas']['quantity'] for entry in entries),
            [1, 2],
        )

    def test_new_instance(self):
        """An event can be attached to the creation of a new instance."""
        from audit.helpers import audit_event

        company = Company(name='New Company')

        with audit_event(company, AuditTestEvents.MOVED, notes='Created'):
            company.save()

        [entry] = AuditLogEntry.objects.get_for_object(company)

        self.assertEqual(entry.action, AuditLogEntry.Action.CREATE)
        self.assertEqual(entry.event_type, AuditTestEvents.MOVED)
        self.assertEqual(entry.notes, 'Created')

    def test_invalid_event_type(self):
        """Event types must be defined by the model."""
        from audit.helpers import log_event

        with self.assertRaises(ValueError):
            log_event(self.company, 999)

        with self.assertRaises(ValueError):
            log_event(self.company, None)

        # Models without event types
        with self.assertRaises(ValueError):
            log_event(self.part, AuditTestEvents.MOVED)

    def test_error_not_recorded(self):
        """No event entry is created if an error occurs within the context."""
        from audit.helpers import audit_event

        n = self.entries().count()

        with (
            self.assertRaises(RuntimeError),
            audit_event(self.company, AuditTestEvents.MOVED),
        ):
            raise RuntimeError('Failed')

        self.assertEqual(self.entries().count(), n)

    def test_disabled(self):
        """Events are not recorded when auditing is disabled."""
        from auditlog.context import disable_auditlog

        from audit.helpers import log_event

        n = self.entries().count()

        with disable_auditlog():
            log_event(self.company, AuditTestEvents.MOVED)

        set_global_setting('AUDIT_LOG_ENABLED', False)
        self.addCleanup(set_global_setting, 'AUDIT_LOG_ENABLED', True)

        log_event(self.company, AuditTestEvents.MOVED)

        self.assertEqual(self.entries().count(), n)

    def test_batched(self):
        """Event entries can be written in a batch."""
        from django.db import transaction

        from audit.helpers import log_event, write_batched

        n = self.entries().count()

        with transaction.atomic(), write_batched():
            log_event(self.company, AuditTestEvents.MOVED)
            log_event(self.company, AuditTestEvents.COUNTED)

            # Not written until the batch is complete
            self.assertEqual(self.entries().count(), n)

        self.assertEqual(
            [entry.event_type for entry in self.entries()[n:]],
            [AuditTestEvents.MOVED, AuditTestEvents.COUNTED],
        )

    def test_api(self):
        """Event information is provided via the API (with redacted references)."""
        from audit.helpers import log_event

        log_event(
            self.company,
            AuditTestEvents.MOVED,
            notes='Via API',
            deltas={'part': self.part, 'quantity': 3},
        )

        entry = self.entries().last()
        url = reverse('api-audit-log-list')

        # Filter by event type
        data = self.get(url, {'event_type': AuditTestEvents.MOVED}).data
        self.assertEqual([item['pk'] for item in data], [entry.pk])
        self.assertEqual(
            self.get(url, {'event_type': AuditTestEvents.COUNTED}).data, []
        )

        [item] = data

        self.assertEqual(item['event_type'], AuditTestEvents.MOVED)
        self.assertEqual(item['event_label'], 'Moved')
        self.assertEqual(item['notes'], 'Via API')
        self.assertEqual(item['deltas']['quantity'], 3)

        # Deltas are only provided via the 'deltas' field
        self.assertIsNone(item['additional_data'])

        # The user cannot view parts - the reference is redacted
        self.assertEqual(
            item['deltas']['part'], {'model_type': 'part.part', 'pk': None, 'str': None}
        )

        self.assignRole('part.view')

        item = self.get(url, {'event_type': AuditTestEvents.MOVED}).data[0]
        self.assertEqual(item['deltas']['part']['pk'], self.part.pk)
        self.assertEqual(item['deltas']['part']['str'], str(self.part))
