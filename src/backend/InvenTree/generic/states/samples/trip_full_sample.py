"""Sample implementation of using transitions."""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from common.notifications import trigger_notification
from generic.states import (
    ColorEnum,
    StateTransitionMixin,
    StatusCode,
    after_commit,
    blocking_reason,
    inventree_transition,
)
from generic.states.api_helpers import FSMTransitionMixin
from generic.states.fields import InvenTreeCustomStatusModelField
from InvenTree.helpers_api import CleanModelViewSet, InvenTreeApiRouter

# 1. enums for all possible states


class TripStatus(StatusCode):
    """Defines a set of status codes for a SampleTrip.

    Attributes:
        PENDING: Trip is pending / planned
        PLANNING_DONE: Trip planning is completed
        START_DATE_SET: Trip start date has been set
        IN_PROGRESS: Trip is currently in progress
        COMPLETED: Trip has been completed
        CANCELLED: Trip was cancelled
        FAILED: Trip has failed
        POSTPONED: Trip has been postponed

    """

    PENDING = 10, _('Pending'), ColorEnum.secondary
    PLANNING_DONE = 20, _('Planning Done'), ColorEnum.info
    START_DATE_SET = 30, _('Start Date Set'), ColorEnum.info
    IN_PROGRESS = 40, _('In Progress'), ColorEnum.primary
    COMPLETED = 50, _('Completed'), ColorEnum.success
    CANCELLED = 60, _('Cancelled'), ColorEnum.danger
    FAILED = 70, _('Failed'), ColorEnum.warning
    POSTPONED = 80, _('Postponed'), ColorEnum.warning


from generic.events import BaseEventEnum


class TripEvents(BaseEventEnum):
    """Event enumeration for the SampleTrip."""

    # SampleTrip events
    STARTED = 'trip.started'
    COMPLETED = 'trip.completed'
    FAILED = 'trip.failed'
    CANCELLED = 'trip.cancelled'
    POSTPONED = 'trip.postponed'


class SampleTrip(StateTransitionMixin, models.Model):
    """Traveling the world with a group of people."""

    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    captain = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='captained_trips'
    )
    was_successful = models.BooleanField(default=None, blank=True, null=True)
    last_log = models.TextField(blank=True, null=True)

    status = InvenTreeCustomStatusModelField(
        default=TripStatus.PENDING.value,
        choices=TripStatus.items(),
        status_class=TripStatus,
        verbose_name=_('Status'),
        help_text=_('Current status'),
    )

    # region transitions
    @inventree_transition(
        source=[TripStatus.PLANNING_DONE, TripStatus.START_DATE_SET],
        target=TripStatus.IN_PROGRESS,
        field='status',
        event=TripEvents.STARTED,
    )
    def start_trip(self):
        """Transition the trip to 'In Progress'."""
        # Note: this is named differently than the other transition methods; this could cause confusion on the api

    @inventree_transition(
        source=[TripStatus.IN_PROGRESS],
        target=TripStatus.COMPLETED,
        event=TripEvents.COMPLETED,
        field='status',
    )
    def complete(self):
        """Transition the trip to 'Completed'."""

    @blocking_reason(_('Trip must have a captain assigned before it can be failed'))
    def has_captain(self):
        """Check if the trip has a captain assigned."""
        return self.captain_id is not None

    @inventree_transition(
        source=[TripStatus.IN_PROGRESS],
        target=TripStatus.FAILED,
        field='status',
        event=TripEvents.FAILED,
        conditions=[has_captain],
    )
    def fail(self, user: User, logmessage: str):
        """Transition the trip to 'Failed'. Only the captain can mark a trip as failed."""
        if not self.captain or self.captain != user:
            raise ValidationError(_('Only the captain can perform this action'))

        if not logmessage:
            raise ValidationError(_('Log message is required to fail the trip.'))

        self.last_log = logmessage

        after_commit(_notify_fail, self.id)

    @inventree_transition(
        source=[TripStatus.IN_PROGRESS],
        target=TripStatus.CANCELLED,
        event=TripEvents.CANCELLED,
        field='status',
    )
    def cancel(self):
        """Transition the trip to 'Cancelled'."""

    @inventree_transition(
        source=[TripStatus.IN_PROGRESS],
        target=TripStatus.POSTPONED,
        event=TripEvents.POSTPONED,
        field='status',
    )
    def postpone(self):
        """Transition the trip to 'Postponed'."""

    # endregion transitions


def _notify_fail(trip_id):
    """Notify that a trip has failed."""
    trip = SampleTrip.objects.get(id=trip_id)
    all_involved = [trip.captain]
    context = {
        'name': _('Trip Failed'),
        'slug': 'trip.failed',
        'message': _('The trip has been marked as failed'),
    }
    trigger_notification(trip, 'trip.failed', targets=all_involved, context=context)


# And all of the APIs

my_awesome_router = InvenTreeApiRouter()


class SampleTripSerializer(serializers.ModelSerializer):
    """Serializer for the SampleTrip model."""

    class Meta:
        """Meta class for the SampleTrip serializer."""

        model = SampleTrip
        fields = '__all__'


class TripFailSerializer(serializers.Serializer):
    """Serializer supplying the extra argument required by the 'fail' transition."""

    logmessage = serializers.CharField(write_only=True)


class SampleTripViewSet(FSMTransitionMixin, CleanModelViewSet):
    """ViewSet for the SampleTrip model."""

    queryset = SampleTrip.objects.all()
    serializer_class = SampleTripSerializer

    transition_exclude = ('cancel',)
    transition_options = {
        # start_trip is named differently to the rest of the transitions; expose it as 'start'
        'start_trip': {'name': 'start'},
        'fail': {'serializer_class': TripFailSerializer},
    }

    @action(detail=True, methods=['get'])
    def postpone(self, *args, **kwargs):
        """Handle the 'postpone' action for the SampleTrip."""
        # Mirrors the 'postpone' transition defined in the model but takes precedence over the transition
        return Response({
            'status': False,
            'reason': 'Where we are going there is no taking back',
        })


my_awesome_router.register('trips', SampleTripViewSet)

urlpatterns = my_awesome_router.urls
