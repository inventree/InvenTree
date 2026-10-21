"""Unit tests for the audit app.

No production models are audited yet, so these tests temporarily register
PurchaseOrder (parent) and PurchaseOrderLineItem (child) with the audit log.
"""

from base64 import b64encode
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from auditlog.registry import auditlog

import audit.context
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


class AuditTestMixin:
    """Temporarily register test models with the audit log."""

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

        for model in TEST_MODELS:
            register_model(model)

        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        """Unregister test models."""
        super().tearDownClass()

        for model in TEST_MODELS:
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
                'company.address',
                'company.company',
                'company.contact',
                'company.manufacturerpart',
                'company.supplierpart',
                'company.supplierpricebreak',
            ],
        )

        for model in audited_models():
            self.assertTrue(auditlog.contains(model))

        for model in TEST_MODELS:
            self.assertFalse(auditlog.contains(model))

    def test_register_model(self):
        """Registration applies the base excluded fields."""
        register_model(PurchaseOrder, exclude_fields=['notes'])

        try:
            self.assertTrue(auditlog.contains(PurchaseOrder))
            exclude = auditlog.get_model_fields(PurchaseOrder)['exclude_fields']

            for field in [*BASE_EXCLUDE_FIELDS, 'notes']:
                self.assertIn(field, exclude)
        finally:
            auditlog.unregister(PurchaseOrder)

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
        self.addCleanup(set_global_setting, 'AUDIT_LOG_DELETE_OLD_ENTRIES', False)
        self.addCleanup(set_global_setting, 'AUDIT_LOG_DELETE_DAYS', 365)

        with mock.patch('audit.tasks.DELETE_BATCH_SIZE', 1):
            delete_old_audit_entries()

        self.assertEqual(AuditLogEntry.objects.count(), 1)


class AuditAPITest(AuditTestMixin, InvenTreeAPITestCase):
    """Tests for the audit log API endpoints."""

    roles = ['purchase_order.view', 'purchase_order.change']
    is_staff = False

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

    def test_staff_only_fields(self):
        """Remote address is only exposed to staff users."""
        self.patch_po('Edit')

        data = self.po_history()
        self.assertNotIn('remote_addr', data[0])
        self.assertNotIn('remote_port', data[0])

        self.user.is_staff = True
        self.user.save()

        data = self.po_history()
        self.assertEqual(data[0]['remote_addr'], '127.0.0.1')

    def test_view_restriction(self):
        """Models with a view restriction are hidden from non-staff users."""
        self.assertGreater(len(self.po_history()), 0)

        with mock.patch.object(
            PurchaseOrder, 'AUDIT_VIEW_RESTRICTION', 'staff', create=True
        ):
            self.assertEqual(len(self.po_history(include_children=False)), 0)

            self.user.is_staff = True
            self.user.save()

            self.assertGreater(len(self.po_history(include_children=False)), 0)

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
