"""Audit log tests for the Company, Contact and Address models."""

from django.db.models import F
from django.urls import reverse

from auditlog.context import disable_auditlog

from audit.helpers import audited_update
from audit.models import AuditLogEntry
from common.settings import set_global_setting
from company.models import Address, Company, Contact
from InvenTree.unit_test import InvenTreeAPITestCase

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

    def test_unaudited_model(self):
        """Models which are not audited fall back to a plain update."""
        from part.models import PartCategory

        PartCategory.objects.create(name='Cat', description='x')

        n = audited_update(PartCategory.objects.all(), description='y')

        self.assertEqual(n, 1)
        self.assertFalse(
            AuditLogEntry.objects.filter(
                content_type=PartCategory.get_content_type()
            ).exists()
        )
