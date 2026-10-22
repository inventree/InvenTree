"""Audit log tests for the Part and PartCategory models."""

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from audit.models import AuditLogEntry
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part, PartCategory

ACTION = AuditLogEntry.Action


class PartAuditTest(InvenTreeAPITestCase):
    """Audit tests for Part and PartCategory objects."""

    roles = [
        'part.view',
        'part.add',
        'part.change',
        'part.delete',
        'part_category.view',
        'part_category.add',
        'part_category.change',
        'part_category.delete',
    ]

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super().setUpTestData()

        cls.top = PartCategory.objects.create(name='Electronics')
        cls.category = PartCategory.objects.create(name='Resistors', parent=cls.top)
        cls.part = Part.objects.create(
            name='R_10K', description='10k resistor', category=cls.category
        )

    def entries(self, model, pk, **filters):
        """Return audit entries for a given object (by PK - which survives deletion)."""
        return AuditLogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(model),
            object_pk=str(pk),
            **filters,
        )

    def history(self, model_type: str, pk, **params):
        """Return the audit history for an object (including child entries)."""
        return self.get(
            reverse('api-audit-log-list'),
            {'model_type': model_type, 'model_id': pk, **params},
        ).data

    def test_part_create(self):
        """Creating a part is recorded."""
        entry = self.entries(Part, self.part.pk, action=ACTION.CREATE).get()

        self.assertEqual(entry.changes_dict['name'], [None, 'R_10K'])
        self.assertEqual(entry.object_repr, str(self.part))

        # Derived / tree fields are not recorded
        for field in ['bom_checksum', 'barcode_hash', 'lft', 'rght', 'tree_id']:
            self.assertNotIn(field, entry.changes_dict)

    def test_part_edit(self):
        """Part edits via the API are recorded against the user."""
        self.patch(
            reverse('api-part-detail', kwargs={'pk': self.part.pk}),
            {'description': '10k resistor, 1%', 'IPN': 'RES-10K', 'active': False},
        )

        entry = self.entries(Part, self.part.pk, action=ACTION.UPDATE).get()

        self.assertEqual(entry.actor, self.user)
        self.assertEqual(
            entry.changes_dict['description'], ['10k resistor', '10k resistor, 1%']
        )
        self.assertEqual(entry.changes_dict['IPN'], [None, 'RES-10K'])
        self.assertEqual(entry.changes_dict['active'], [True, False])

    def test_bom_validation(self):
        """Validating the BOM is recorded - without the (derived) checksum."""
        self.part.assembly = True
        self.part.save()

        self.part.validate_bom(self.user)

        # Note: entries are ordered by timestamp (newest first) by default
        entry = (
            self.entries(Part, self.part.pk, action=ACTION.UPDATE).order_by('pk').last()
        )

        self.assertEqual(entry.changes_dict['bom_validated'], [False, True])
        self.assertEqual(entry.changes_dict['bom_checked_by'], [None, self.user.pk])
        self.assertIn('bom_checked_date', entry.changes_dict)
        self.assertNotIn('bom_checksum', entry.changes_dict)

    def test_part_history_includes_parameters(self):
        """Parameters (already audited) are shown in the part history."""
        from common.models import Parameter, ParameterTemplate

        template = ParameterTemplate.objects.create(name='Resistance', units='ohm')

        Parameter.objects.create(
            model_type=Part.get_content_type(),
            model_id=self.part.pk,
            template=template,
            data='10000',
        )

        model_types = {e['model_type'] for e in self.history('part.part', self.part.pk)}

        self.assertIn('part.part', model_types)
        self.assertIn('common.parameter', model_types)

    def test_category_edit(self):
        """Category edits are recorded - without the (derived) pathstring."""
        child = PartCategory.objects.create(name='SMD', parent=self.category)

        self.patch(
            reverse('api-part-category-detail', kwargs={'pk': self.category.pk}),
            {'name': 'Resistor', 'description': 'All resistors'},
        )

        entry = self.entries(PartCategory, self.category.pk, action=ACTION.UPDATE).get()

        self.assertEqual(entry.actor, self.user)
        self.assertEqual(entry.changes_dict['name'], ['Resistors', 'Resistor'])
        self.assertNotIn('pathstring', entry.changes_dict)

        # The pathstring of the child category is updated (in bulk) - but not recorded
        child.refresh_from_db()
        self.assertEqual(child.pathstring, 'Electronics/Resistor/SMD')
        self.assertFalse(
            self.entries(PartCategory, child.pk, action=ACTION.UPDATE).exists()
        )

    def test_category_delete(self):
        """Deleting a category re-parents its parts and subcategories - and is recorded."""
        child = PartCategory.objects.create(name='SMD', parent=self.category)
        category_pk = self.category.pk

        self.category.delete()

        self.assertEqual(
            self.entries(PartCategory, category_pk, action=ACTION.DELETE).count(), 1
        )

        # The part is moved to the parent category
        part_entry = self.entries(Part, self.part.pk, action=ACTION.UPDATE).get()
        self.assertEqual(
            part_entry.changes_dict['category'], [category_pk, self.top.pk]
        )

        # The subcategory is moved to the parent category
        child_entry = self.entries(PartCategory, child.pk, action=ACTION.UPDATE).get()
        self.assertEqual(child_entry.changes_dict['parent'], [category_pk, self.top.pk])

    def test_category_history(self):
        """The category history is available via the API."""
        history = self.history('part.partcategory', self.category.pk)

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['action'], ACTION.CREATE)
        self.assertEqual(history[0]['model_label'], 'Part Category')
