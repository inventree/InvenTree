"""Audit log tests for the Build model."""

from django.db.models import F
from django.urls import reverse

from audit.models import AuditLogEntry
from build.models import Build
from build.status_codes import BuildStatus
from build.test_build import BuildTestBase
from InvenTree.unit_test import InvenTreeAPITestCase

ACTION = AuditLogEntry.Action


def build_entries(build_pk, **filters):
    """Return audit entries recorded against a Build (by PK)."""
    return AuditLogEntry.objects.filter(
        content_type=Build.get_content_type(), object_pk=str(build_pk), **filters
    )


class BuildAuditTest(BuildTestBase):
    """Tests for audit history of Build objects."""

    def updates(self):
        """Return UPDATE entries for the test build (oldest first)."""
        return build_entries(self.build.pk, action=ACTION.UPDATE).order_by('pk')

    def test_create(self):
        """Creating a build order is recorded."""
        entry = build_entries(self.build.pk, action=ACTION.CREATE).get()

        self.assertEqual(entry.changes_dict['reference'][1], self.build.reference)
        self.assertEqual(entry.object_repr, self.build.reference)

        # Derived / tree fields are not recorded
        for field in ['reference_int', 'lft', 'rght', 'tree_id', 'level']:
            self.assertNotIn(field, entry.changes_dict)

    def test_status_change(self):
        """Status transitions (e.g. issuing the build) are recorded."""
        self.build.issue_build()

        entry = self.updates().last()

        self.assertEqual(
            entry.changes_dict['status'],
            [BuildStatus.PENDING.value, BuildStatus.PRODUCTION.value],
        )

    def test_complete_output(self):
        """The 'completed' quantity (updated via an F() expression) is recorded as a number."""
        self.build.issue_build()

        completed = self.build.completed

        self.build.complete_build_output(self.output_1, None)
        self.build.refresh_from_db()

        self.assertEqual(self.build.completed, completed + self.output_1.quantity)

        [entry] = [e for e in self.updates() if 'completed' in e.changes_dict]

        self.assertEqual(
            entry.changes_dict['completed'], [completed, self.build.completed]
        )
        self.assertNotIn('F(', str(entry.changes))

    def test_expression_update(self):
        """Saving any field as an F() expression records the resolved value."""
        self.build.priority = 5
        self.build.save()

        self.build.priority = F('priority') + 3
        self.build.save(update_fields=['priority'])

        entry = self.updates().last()
        self.assertEqual(entry.changes_dict, {'priority': [5, 8]})

        # An expression which does not change the value is not recorded
        n = self.updates().count()

        self.build.priority = F('priority') + 0
        self.build.save(update_fields=['priority'])

        self.assertEqual(self.updates().count(), n)

    def test_failed_save_not_recorded(self):
        """A deferred (expression) entry from a failed save is not attached to a later save."""
        from django.core.exceptions import FieldError
        from django.db import transaction

        self.build.priority = F('not_a_field') + 1

        with self.assertRaises(FieldError), transaction.atomic():
            self.build.save(update_fields=['priority'])

        # Subsequent save of an unrelated field
        self.build.refresh_from_db()
        self.build.title = 'New title'
        self.build.save()

        entry = self.updates().last()
        self.assertEqual(list(entry.changes_dict.keys()), ['title'])

    def test_delete_reparents_children(self):
        """Deleting a build re-parents its child builds - and the change is recorded."""
        child = Build.objects.create(
            part=self.assembly, quantity=1, reference='BO-9001', parent=self.build
        )

        grandchild = Build.objects.create(
            part=self.assembly, quantity=1, reference='BO-9002', parent=child
        )

        child_pk = child.pk
        child.delete()

        grandchild.refresh_from_db()
        self.assertEqual(grandchild.parent, self.build)

        entry = build_entries(grandchild.pk, action=ACTION.UPDATE).get()
        self.assertEqual(entry.changes_dict['parent'], [child_pk, self.build.pk])


class BuildAuditAPITest(InvenTreeAPITestCase):
    """Tests for build audit history via the API."""

    fixtures = ['category', 'part', 'location', 'bom', 'build', 'build_line', 'stock']

    roles = ['build.view', 'build.change']

    def test_edit_via_api(self):
        """Edits made via the API are recorded against the user, and shown in the history."""
        build = Build.objects.get(pk=1)

        self.patch(
            reverse('api-build-detail', kwargs={'pk': build.pk}),
            {'title': 'Updated title', 'priority': 7},
        )

        entry = build_entries(build.pk, action=ACTION.UPDATE).get()

        self.assertEqual(entry.actor, self.user)
        self.assertEqual(entry.changes_dict['title'][1], 'Updated title')
        self.assertEqual(entry.changes_dict['priority'][1], 7)

        history = self.get(
            reverse('api-audit-log-list'),
            {'model_type': 'build.build', 'model_id': build.pk},
        ).data

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['model_label'], 'Build Order')


class BuildStockAuditTest(BuildTestBase):
    """Stock operations performed by a build order record a single audit entry per stock item."""

    def stock_entries(self, item, n=0):
        """Return the audit entries for a stock item (after the first n entries)."""
        from stock.models import StockItem

        return list(
            AuditLogEntry.objects.filter(
                content_type=StockItem.get_content_type(), object_pk=str(item.pk)
            ).order_by('pk')[n:]
        )

    def test_create_output(self):
        """Creating build outputs records a single CREATE entry for each output."""
        from part.models import Part
        from stock.status_codes import StockHistoryCode

        # An assembly without any trackable components
        assembly = Part.objects.create(
            name='Simple Assembly', description='An assembly', assembly=True
        )
        build = Build.objects.create(part=assembly, quantity=5, reference='BO-9876')

        outputs = build.create_build_output(5, user=self.user)

        for output in outputs:
            [entry] = self.stock_entries(output)

            self.assertEqual(entry.action, ACTION.CREATE)
            self.assertEqual(entry.event_type, StockHistoryCode.BUILD_OUTPUT_CREATED)
            self.assertEqual(entry.actor, self.user)
            self.assertEqual(
                entry.additional_data['deltas']['buildorder']['pk'], build.pk
            )

    def test_create_serialized_outputs(self):
        """Creating serialized build outputs records a single CREATE entry for each output."""
        from stock.status_codes import StockHistoryCode

        self.build.part.trackable = True
        self.build.part.save()

        outputs = self.build.create_build_output(
            3, serials=['1001', '1002', '1003'], user=self.user
        )

        self.assertEqual(outputs.count(), 3)

        for output in outputs:
            [entry] = self.stock_entries(output)

            self.assertEqual(entry.event_type, StockHistoryCode.BUILD_OUTPUT_CREATED)
            self.assertEqual(entry.changes_dict['serial'][1], output.serial)

    def test_consume(self):
        """Consuming allocated stock records a single entry for each affected item."""
        from build.models import BuildItem
        from stock.models import StockItem
        from stock.status_codes import StockHistoryCode

        BuildItem.objects.create(
            build_line=self.line_1, stock_item=self.stock_1_1, quantity=3
        )
        BuildItem.objects.create(
            build_line=self.line_1, stock_item=self.stock_1_2, quantity=10
        )

        n_1 = len(self.stock_entries(self.stock_1_1))
        n_2 = len(self.stock_entries(self.stock_1_2))

        self.build.complete_allocations(
            BuildItem.objects.filter(build_line__build=self.build), user=self.user
        )

        # Fully consumed item
        [entry] = self.stock_entries(self.stock_1_1, n_1)

        self.assertEqual(entry.event_type, StockHistoryCode.BUILD_CONSUMED)
        self.assertEqual(entry.changes_dict['consumed_by'], [None, self.build.pk])
        self.assertEqual(entry.actor, self.user)

        # Partially consumed item (split)
        [entry] = self.stock_entries(self.stock_1_2, n_2)

        self.assertEqual(entry.event_type, StockHistoryCode.SPLIT_CHILD_ITEM)
        self.assertEqual(entry.changes_dict['quantity'], ['100.00000', '90.00000'])

        # The split item is created (and consumed)
        split = StockItem.objects.get(parent=self.stock_1_2)

        [entry] = self.stock_entries(split)

        self.assertEqual(entry.action, ACTION.CREATE)
        self.assertEqual(entry.event_type, StockHistoryCode.BUILD_CONSUMED)
        self.assertEqual(entry.changes_dict['consumed_by'][1], self.build.pk)

    def test_complete_output(self):
        """Completing a build output records a single entry."""
        from stock.status_codes import StockHistoryCode

        self.build.issue_build()

        n = len(self.stock_entries(self.output_1))

        self.build.complete_build_output(self.output_1, self.user)

        [entry] = self.stock_entries(self.output_1, n)

        self.assertEqual(entry.event_type, StockHistoryCode.BUILD_OUTPUT_COMPLETED)
        self.assertEqual(entry.changes_dict['is_building'], [True, False])

    def test_scrap_output(self):
        """Scrapping a build output records a single entry."""
        from stock.models import StockLocation
        from stock.status_codes import StockHistoryCode, StockStatus

        self.build.issue_build()

        location = StockLocation.objects.create(name='Scrap')

        n = len(self.stock_entries(self.output_1))

        self.build.scrap_build_output(
            self.output_1,
            self.output_1.quantity,
            location,
            user=self.user,
            notes='Scrapped',
            discard_allocations=True,
        )

        [entry] = self.stock_entries(self.output_1, n)

        self.assertEqual(entry.event_type, StockHistoryCode.BUILD_OUTPUT_REJECTED)
        self.assertEqual(entry.notes, 'Scrapped')
        self.assertEqual(
            entry.changes_dict['status'],
            [StockStatus.OK.value, StockStatus.REJECTED.value],
        )

    def test_consume_install(self):
        """Consuming trackable stock (installed into an output) records an entry for both items."""
        from build.models import BuildItem
        from stock.models import StockItem
        from stock.status_codes import StockHistoryCode

        component = StockItem.objects.create(
            part=self.sub_part_3, quantity=1, serial='SN-1'
        )

        BuildItem.objects.create(
            build_line=self.line_3,
            stock_item=component,
            quantity=1,
            install_into=self.output_1,
        )

        n_component = len(self.stock_entries(component))
        n_output = len(self.stock_entries(self.output_1))

        self.build.complete_allocations(
            BuildItem.objects.filter(stock_item=component), user=self.user
        )

        [entry] = self.stock_entries(component, n_component)

        self.assertEqual(entry.event_type, StockHistoryCode.INSTALLED_INTO_ASSEMBLY)
        self.assertEqual(entry.changes_dict['belongs_to'], [None, self.output_1.pk])
        self.assertEqual(
            entry.additional_data['deltas']['buildorder']['pk'], self.build.pk
        )

        # Nothing changed for the output itself - the event is recorded regardless
        [entry] = self.stock_entries(self.output_1, n_output)

        self.assertEqual(entry.event_type, StockHistoryCode.INSTALLED_CHILD_ITEM)
        self.assertEqual(entry.changes_dict, {})
        self.assertEqual(
            entry.additional_data['deltas']['stockitem']['pk'], component.pk
        )

    def test_consume_install_multiple(self):
        """Installing multiple components into one output records an entry for each."""
        from build.models import BuildItem
        from stock.models import StockItem
        from stock.status_codes import StockHistoryCode

        components = [
            StockItem.objects.create(part=self.sub_part_3, quantity=1, serial=serial)
            for serial in ['SN-1', 'SN-2']
        ]

        for component in components:
            BuildItem.objects.create(
                build_line=self.line_3,
                stock_item=component,
                quantity=1,
                install_into=self.output_1,
            )

        n_output = len(self.stock_entries(self.output_1))

        self.build.complete_allocations(
            BuildItem.objects.filter(stock_item__in=components), user=self.user
        )

        entries = self.stock_entries(self.output_1, n_output)

        self.assertEqual(len(entries), 2)

        for entry in entries:
            self.assertEqual(entry.event_type, StockHistoryCode.INSTALLED_CHILD_ITEM)

        self.assertEqual(
            sorted(
                entry.additional_data['deltas']['stockitem']['pk'] for entry in entries
            ),
            sorted(component.pk for component in components),
        )
