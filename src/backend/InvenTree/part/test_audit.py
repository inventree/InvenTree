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


class BomAuditTest(InvenTreeAPITestCase):
    """Audit tests for BomItem and BomItemSubstitute objects."""

    roles = [
        'part.view',
        'part.change',
        'bom.view',
        'bom.add',
        'bom.change',
        'bom.delete',
    ]

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super().setUpTestData()

        cls.assembly = Part.objects.create(
            name='Widget Assembly', description='An assembly', assembly=True
        )
        cls.resistor = Part.objects.create(
            name='R_10K', description='10k resistor', component=True
        )
        cls.alternative = Part.objects.create(
            name='R_10K_ALT', description='10k resistor (alt)', component=True
        )

    def entries(self, model, pk, **filters):
        """Return audit entries for a given object (by PK - which survives deletion)."""
        return AuditLogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(model),
            object_pk=str(pk),
            **filters,
        )

    def assembly_history(self, assembly=None):
        """Return the audit history for the assembly (including BOM changes)."""
        assembly = assembly or self.assembly

        return self.get(
            reverse('api-audit-log-list'),
            {'model_type': 'part.part', 'model_id': assembly.pk},
        ).data

    def test_bom_item(self):
        """BOM item changes via the API are recorded against the assembly."""
        from part.models import BomItem

        pk = self.post(
            reverse('api-bom-list'),
            {'part': self.assembly.pk, 'sub_part': self.resistor.pk, 'quantity': 4},
        ).data['pk']

        url = reverse('api-bom-item-detail', kwargs={'pk': pk})
        self.patch(url, {'quantity': 6, 'reference': 'R1-R6'})
        self.delete(url)

        entries = self.entries(BomItem, pk)

        self.assertEqual(
            sorted(entries.values_list('action', flat=True)),
            [ACTION.CREATE, ACTION.UPDATE, ACTION.DELETE],
        )

        for entry in entries:
            self.assertEqual(entry.actor, self.user)
            self.assertEqual(entry.parent_object_pk, str(self.assembly.pk))
            self.assertNotIn('checksum', entry.changes_dict)
            self.assertNotIn('validated', entry.changes_dict)
            self.assertNotIn(' object (', entry.object_repr)

        update = entries.get(action=ACTION.UPDATE)
        self.assertEqual(update.changes_dict['reference'], ['', 'R1-R6'])

        bom_actions = [
            e['action']
            for e in self.assembly_history()
            if e['model_type'] == 'part.bomitem'
        ]

        self.assertEqual(
            sorted(bom_actions), [ACTION.CREATE, ACTION.UPDATE, ACTION.DELETE]
        )

    def test_validate_bom(self):
        """Validating the BOM (which re-saves every line) records no BOM item entries."""
        from part.models import BomItem

        items = [
            BomItem.objects.create(part=self.assembly, sub_part=part, quantity=1)
            for part in [self.resistor, self.alternative]
        ]

        self.assembly.validate_bom(self.user)

        for item in items:
            item.refresh_from_db()
            self.assertTrue(item.validated)
            self.assertFalse(
                self.entries(BomItem, item.pk, action=ACTION.UPDATE).exists()
            )

        # ...but the validation itself is recorded against the assembly
        entry = (
            self
            .entries(Part, self.assembly.pk, action=ACTION.UPDATE)
            .order_by('pk')
            .last()
        )
        self.assertEqual(entry.changes_dict['bom_validated'], [False, True])

    def test_substitutes(self):
        """Substitute changes are recorded against the assembly (not the BOM item)."""
        from part.models import BomItem, BomItemSubstitute

        bom_item = BomItem.objects.create(
            part=self.assembly, sub_part=self.resistor, quantity=1
        )

        pk = self.post(
            reverse('api-bom-substitute-list'),
            {'bom_item': bom_item.pk, 'part': self.alternative.pk},
        ).data['pk']

        self.delete(reverse('api-bom-substitute-detail', kwargs={'pk': pk}))

        entries = self.entries(BomItemSubstitute, pk)

        self.assertEqual(
            sorted(entries.values_list('action', flat=True)),
            [ACTION.CREATE, ACTION.DELETE],
        )

        for entry in entries:
            self.assertEqual(entry.parent_content_type, Part.get_content_type())
            self.assertEqual(entry.parent_object_pk, str(self.assembly.pk))
            self.assertEqual(
                entry.object_repr,
                f'{self.alternative.full_name} (substitute for {self.resistor.full_name})',
            )

        self.assertIn(
            'part.bomitemsubstitute', {e['model_type'] for e in self.assembly_history()}
        )

    def test_substitute_cascade_delete(self):
        """Substitutes deleted along with their BOM item retain the assembly reference."""
        from part.models import BomItem, BomItemSubstitute

        bom_item = BomItem.objects.create(
            part=self.assembly, sub_part=self.resistor, quantity=1
        )
        substitute = BomItemSubstitute.objects.create(
            bom_item=bom_item, part=self.alternative
        )
        substitute_pk = substitute.pk

        BomItem.objects.get(pk=bom_item.pk).delete()

        entry = self.entries(
            BomItemSubstitute, substitute_pk, action=ACTION.DELETE
        ).get()
        self.assertEqual(entry.parent_object_pk, str(self.assembly.pk))

    def test_copy_bom(self):
        """Copying a BOM is recorded against the new assembly."""
        from part.models import BomItem, BomItemSubstitute

        bom_item = BomItem.objects.create(
            part=self.assembly, sub_part=self.resistor, quantity=2
        )
        BomItemSubstitute.objects.create(bom_item=bom_item, part=self.alternative)

        other = Part.objects.create(
            name='Widget Assembly v2', description='An assembly', assembly=True
        )
        other.copy_bom_from(self.assembly)

        model_types = [
            (e['model_type'], e['action']) for e in self.assembly_history(other)
        ]

        self.assertIn(('part.bomitem', ACTION.CREATE), model_types)
        self.assertIn(('part.bomitemsubstitute', ACTION.CREATE), model_types)
