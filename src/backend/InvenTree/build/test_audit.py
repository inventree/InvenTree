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
