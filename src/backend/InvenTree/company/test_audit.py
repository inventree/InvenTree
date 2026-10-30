"""Audit log tests for the Company, Contact and Address models."""

from django.db.models import F
from django.urls import reverse

from auditlog.context import disable_auditlog

from audit.helpers import audited_update
from audit.models import AuditLogEntry
from common.settings import set_global_setting
from company.models import (
    Address,
    Company,
    Contact,
    ManufacturerPart,
    SupplierPart,
    SupplierPriceBreak,
)
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part

ACTION = AuditLogEntry.Action


class CompanyAuditTest(InvenTreeAPITestCase):
    """Tests for audit history of Company / Contact / Address models."""

    roles = [
        'purchase_order.view',
        'purchase_order.add',
        'purchase_order.change',
        'purchase_order.delete',
    ]

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super().setUpTestData()

        cls.company = Company.objects.create(
            name='Acme Widgets', description='Widget supplier', is_supplier=True
        )

    def history(self, company=None, **params):
        """Return the audit history for a company (including contacts / addresses)."""
        company = company or self.company

        return self.get(
            reverse('api-audit-log-list'),
            {'model_type': 'company.company', 'model_id': company.pk, **params},
        ).data

    def entries(self, instance, **filters):
        """Return audit entries recorded directly against an instance."""
        return AuditLogEntry.objects.get_for_object(instance).filter(**filters)

    def test_company_edit(self):
        """Company edits via the API are recorded against the user."""
        self.patch(
            reverse('api-company-detail', kwargs={'pk': self.company.pk}),
            {'description': 'Widgets and gadgets', 'is_customer': True},
        )

        entry = self.entries(self.company, action=ACTION.UPDATE).get()

        self.assertEqual(entry.actor, self.user)
        self.assertEqual(
            entry.changes_dict['description'],
            ['Widget supplier', 'Widgets and gadgets'],
        )
        self.assertEqual(entry.changes_dict['is_customer'], [False, True])
        self.assertNotIn('metadata', entry.changes_dict)

        # Reverse relations are not recorded on creation
        created = self.entries(self.company, action=ACTION.CREATE).get()

        self.assertEqual(created.changes_dict['name'], [None, 'Acme Widgets'])

        for field in ['contacts', 'addresses', 'supplied_parts']:
            self.assertNotIn(field, created.changes_dict)

    def test_contact_history(self):
        """Contact changes are included in the company history."""
        url = reverse('api-contact-list')

        response = self.post(url, {'company': self.company.pk, 'name': 'Jane Doe'})
        contact = Contact.objects.get(pk=response.data['pk'])

        self.patch(
            reverse('api-contact-detail', kwargs={'pk': contact.pk}),
            {'role': 'Purchasing'},
        )
        self.delete(reverse('api-contact-detail', kwargs={'pk': contact.pk}))

        entries = [e for e in self.history() if e['model_type'] == 'company.contact']

        self.assertEqual(
            sorted(e['action'] for e in entries),
            [ACTION.CREATE, ACTION.UPDATE, ACTION.DELETE],
        )

        for entry in entries:
            self.assertEqual(entry['parent_model_type'], 'company.company')
            self.assertEqual(entry['parent_object_pk'], str(self.company.pk))
            self.assertEqual(entry['actor'], self.user.pk)

        # The contact history is not included when child entries are excluded
        self.assertFalse(
            any(
                e['model_type'] == 'company.contact'
                for e in self.history(include_children=False)
            )
        )

    def test_primary_address(self):
        """Demoting the previous primary address (a bulk update) is recorded."""
        url = reverse('api-address-list')

        first = self.post(
            url, {'company': self.company.pk, 'title': 'Head Office', 'line1': 'A'}
        ).data
        self.assertTrue(first['primary'])

        self.post(
            url,
            {
                'company': self.company.pk,
                'title': 'Warehouse',
                'line1': 'B',
                'primary': True,
            },
        )

        first = Address.objects.get(pk=first['pk'])
        self.assertFalse(first.primary)

        entry = self.entries(first, action=ACTION.UPDATE).get()

        self.assertEqual(entry.changes_dict, {'primary': [True, False]})
        self.assertEqual(entry.actor, self.user)
        self.assertEqual(entry.parent_object_pk, str(self.company.pk))
        self.assertIsNotNone(entry.cid)

    def test_company_delete(self):
        """Deleting a company records the cascaded contact / address deletions."""
        company = Company.objects.create(name='Short Lived Ltd')
        contact = Contact.objects.create(company=company, name='John Smith')
        address = Address.objects.create(company=company, title='HQ', line1='X')

        # Note: delete() clears the PK of the deleted instance
        targets = [(type(obj), str(obj.pk)) for obj in [company, contact, address]]
        company_pk = company.pk

        company.delete()

        for model, pk in targets:
            self.assertEqual(
                AuditLogEntry.objects.filter(
                    content_type=model.get_content_type(),
                    object_pk=pk,
                    action=ACTION.DELETE,
                ).count(),
                1,
            )

        # History of the deleted company is still available
        actions = [
            (e['model_type'], e['action'])
            for e in self.get(
                reverse('api-audit-log-list'),
                {'model_type': 'company.company', 'model_id': company_pk},
            ).data
        ]

        for model_type in ['company.company', 'company.contact', 'company.address']:
            self.assertIn((model_type, ACTION.CREATE), actions)
            self.assertIn((model_type, ACTION.DELETE), actions)


class AuditedUpdateTest(InvenTreeAPITestCase):
    """Tests for the audited_update helper."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super().setUpTestData()

        cls.companies = [
            Company.objects.create(name=f'Company {idx}', description='Original')
            for idx in range(3)
        ]

    def update_entries(self):
        """Return all UPDATE entries for Company objects."""
        return AuditLogEntry.objects.filter(
            content_type=Company.get_content_type(), action=ACTION.UPDATE
        )

    def test_update(self):
        """Each updated row gets an entry - matching the signal-based format."""
        n = audited_update(
            Company.objects.filter(pk__in=[c.pk for c in self.companies[:2]]),
            description='Bulk',
        )

        self.assertEqual(n, 2)
        self.assertEqual(self.update_entries().count(), 2)

        for entry in self.update_entries():
            self.assertEqual(entry.changes_dict, {'description': ['Original', 'Bulk']})

        # Compare with an entry generated by a regular save()
        company = self.companies[2]
        company.description = 'Bulk'
        company.save()

        entry = self.update_entries().get(object_pk=str(company.pk))
        self.assertEqual(entry.changes_dict, {'description': ['Original', 'Bulk']})

    def test_unchanged_rows(self):
        """Rows which are not actually modified do not produce entries."""
        n = audited_update(Company.objects.all(), description='Original')

        self.assertEqual(n, 3)
        self.assertEqual(self.update_entries().count(), 0)

    def test_filter_on_updated_field(self):
        """Updating the field the queryset is filtered on still records each row."""
        audited_update(
            Company.objects.filter(description='Original'), description='Changed'
        )

        self.assertEqual(self.update_entries().count(), 3)

    def test_expression(self):
        """F() expressions are supported (new values are re-read from the database)."""
        audited_update(Company.objects.all(), name=F('description'))

        for entry in self.update_entries():
            self.assertEqual(entry.changes_dict['name'][1], 'Original')

    def test_disabled(self):
        """No entries are created when auditing is disabled."""
        with disable_auditlog():
            n = audited_update(Company.objects.all(), description='A')

        self.assertEqual(n, 3)
        self.assertEqual(self.update_entries().count(), 0)

        set_global_setting('AUDIT_LOG_ENABLED', False)
        self.addCleanup(set_global_setting, 'AUDIT_LOG_ENABLED', True)

        audited_update(Company.objects.all(), description='B')

        self.assertEqual(self.update_entries().count(), 0)
        self.assertEqual(Company.objects.filter(description='B').count(), 3)

    def test_bulk_update(self):
        """audited_bulk_update() records an entry for each modified row."""
        from audit.helpers import audited_bulk_update

        a, b, c = self.companies

        a.description = 'Bulk A'
        b.description = 'Bulk B'
        # 'c' is included, but not modified

        n = audited_bulk_update(Company, [a, b, c], ['description'])

        self.assertEqual(n, 3)
        self.assertEqual(self.update_entries().count(), 2)

        for company in [a, b]:
            entry = self.update_entries().get(object_pk=str(company.pk))
            self.assertEqual(
                entry.changes_dict, {'description': ['Original', company.description]}
            )

    def test_bulk_update_expression(self):
        """audited_bulk_update() records the value written by an F() expression."""
        from audit.helpers import audited_bulk_update

        for company in self.companies:
            company.name = F('description')

        audited_bulk_update(Company, self.companies, ['name'])

        self.assertEqual(self.update_entries().count(), 3)

        for entry in self.update_entries():
            self.assertEqual(entry.changes_dict['name'][1], 'Original')

    def test_bulk_update_fields_only(self):
        """Only the fields passed to bulk_update() are recorded."""
        from audit.helpers import audited_bulk_update

        company = self.companies[0]
        company.description = 'Changed'
        company.website = 'https://example.com'

        audited_bulk_update(Company, [company], ['description'])

        entry = self.update_entries().get()
        self.assertEqual(list(entry.changes_dict.keys()), ['description'])

    def test_bulk_update_disabled(self):
        """No entries are recorded by audited_bulk_update() when auditing is disabled."""
        from audit.helpers import audited_bulk_update

        for company in self.companies:
            company.description = 'Quiet'

        with disable_auditlog():
            audited_bulk_update(Company, self.companies, ['description'])

        self.assertEqual(self.update_entries().count(), 0)
        self.assertEqual(Company.objects.filter(description='Quiet').count(), 3)

    def test_unaudited_model(self):
        """Models which are not audited fall back to a plain update."""
        from django.contrib.contenttypes.models import ContentType

        from audit.helpers import is_audited
        from stock.models import StockLocationType

        self.assertFalse(is_audited(StockLocationType))

        StockLocationType.objects.create(name='Type', description='x')

        n = audited_update(StockLocationType.objects.all(), description='y')

        self.assertEqual(n, 1)
        self.assertEqual(StockLocationType.objects.get().description, 'y')
        self.assertFalse(
            AuditLogEntry.objects.filter(
                content_type=ContentType.objects.get_for_model(StockLocationType)
            ).exists()
        )


class SupplierPartAuditTest(InvenTreeAPITestCase):
    """Tests for audit history of ManufacturerPart / SupplierPart / SupplierPriceBreak."""

    roles = [
        'part.view',
        'purchase_order.view',
        'purchase_order.add',
        'purchase_order.change',
        'purchase_order.delete',
    ]

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super().setUpTestData()

        cls.supplier = Company.objects.create(name='Supplier Co', is_supplier=True)
        cls.manufacturer = Company.objects.create(name='Maker Co', is_manufacturer=True)
        cls.part = Part.objects.create(
            name='Widget', description='A widget', purchaseable=True
        )
        cls.supplier_part = SupplierPart.objects.create(
            part=cls.part, supplier=cls.supplier, SKU='WID-001'
        )

    def entries(self, instance, **filters):
        """Return audit entries recorded directly against an instance."""
        return AuditLogEntry.objects.get_for_object(instance).filter(**filters)

    def history(self, model_type, pk, **params):
        """Return the audit history for an object (including children)."""
        return self.get(
            reverse('api-audit-log-list'),
            {'model_type': model_type, 'model_id': pk, **params},
        ).data

    def test_supplier_part_edit(self):
        """Supplier part edits are recorded, and shown in the supplier history."""
        self.patch(
            reverse('api-supplier-part-detail', kwargs={'pk': self.supplier_part.pk}),
            {'note': 'Preferred source', 'pack_quantity': '10'},
        )

        entry = self.entries(self.supplier_part, action=ACTION.UPDATE).get()

        self.assertEqual(entry.actor, self.user)
        self.assertEqual(entry.parent_object_pk, str(self.supplier.pk))
        self.assertEqual(entry.changes_dict['note'][1], 'Preferred source')
        self.assertEqual(entry.changes_dict['pack_quantity'][1], '10')

        # Derived field is not recorded
        self.assertNotIn('pack_quantity_native', entry.changes_dict)

        history = self.history('company.company', self.supplier.pk)
        self.assertIn(
            ('company.supplierpart', ACTION.UPDATE),
            [(e['model_type'], e['action']) for e in history],
        )

    def test_availability_not_recorded(self):
        """Supplier availability updates are not recorded."""
        self.supplier_part.update_available_quantity(250)

        self.assertFalse(
            self.entries(self.supplier_part, action=ACTION.UPDATE).exists()
        )

        # Other changes in the same save are still recorded
        self.supplier_part.note = 'Checked'
        self.supplier_part.update_available_quantity(300)

        entry = self.entries(self.supplier_part, action=ACTION.UPDATE).get()
        self.assertEqual(list(entry.changes_dict.keys()), ['note'])

    def test_primary_supplier_part(self):
        """Demoting the previous primary supplier part (a bulk update) is recorded."""
        self.assertTrue(self.supplier_part.primary)

        SupplierPart.objects.create(
            part=self.part, supplier=self.supplier, SKU='WID-002', primary=True
        )

        self.supplier_part.refresh_from_db()
        self.assertFalse(self.supplier_part.primary)

        entry = self.entries(self.supplier_part, action=ACTION.UPDATE).get()
        self.assertEqual(entry.changes_dict, {'primary': [True, False]})
        self.assertEqual(entry.parent_object_pk, str(self.supplier.pk))

    def test_manufacturer_part(self):
        """Manufacturer part changes are shown in the manufacturer history."""
        response = self.post(
            reverse('api-manufacturer-part-list'),
            {'part': self.part.pk, 'manufacturer': self.manufacturer.pk, 'MPN': 'M-1'},
        )

        mp = ManufacturerPart.objects.get(pk=response.data['pk'])

        self.patch(
            reverse('api-manufacturer-part-detail', kwargs={'pk': mp.pk}),
            {'description': 'Rev B'},
        )

        history = self.history('company.company', self.manufacturer.pk)
        entries = [e for e in history if e['model_type'] == 'company.manufacturerpart']

        self.assertEqual(
            sorted(e['action'] for e in entries), [ACTION.CREATE, ACTION.UPDATE]
        )

        for entry in entries:
            self.assertEqual(entry['parent_object_pk'], str(self.manufacturer.pk))
            self.assertEqual(entry['actor'], self.user.pk)

    def test_price_breaks(self):
        """Price break changes are shown in the supplier part history."""
        url = reverse('api-part-supplier-price-list')

        response = self.post(
            url,
            {
                'part': self.supplier_part.pk,
                'quantity': 10,
                'price': '1.50',
                'price_currency': 'USD',
            },
        )

        pb = SupplierPriceBreak.objects.get(pk=response.data['pk'])

        self.patch(
            reverse('api-part-supplier-price-detail', kwargs={'pk': pb.pk}),
            {'price': '1.25'},
        )

        entry = self.entries(pb, action=ACTION.UPDATE).get()
        self.assertIn('price', entry.changes_dict)
        self.assertEqual(entry.parent_object_pk, str(self.supplier_part.pk))

        history = self.history(
            'company.supplierpart', self.supplier_part.pk, changes_detail=True
        )
        entries = [
            e for e in history if e['model_type'] == 'company.supplierpricebreak'
        ]

        self.assertEqual(
            sorted(e['action'] for e in entries), [ACTION.CREATE, ACTION.UPDATE]
        )

        # Price breaks are not included in the supplier (company) history
        self.assertFalse(
            any(
                e['model_type'] == 'company.supplierpricebreak'
                for e in self.history('company.company', self.supplier.pk)
            )
        )

    def test_price_break_permission(self):
        """Price break history requires permission on the price break model."""
        SupplierPriceBreak.objects.create(part=self.supplier_part, quantity=1, price=2)

        def price_entries():
            return [
                e
                for e in self.history('company.supplierpart', self.supplier_part.pk)
                if e['model_type'] == 'company.supplierpricebreak'
            ]

        self.assertEqual(len(price_entries()), 1)

        # Supplier part is visible via the 'part' role, but companies / price breaks are not
        self.clearRoles()
        self.assignRole('part.view')

        history = self.history('company.supplierpart', self.supplier_part.pk)
        self.assertGreater(len(history), 0)
        self.assertEqual(len(price_entries()), 0)

        # Parent (supplier company) reference is hidden
        for entry in history:
            self.assertIsNone(entry['parent_model_type'])
            self.assertIsNone(entry['parent_object_pk'])

        # Supplier part entries cannot be retrieved via the supplier
        self.assertEqual(self.history('company.company', self.supplier.pk), [])
