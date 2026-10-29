"""Unit tests for the BomSnapshot model and API."""

from django.core.exceptions import ValidationError
from django.urls import reverse

import build.models
from common.settings import set_global_setting
from InvenTree.unit_test import InvenTreeAPITestCase, InvenTreeTestCase, TestQueryMixin

from .models import BomItem, BomItemSubstitute, BomSnapshot, Part


class BomSnapshotTestMixin:
    """Mixin class providing a simple assembly with a BOM."""

    def create_assembly(self):
        """Create an assembly part with two BOM lines."""
        self.assembly = Part.objects.create(
            name='Snapshot Assembly', description='An assembly', assembly=True
        )

        self.components = [
            Part.objects.create(
                name=f'Snapshot Component {idx}',
                description='A component',
                IPN=f'SC-{idx}',
                component=True,
            )
            for idx in range(3)
        ]

        self.line_1 = BomItem.objects.create(
            part=self.assembly,
            sub_part=self.components[0],
            quantity=2,
            reference='R1, R2',
        )

        self.line_2 = BomItem.objects.create(
            part=self.assembly, sub_part=self.components[1], quantity=1.5, attrition=5
        )


class BomSnapshotModelTest(BomSnapshotTestMixin, TestQueryMixin, InvenTreeTestCase):
    """Tests for the BomSnapshot model."""

    def setUp(self):
        """Create an assembly for testing."""
        super().setUp()
        self.create_assembly()

    def test_snapshot_on_validate(self):
        """A snapshot is created when the BOM is validated."""
        self.assertEqual(self.assembly.bom_snapshots.count(), 0)

        self.assembly.validate_bom(self.user, note='Initial release')

        self.assertEqual(self.assembly.bom_snapshots.count(), 1)

        snapshot = self.assembly.bom_snapshots.first()

        self.assertEqual(snapshot.checksum, self.assembly.bom_checksum)
        self.assertEqual(snapshot.created_by, self.user)
        self.assertEqual(snapshot.note, 'Initial release')
        self.assertEqual(snapshot.line_count, 2)
        self.assertEqual(snapshot.schema_version, BomSnapshot.SCHEMA_VERSION)

        data = snapshot.data

        self.assertEqual(data['assembly']['pk'], self.assembly.pk)
        self.assertEqual(data['assembly']['name'], 'Snapshot Assembly')
        self.assertEqual(len(data['items']), 2)

        item = data['items'][0]

        self.assertEqual(item['pk'], self.line_1.pk)
        self.assertIsNone(item['inherited_from'])
        self.assertEqual(item['sub_part']['pk'], self.components[0].pk)
        self.assertEqual(item['sub_part']['IPN'], 'SC-0')
        self.assertEqual(item['quantity'], '2')
        self.assertEqual(item['reference'], 'R1, R2')
        self.assertEqual(item['substitutes'], [])

        item = data['items'][1]

        self.assertEqual(item['quantity'], '1.5')
        self.assertEqual(item['attrition'], '5')

    def test_no_snapshot_on_invalidate(self):
        """Marking the BOM as invalid does not create a snapshot."""
        self.assembly.validate_bom(self.user, valid=False)
        self.assertEqual(self.assembly.bom_snapshots.count(), 0)

    def test_dedupe(self):
        """A snapshot is only created if the BOM has changed since the latest snapshot."""
        self.assembly.validate_bom(self.user)
        self.assembly.validate_bom(self.user, note='Ignored')

        self.assertEqual(self.assembly.bom_snapshots.count(), 1)
        self.assertEqual(self.assembly.bom_snapshots.first().note, '')

        # Change the BOM, and re-validate
        self.line_1.set_quantity(3)
        self.line_1.save()

        self.assertFalse(self.assembly.is_bom_valid())

        self.assembly.validate_bom(self.user)
        self.assertEqual(self.assembly.bom_snapshots.count(), 2)

        # Revert the change - returning to a previous state is a new snapshot (A -> B -> A)
        self.line_1.set_quantity(2)
        self.line_1.save()

        self.assembly.validate_bom(self.user)
        self.assertEqual(self.assembly.bom_snapshots.count(), 3)

        checksums = list(
            self.assembly.bom_snapshots.order_by('pk').values_list(
                'checksum', flat=True
            )
        )

        self.assertEqual(checksums[0], checksums[2])
        self.assertNotEqual(checksums[0], checksums[1])

    def test_setting_disabled(self):
        """No snapshot is created if the PART_BOM_SNAPSHOT setting is disabled."""
        set_global_setting('PART_BOM_SNAPSHOT', False)

        self.assembly.validate_bom(self.user)

        self.assertTrue(self.assembly.is_bom_valid())
        self.assertEqual(self.assembly.bom_snapshots.count(), 0)

        set_global_setting('PART_BOM_SNAPSHOT', True)

    def test_immutable(self):
        """An existing snapshot cannot be modified."""
        self.assembly.validate_bom(self.user)

        snapshot = self.assembly.bom_snapshots.first()
        snapshot.note = 'Modified'

        with self.assertRaises(ValidationError):
            snapshot.save()

        snapshot.refresh_from_db()
        self.assertEqual(snapshot.note, '')

    def test_inherited_and_substitutes(self):
        """Inherited BOM items and substitute parts are included in the snapshot."""
        template = Part.objects.create(
            name='Snapshot Template',
            description='A template assembly',
            assembly=True,
            is_template=True,
        )

        variant = Part.objects.create(
            name='Snapshot Variant',
            description='A variant assembly',
            assembly=True,
            variant_of=template,
        )

        inherited_line = BomItem.objects.create(
            part=template, sub_part=self.components[0], quantity=1, inherited=True
        )

        # Not inherited - should not appear in the variant BOM
        BomItem.objects.create(
            part=template, sub_part=self.components[1], quantity=1, inherited=False
        )

        own_line = BomItem.objects.create(
            part=variant, sub_part=self.components[2], quantity=4
        )

        BomItemSubstitute.objects.create(bom_item=own_line, part=self.components[1])

        variant.validate_bom(self.user)

        snapshot = variant.bom_snapshots.first()
        items = {item['pk']: item for item in snapshot.data['items']}

        self.assertEqual(snapshot.line_count, 2)
        self.assertEqual(set(items.keys()), {inherited_line.pk, own_line.pk})

        self.assertEqual(items[inherited_line.pk]['inherited_from'], template.pk)
        self.assertIsNone(items[own_line.pk]['inherited_from'])

        substitutes = items[own_line.pk]['substitutes']
        self.assertEqual(len(substitutes), 1)
        self.assertEqual(substitutes[0]['pk'], self.components[1].pk)
        self.assertEqual(substitutes[0]['name'], 'Snapshot Component 1')

        # Substitutes are not part of the BOM checksum
        BomItemSubstitute.objects.create(bom_item=own_line, part=self.components[0])
        self.assertTrue(variant.is_bom_valid())

    def test_stored_values(self):
        """Snapshot data is stored by value, and is unaffected by later part changes."""
        self.assembly.validate_bom(self.user)

        component = self.components[0]
        component.name = 'Renamed Component'
        component.save()

        # Delete the other component (and thus its BOM line)
        set_global_setting('PART_ALLOW_DELETE_FROM_ASSEMBLY', True)

        deleted = self.components[1]
        deleted.active = False
        deleted.save()
        deleted.delete()

        set_global_setting('PART_ALLOW_DELETE_FROM_ASSEMBLY', False)

        self.assertFalse(BomItem.objects.filter(pk=self.line_2.pk).exists())

        snapshot = self.assembly.bom_snapshots.first()
        items = snapshot.data['items']

        self.assertEqual(snapshot.line_count, 2)
        self.assertEqual(items[0]['sub_part']['name'], 'Snapshot Component 0')
        self.assertEqual(items[1]['sub_part']['name'], 'Snapshot Component 1')

    def test_snapshot_queries(self):
        """The number of queries required to snapshot the BOM does not scale with BOM size."""
        for idx in range(50):
            sub_part = Part.objects.create(
                name=f'Bulk Component {idx}', description='A component', component=True
            )

            item = BomItem.objects.create(
                part=self.assembly, sub_part=sub_part, quantity=1
            )

            BomItemSubstitute.objects.create(bom_item=item, part=self.components[0])

        with self.assertNumQueriesLessThan(10):
            data = self.assembly.get_bom_snapshot_data()

        self.assertEqual(len(data), 52)

    def test_build_snapshot(self):
        """A build order records the validated BOM snapshot it was created against."""
        # BOM not validated - no snapshot
        bo = build.models.Build.objects.create(
            part=self.assembly, quantity=1, reference='BO-9990'
        )
        self.assertIsNone(bo.bom_snapshot)

        self.assembly.validate_bom(self.user)
        snapshot = self.assembly.bom_snapshots.first()

        bo = build.models.Build.objects.create(
            part=self.assembly, quantity=1, reference='BO-9991'
        )
        self.assertEqual(bo.bom_snapshot, snapshot)

        # Change the BOM - the BOM is no longer valid, so no snapshot is linked
        self.line_2.set_quantity(10)
        self.line_2.save()

        bo = build.models.Build.objects.create(
            part=self.assembly, quantity=1, reference='BO-9992'
        )
        self.assertIsNone(bo.bom_snapshot)

        # Validate with snapshots disabled - the stored checksum does not match the latest snapshot
        set_global_setting('PART_BOM_SNAPSHOT', False)
        self.assembly.validate_bom(self.user)
        set_global_setting('PART_BOM_SNAPSHOT', True)

        self.assertTrue(self.assembly.is_bom_valid())

        bo = build.models.Build.objects.create(
            part=self.assembly, quantity=1, reference='BO-9993'
        )
        self.assertIsNone(bo.bom_snapshot)

        # Deleting the snapshot does not delete the build order
        snapshot.delete()
        bo = build.models.Build.objects.get(reference='BO-9991')
        self.assertIsNone(bo.bom_snapshot)


class BomSnapshotAPITest(BomSnapshotTestMixin, InvenTreeAPITestCase):
    """Tests for the BomSnapshot API endpoints."""

    roles = ['part.view', 'bom.view']

    def setUp(self):
        """Create an assembly with a validated BOM."""
        super().setUp()
        self.create_assembly()

        self.assembly.validate_bom(self.user, note='First')

        self.line_1.set_quantity(5)
        self.line_1.save()

        self.assembly.validate_bom(self.user, note='Second')

        # A different assembly, with its own snapshot
        other = Part.objects.create(
            name='Other Assembly', description='Another assembly', assembly=True
        )
        BomItem.objects.create(part=other, sub_part=self.components[2], quantity=1)
        other.validate_bom(None)

    def test_list(self):
        """Test the BomSnapshot list endpoint."""
        url = reverse('api-bom-snapshot-list')

        response = self.get(url)
        self.assertEqual(len(response.data), 3)

        response = self.get(url, {'part': self.assembly.pk})
        self.assertEqual(len(response.data), 2)

        # Newest first
        self.assertEqual(response.data[0]['note'], 'Second')
        self.assertEqual(response.data[1]['note'], 'First')

        entry = response.data[0]

        self.assertEqual(entry['line_count'], 2)
        self.assertEqual(entry['created_by'], self.user.pk)
        self.assertEqual(entry['created_by_detail']['username'], self.user.username)

        # BOM data is not included in the list endpoint
        self.assertNotIn('data', entry)

    def test_detail(self):
        """Test the BomSnapshot detail endpoint."""
        snapshot = self.assembly.bom_snapshots.order_by('pk').first()
        url = reverse('api-bom-snapshot-detail', kwargs={'pk': snapshot.pk})

        response = self.get(url)

        self.assertEqual(response.data['note'], 'First')
        self.assertEqual(len(response.data['data']['items']), 2)
        self.assertEqual(response.data['data']['items'][0]['quantity'], '2')

    def test_read_only(self):
        """Snapshots cannot be created, modified or deleted via the API."""
        self.assignRole('bom.add')
        self.assignRole('bom.change')
        self.assignRole('bom.delete')

        snapshot = self.assembly.bom_snapshots.first()

        list_url = reverse('api-bom-snapshot-list')
        detail_url = reverse('api-bom-snapshot-detail', kwargs={'pk': snapshot.pk})

        self.post(list_url, {'part': self.assembly.pk}, expected_code=405)
        self.patch(detail_url, {'note': 'Modified'}, expected_code=405)
        self.delete(detail_url, expected_code=405)

        snapshot.refresh_from_db()
        self.assertEqual(snapshot.note, 'Second')

    def test_permissions(self):
        """The BOM view permission is required to access snapshots."""
        snapshot = self.assembly.bom_snapshots.first()

        self.clearRoles()
        self.assignRole('part.view')

        self.get(reverse('api-bom-snapshot-list'), expected_code=403)
        self.get(
            reverse('api-bom-snapshot-detail', kwargs={'pk': snapshot.pk}),
            expected_code=403,
        )

    def test_validate_note(self):
        """A note provided via the BOM validation API is stored against the snapshot."""
        self.assignRole('part.change')
        self.assignRole('bom.change')

        url = reverse('api-part-bom-validate', kwargs={'pk': self.assembly.pk})

        self.line_2.set_quantity(7)
        self.line_2.save()

        self.patch(url, {'valid': True, 'note': 'ECO-123'}, expected_code=200)

        snapshot = self.assembly.bom_snapshots.order_by('-pk').first()
        self.assertEqual(snapshot.note, 'ECO-123')
        self.assertEqual(snapshot.created_by, self.user)
        self.assertEqual(self.assembly.bom_snapshots.count(), 3)

        # Re-validating an unchanged BOM does not create a snapshot (the note is discarded)
        self.patch(url, {'valid': True, 'note': 'Discarded'}, expected_code=200)
        self.assertEqual(self.assembly.bom_snapshots.count(), 3)

    def test_build_field(self):
        """The 'bom_snapshot' field is exposed (read-only) via the BuildOrder API."""
        self.assignRole('build.view')
        self.assignRole('build.change')

        snapshot = self.assembly.get_latest_bom_snapshot()
        self.assertIsNotNone(snapshot)

        bo = build.models.Build.objects.create(
            part=self.assembly, quantity=1, reference='BO-9995'
        )

        url = reverse('api-build-detail', kwargs={'pk': bo.pk})

        response = self.get(url)
        self.assertEqual(response.data['bom_snapshot'], snapshot.pk)

        # The field cannot be changed via the API
        self.patch(url, {'bom_snapshot': None}, expected_code=200)

        bo.refresh_from_db()
        self.assertEqual(bo.bom_snapshot, snapshot)
