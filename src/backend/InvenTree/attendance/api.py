"""JSON API endpoints for the Attendance app."""

from django.contrib.auth.models import User
from django.urls import include, path
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_filters.rest_framework.filterset import FilterSet
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response

import InvenTree.permissions
from attendance.models import ClockEntry, Shift, ShiftAssignment
from attendance.serializers import (
    ClockEntryCreateSerializer,
    ClockEntrySerializer,
    ClockStatusSerializer,
    ShiftAssignmentSerializer,
    ShiftSerializer,
)
from InvenTree.filters import SEARCH_ORDER_FILTER, InvenTreeDateFilter
from InvenTree.mixins import CreateAPI, ListAPI, ListCreateAPI, RetrieveUpdateDestroyAPI


class ClockStatusView(ListAPI):
    """Return the current clock-in status for the requesting user.

    GET /api/attendance/status/
    Staff users may pass ?user=<id> to query another user's status.
    """

    permission_classes = [InvenTree.permissions.IsAuthenticatedOrReadScope]
    serializer_class = ClockStatusSerializer

    def get_queryset(self):
        """Not used — overridden by list()."""
        return ClockEntry.objects.none()

    def list(self, request, *args, **kwargs):
        """Return current clock status for the resolved user."""
        user = self._resolve_user(request)
        open_entry = ClockEntry.objects.filter(
            user=user, clock_out__isnull=True
        ).first()
        last_entry = ClockEntry.objects.filter(user=user).first()

        data = {
            'clocked_in': open_entry is not None,
            'current_entry': ClockEntrySerializer(open_entry).data
            if open_entry
            else None,
            'last_entry': ClockEntrySerializer(last_entry).data if last_entry else None,
        }
        return Response(data)

    def _resolve_user(self, request):
        """Resolve which user to return status for."""
        user_id = request.query_params.get('user')
        if user_id is not None:
            if not request.user.is_staff:
                raise PermissionDenied(
                    _("Only staff users may query another user's status.")
                )
            try:
                return User.objects.get(pk=user_id)
            except User.DoesNotExist:
                raise NotFound(_('User not found.'))
        return request.user


class ClockActionView(CreateAPI):
    """Clock in or out.

    POST /api/attendance/clock/
    Body: { "action": "in" | "out", "location"?: "...", "notes"?: "..." }
    """

    permission_classes = [InvenTree.permissions.IsAuthenticatedOrReadScope]
    serializer_class = ClockEntryCreateSerializer

    def create(self, request, *args, **kwargs):
        """Clock in or out based on the 'action' field."""
        serializer = ClockEntryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        location = serializer.validated_data.get('location', '')
        notes = serializer.validated_data.get('notes', '')

        if action == 'in':
            return self._clock_in(request.user, location, notes)
        return self._clock_out(request.user, location, notes)

    def _clock_in(self, user, location, notes):
        """Create a new open clock entry."""
        open_entry = ClockEntry.objects.filter(
            user=user, clock_out__isnull=True
        ).first()

        if open_entry is not None:
            return Response(
                {
                    'detail': _('You are already clocked in since %(since)s.')
                    % {'since': open_entry.clock_in.isoformat()},
                    'entry': ClockEntrySerializer(open_entry).data,
                },
                status=status.HTTP_409_CONFLICT,
            )

        entry = ClockEntry.objects.create(
            user=user, clock_in=timezone.now(), location=location, notes=notes
        )
        return Response(
            ClockEntrySerializer(entry).data, status=status.HTTP_201_CREATED
        )

    def _clock_out(self, user, location, notes):
        """Close the most recent open clock entry."""
        open_entry = ClockEntry.objects.filter(
            user=user, clock_out__isnull=True
        ).first()

        if open_entry is None:
            return Response(
                {'detail': _('You are not clocked in.')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        open_entry.clock_out = timezone.now()

        # Optionally update location / notes if the user provided them on clock-out
        if location:
            open_entry.location = location
        if notes:
            existing = open_entry.notes or ''
            open_entry.notes = f'{existing}\n{notes}'.strip()

        open_entry.save(update_fields=['clock_out', 'location', 'notes', 'updated_at'])
        return Response(
            ClockEntrySerializer(open_entry).data, status=status.HTTP_200_OK
        )


class ClockEntryFilter(FilterSet):
    """Filter for ClockEntry list endpoint."""

    clock_in_after = InvenTreeDateFilter(
        field_name='clock_in',
        label=_('Clock-in after'),
        lookup_expr='gte',
        help_text=_('Filter entries clocked in on or after this date'),
    )
    clock_in_before = InvenTreeDateFilter(
        field_name='clock_in',
        label=_('Clock-in before'),
        lookup_expr='lt',
        help_text=_('Filter entries clocked in on or before this date'),
    )

    class Meta:
        """Metaclass for ClockEntryFilter."""

        model = ClockEntry
        fields: list[str] = []


class ClockEntryList(ListAPI):
    """List clock entries for the requesting user.

    GET /api/attendance/entries/
    Staff may pass ?user=<id> to view another user's entries.
    Supports date filtering via ?clock_in_after= and ?clock_in_before=.
    """

    permission_classes = [InvenTree.permissions.IsAuthenticatedOrReadScope]
    serializer_class = ClockEntrySerializer
    filterset_class = ClockEntryFilter
    filter_backends = SEARCH_ORDER_FILTER

    def get_queryset(self):
        """Return entries for the resolved user."""
        user = self._resolve_user()
        return ClockEntry.objects.filter(user=user)

    def _resolve_user(self):
        user_id = self.request.query_params.get('user')
        if user_id is not None:
            if not self.request.user.is_staff:
                raise PermissionDenied()
            try:
                return User.objects.get(pk=user_id)
            except User.DoesNotExist:
                raise NotFound(_('User not found.'))
        return self.request.user


class TimesheetSummaryView(ListAPI):
    """Aggregated hours per user for management reporting.

    GET /api/attendance/summary/
    Supports ?clock_in_after= and ?clock_in_before= date filters,
    and optional ?user=<id> to filter to a single user.
    """

    permission_classes = [InvenTree.permissions.IsStaffOrReadOnlyScope]

    def list(self, request, *args, **kwargs):
        """Return aggregated per-user timesheet summary."""
        queryset = ClockEntry.objects.all()

        after = request.query_params.get('clock_in_after')
        before = request.query_params.get('clock_in_before')
        user_id = request.query_params.get('user')

        if after:
            queryset = queryset.filter(clock_in__gte=after)
        if before:
            queryset = queryset.filter(clock_in__lt=before)
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        entries = list(
            queryset.select_related('user').order_by('user__username', '-clock_in')
        )

        # Aggregate per user
        summary: dict[int, dict] = {}
        for entry in entries:
            uid = entry.user_id
            if uid not in summary:
                summary[uid] = {
                    'username': entry.user.username,
                    'user_full_name': entry.user.get_full_name() or entry.user.username,
                    'total_hours': 0.0,
                    'entry_count': 0,
                    'is_clocked_in': False,
                }
            hours = entry.duration.total_seconds() / 3600.0
            summary[uid]['total_hours'] += hours
            summary[uid]['entry_count'] += 1
            if entry.is_clocked_in:
                summary[uid]['is_clocked_in'] = True

        # Round to 2 decimal places
        for row in summary.values():
            row['total_hours'] = round(row['total_hours'], 2)

        return Response(list(summary.values()))


class ShiftList(ListCreateAPI):
    """List all shifts or create a new one (staff only)."""

    permission_classes = [InvenTree.permissions.IsStaffOrReadOnlyScope]
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer


class ShiftDetail(RetrieveUpdateDestroyAPI):
    """Retrieve, update or delete a shift (staff only)."""

    permission_classes = [InvenTree.permissions.IsStaffOrReadOnlyScope]
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer


class ShiftAssignmentList(ListCreateAPI):
    """List all shift assignments or create a new one (staff only)."""

    permission_classes = [InvenTree.permissions.IsStaffOrReadOnlyScope]
    queryset = ShiftAssignment.objects.all()
    serializer_class = ShiftAssignmentSerializer


class ShiftAssignmentDetail(RetrieveUpdateDestroyAPI):
    """Retrieve, update or delete a shift assignment (staff only)."""

    permission_classes = [InvenTree.permissions.IsStaffOrReadOnlyScope]
    queryset = ShiftAssignment.objects.all()
    serializer_class = ShiftAssignmentSerializer


attendance_urls = [
    # Clock in / out
    path('status/', ClockStatusView.as_view(), name='api-attendance-status'),
    path('clock/', ClockActionView.as_view(), name='api-attendance-clock'),
    path('entries/', ClockEntryList.as_view(), name='api-attendance-entries'),
    path('summary/', TimesheetSummaryView.as_view(), name='api-attendance-summary'),
    # Shifts
    path(
        'shifts/',
        include([
            path(
                '<int:pk>/', ShiftDetail.as_view(), name='api-attendance-shift-detail'
            ),
            path('', ShiftList.as_view(), name='api-attendance-shift-list'),
        ]),
    ),
    # Assignments
    path(
        'assignments/',
        include([
            path(
                '<int:pk>/',
                ShiftAssignmentDetail.as_view(),
                name='api-attendance-assignment-detail',
            ),
            path(
                '', ShiftAssignmentList.as_view(), name='api-attendance-assignment-list'
            ),
        ]),
    ),
]
