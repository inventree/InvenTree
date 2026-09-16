"""Tests for the 'trip_full_sample' tutorial - a worked example of the generic.states transition framework.

``SampleTrip`` is illustrative only: it has no migration and its router is not included in the
real API urlconf. To exercise it end-to-end (model + API) without touching the real InvenTree
schema or URL space, this module creates the model's DB table for the duration of the test
classes below (via the schema editor) and points ``ROOT_URLCONF`` at the small urlconf defined
in this module, rather than adding a migration or wiring the sample into the real project.
"""

import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase, override_settings
from django.urls import include, path, reverse

from generic.states import after_commit, can_proceed
from generic.states.introspection import available_transitions, transition_methods
from InvenTree.unit_test import InvenTreeAPITestCase, InvenTreeTestCase
from InvenTree.urls import urlpatterns as _real_urlpatterns

from .trip_full_sample import (
    SampleTrip,
    SampleTripViewSet,
    TripStatus,
    my_awesome_router,
)

# Mounted only for these tests via @override_settings(ROOT_URLCONF=__name__) below. Built on
# top of the real urlconf (rather than replacing it) since some middleware (e.g. host-settings
# checks) reverse()s real, unrelated URL names on every request. Mounted under 'api/' since
# InvenTree's own host-checking middleware exempts that prefix from host/origin validation.
urlpatterns = [
    # Tried before the real urlconf's own 'api/' entry, which has a catch-all fallback
    # for unrecognised API paths that would otherwise shadow these routes.
    path('api/', include(my_awesome_router.urls)),
    *_real_urlpatterns,
]


def setUpModule():
    """Create the DB table for the sample model (it ships without a migration).

    This must happen outside of any test transaction: SQLite cannot toggle foreign
    key enforcement (which ``schema_editor`` needs to do) in the middle of an
    already-open transaction, and every ``TestCase`` wraps its tests in one. Module
    setup/teardown runs before/after that per-class wrapping, so it is done here
    rather than in ``setUpClass``/``tearDownClass``.
    """
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(SampleTrip)


def tearDownModule():
    """Drop the DB table created by ``setUpModule``."""
    with connection.schema_editor() as schema_editor:
        schema_editor.delete_model(SampleTrip)


class TransitionHelperTests(TestCase):
    """Direct tests for small generic.states helpers not otherwise exercised by the sample."""

    def test_after_commit_logs_and_swallows_exceptions(self):
        """A callback that raises must not propagate - it is only logged."""

        def boom():
            raise RuntimeError('boom')

        with self.assertLogs('inventree', level='ERROR') as cm:
            with self.captureOnCommitCallbacks(execute=True):
                after_commit(boom)

        self.assertIn('Error in post-commit callback', cm.output[0])


class TripModelTransitionTests(InvenTreeTestCase):
    """Model-level tests for SampleTrip's transitions (no HTTP layer involved)."""

    def setUp(self):
        """Create a trip captained by the default test user."""
        super().setUp()
        self.other_user = User.objects.create_user(username='sailor', password='sailor')
        self.trip = SampleTrip.objects.create(
            name='Round the world',
            start_date=datetime.date(2024, 1, 1),
            end_date=datetime.date(2024, 2, 1),
            captain=self.user,
            status=TripStatus.PLANNING_DONE.value,
        )

    def test_transition_methods_discovered(self):
        """All five FSM transition methods must be discoverable on the model."""
        self.assertEqual(
            set(transition_methods(SampleTrip)),
            {'start_trip', 'complete', 'fail', 'cancel', 'postpone'},
        )

    def test_start_trip_from_planning_done(self):
        """'start_trip' is reachable from PLANNING_DONE."""
        self.assertTrue(can_proceed(self.trip.start_trip))
        self.assertTrue(self.trip.start_trip())
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.status, TripStatus.IN_PROGRESS.value)

    def test_start_trip_from_start_date_set(self):
        """'start_trip' is also reachable from START_DATE_SET (multiple sources)."""
        self.trip.status = TripStatus.START_DATE_SET.value
        self.trip.save()
        self.trip.start_trip()
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.status, TripStatus.IN_PROGRESS.value)

    def test_start_trip_invalid_source_state(self):
        """'start_trip' from PENDING is not a valid source and must raise."""
        self.trip.status = TripStatus.PENDING.value
        self.trip.save()
        self.assertFalse(can_proceed(self.trip.start_trip))
        with self.assertRaises(ValidationError):
            self.trip.start_trip()
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.status, TripStatus.PENDING.value)

    def test_repeating_a_completed_transition_reports_already_in_state(self):
        """Re-running a transition once already at its target reports 'already X', not a generic error."""
        self.trip.status = TripStatus.IN_PROGRESS.value
        self.trip.save()
        self.trip.complete()
        self.trip.refresh_from_db()

        with self.assertRaises(ValidationError) as cm:
            self.trip.complete()
        self.assertIn('already', str(cm.exception))

    def test_cancel_trip(self):
        """'cancel' moves an in-progress trip to CANCELLED."""
        self.trip.status = TripStatus.IN_PROGRESS.value
        self.trip.save()
        self.trip.cancel()
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.status, TripStatus.CANCELLED.value)

    def test_postpone_trip(self):
        """'postpone' (the model transition, not the API action) moves to POSTPONED."""
        self.trip.status = TripStatus.IN_PROGRESS.value
        self.trip.save()
        self.trip.postpone()
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.status, TripStatus.POSTPONED.value)

    def test_fail_rejects_non_captain(self):
        """Only the captain may fail a trip - any other user is refused."""
        self.trip.status = TripStatus.IN_PROGRESS.value
        self.trip.save()

        with self.assertRaises(ValidationError) as cm:
            self.trip.fail(user=self.other_user, logmessage='Mutiny')
        self.assertIn('Only the captain can perform this action', str(cm.exception))

        self.trip.refresh_from_db()
        self.assertEqual(self.trip.status, TripStatus.IN_PROGRESS.value)

    def test_fail_requires_logmessage(self):
        """The captain still needs to supply a log message to fail the trip."""
        self.trip.status = TripStatus.IN_PROGRESS.value
        self.trip.save()

        with self.assertRaises(ValidationError) as cm:
            self.trip.fail(user=self.user, logmessage='')
        self.assertIn('Log message is required', str(cm.exception))

    def test_fail_by_captain_succeeds_and_notifies(self):
        """The captain can fail the trip, which records the log and schedules a notification."""
        self.trip.status = TripStatus.IN_PROGRESS.value
        self.trip.save()

        with self.captureOnCommitCallbacks(execute=True):
            self.assertTrue(self.trip.fail(user=self.user, logmessage='Lost at sea'))

        self.trip.refresh_from_db()
        self.assertEqual(self.trip.status, TripStatus.FAILED.value)
        self.assertEqual(self.trip.last_log, 'Lost at sea')

    def test_available_transitions_blocked_without_captain(self):
        """The 'fail' condition blocks (with its reason) when there is no captain.

        Built in-memory and never saved: 'captain' is a required FK, so a captain-less
        trip can't be persisted - but available_transitions() only needs attribute
        access, not a DB round-trip.
        """
        trip = SampleTrip(
            name='Solo attempt',
            start_date=datetime.date(2024, 1, 1),
            end_date=datetime.date(2024, 2, 1),
            captain=None,
            status=TripStatus.IN_PROGRESS.value,
        )
        entries = {entry.name: entry for entry in available_transitions(trip)}
        self.assertTrue(entries['fail'].blocked)
        self.assertEqual(
            entries['fail'].blocking_reason,
            'Trip must have a captain assigned before it can fail',
        )
        # 'complete' has no conditions, so it is never blocked
        self.assertFalse(entries['complete'].blocked)
        self.assertIsNone(entries['complete'].blocking_reason)

    def test_available_transitions_not_blocked_with_captain(self):
        """With a captain assigned, the 'fail' condition passes and is not blocked."""
        self.trip.status = TripStatus.IN_PROGRESS.value
        self.trip.save()
        entries = {entry.name: entry for entry in available_transitions(self.trip)}
        self.assertFalse(entries['fail'].blocked)
        self.assertIsNone(entries['fail'].blocking_reason)

    def test_available_transitions_only_lists_reachable_transitions(self):
        """Only transitions valid from the current state are returned."""
        # From PLANNING_DONE, only 'start_trip' is reachable
        names = {entry.name for entry in available_transitions(self.trip)}
        self.assertEqual(names, {'start_trip'})


@override_settings(ROOT_URLCONF=__name__)
class TripApiTransitionTests(InvenTreeAPITestCase):
    """API-level tests for the SampleTrip transition endpoints."""

    superuser = True

    def setUp(self):
        """Create a trip captained by the (superuser) test user."""
        super().setUp()
        self.other_user = User.objects.create_user(username='sailor', password='sailor')
        self.trip = SampleTrip.objects.create(
            name='Round the world',
            start_date=datetime.date(2024, 1, 1),
            end_date=datetime.date(2024, 2, 1),
            captain=self.user,
            status=TripStatus.PLANNING_DONE.value,
        )

    def action_url(self, name, pk=None):
        """Build the URL for one of the router-registered SampleTrip actions."""
        return reverse(f'api-sampletrip-{name}', args=[pk] if pk is not None else [])

    def test_registered_and_skipped_transition_actions(self):
        """The viewset must expose 'start'/'complete'/'fail' and skip 'cancel'/'postpone'."""
        self.assertEqual(
            SampleTripViewSet.generated_transition_actions,
            {'start_trip': 'start', 'complete': 'complete', 'fail': 'fail'},
        )
        self.assertEqual(
            SampleTripViewSet.skipped_transitions['cancel'],
            'excluded by transition_exclude',
        )
        self.assertIn(
            "'postpone' is already defined",
            SampleTripViewSet.skipped_transitions['postpone'],
        )

    def test_list_available_transitions_from_planning_done(self):
        """Only exposed, reachable transitions are listed - 'postpone'/'cancel' never appear."""
        response = self.get(self.action_url('transitions', self.trip.pk))
        names = {entry['name'] for entry in response.data}
        self.assertEqual(names, {'start_trip'})

    def test_list_available_transitions_from_in_progress(self):
        """From IN_PROGRESS, 'complete' and 'fail' are listed and unblocked (captain assigned)."""
        self.trip.status = TripStatus.IN_PROGRESS.value
        self.trip.save()

        response = self.get(self.action_url('transitions', self.trip.pk))
        entries = {entry['name']: entry for entry in response.data}
        self.assertEqual(set(entries), {'complete', 'fail'})
        self.assertFalse(entries['fail']['blocked'])

    def test_start_endpoint(self):
        """POST .../start/ runs the 'start_trip' transition (exposed under an alias).

        With no explicit ``serializer_class`` for this action, the response falls back
        to the viewset's own serializer - so the body reflects the updated trip, not an
        empty object.
        """
        response = self.post(
            self.action_url('start', self.trip.pk), {}, expected_code=200
        )
        self.assertEqual(response.data['id'], self.trip.pk)
        self.assertEqual(response.data['status'], TripStatus.IN_PROGRESS.value)
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.status, TripStatus.IN_PROGRESS.value)

    def test_start_endpoint_invalid_source_state(self):
        """Attempting 'start' from a state where it isn't defined returns a clear 400."""
        self.trip.status = TripStatus.IN_PROGRESS.value
        self.trip.save()

        response = self.post(
            self.action_url('start', self.trip.pk), {}, expected_code=400
        )
        self.assertIn('is not available from state', response.data['detail'])

    def test_complete_endpoint(self):
        """POST .../complete/ runs the 'complete' transition."""
        self.trip.status = TripStatus.IN_PROGRESS.value
        self.trip.save()

        response = self.post(
            self.action_url('complete', self.trip.pk), {}, expected_code=200
        )
        self.assertEqual(response.data['status'], TripStatus.COMPLETED.value)
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.status, TripStatus.COMPLETED.value)

    def test_cancel_endpoint_is_not_registered(self):
        """'cancel' is excluded, so no endpoint for it exists at all."""
        url = reverse('api-sampletrip-detail', args=[self.trip.pk]) + 'cancel/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_postpone_endpoint_uses_hand_written_action(self):
        """The hand-written 'postpone' action wins over the auto-generated transition."""
        response = self.get(self.action_url('postpone', self.trip.pk))
        self.assertEqual(
            response.data,
            {'status': False, 'reason': 'Where we are going there is no taking back'},
        )
        # And the underlying model transition never actually ran:
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.status, TripStatus.PLANNING_DONE.value)

    def test_fail_endpoint_requires_logmessage(self):
        """Without 'logmessage', the request-argument serializer refuses the call."""
        self.trip.status = TripStatus.IN_PROGRESS.value
        self.trip.save()

        response = self.post(
            self.action_url('fail', self.trip.pk), {}, expected_code=400
        )
        self.assertIn('logmessage', response.data)

    def test_fail_endpoint_rejects_non_captain(self):
        """A non-captain (even a superuser) is refused with the blocking_reason message."""
        trip = SampleTrip.objects.create(
            name="Someone else's trip",
            start_date=datetime.date(2024, 1, 1),
            end_date=datetime.date(2024, 2, 1),
            captain=self.other_user,
            status=TripStatus.IN_PROGRESS.value,
        )

        response = self.post(
            self.action_url('fail', trip.pk),
            {'logmessage': 'mutiny'},
            expected_code=400,
        )
        self.assertEqual(
            response.data['detail'], 'Only the captain can perform this action'
        )

    def test_fail_endpoint_succeeds_for_captain(self):
        """The captain can fail the trip over the API, supplying the required log message."""
        self.trip.status = TripStatus.IN_PROGRESS.value
        self.trip.save()

        self.post(
            self.action_url('fail', self.trip.pk),
            {'logmessage': 'Lost at sea'},
            expected_code=200,
        )
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.status, TripStatus.FAILED.value)
        self.assertEqual(self.trip.last_log, 'Lost at sea')
