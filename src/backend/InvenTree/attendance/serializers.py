"""DRF serializers for the attendance app."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from attendance.models import ClockEntry, Shift, ShiftAssignment


class ClockEntrySerializer(serializers.ModelSerializer):
    """Serializer for a clock-in / clock-out entry."""

    username = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.SerializerMethodField(read_only=True)
    is_clocked_in = serializers.BooleanField(read_only=True)
    duration = serializers.SerializerMethodField(read_only=True)
    clock_in = serializers.DateTimeField(read_only=True)
    clock_out = serializers.DateTimeField(read_only=True)

    class Meta:
        """Serializer metaclass."""

        model = ClockEntry
        fields = [
            'pk',
            'user',
            'username',
            'user_full_name',
            'clock_in',
            'clock_out',
            'is_clocked_in',
            'duration',
            'location',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'pk',
            'user',
            'username',
            'user_full_name',
            'clock_in',
            'clock_out',
            'is_clocked_in',
            'duration',
            'created_at',
            'updated_at',
        ]

    def get_user_full_name(self, obj):
        """Return the user's full name, falling back to username."""
        return obj.user.get_full_name() or obj.user.username

    def get_duration(self, obj):
        """Return duration as a human-readable string."""
        delta = obj.duration
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f'{hours}h {minutes}m'


class ClockEntryCreateSerializer(serializers.Serializer):
    """Serializer for creating (clock-in) or closing (clock-out) a clock entry."""

    action = serializers.ChoiceField(
        choices=['in', 'out'], help_text=_("'in' to clock in, 'out' to clock out")
    )
    location = serializers.CharField(required=False, allow_blank=True, max_length=100)
    notes = serializers.CharField(required=False, allow_blank=True)


class ClockStatusSerializer(serializers.Serializer):
    """Read-only snapshot of the current user's clock status."""

    clocked_in = serializers.BooleanField(read_only=True)
    current_entry = ClockEntrySerializer(read_only=True, allow_null=True)
    last_entry = ClockEntrySerializer(read_only=True, allow_null=True)


class ShiftSerializer(serializers.ModelSerializer):
    """Serializer for Shift CRUD."""

    class Meta:
        """Serializer metaclass."""

        model = Shift
        fields = '__all__'


class ShiftAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for ShiftAssignment CRUD."""

    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        """Serializer metaclass."""

        model = ShiftAssignment
        fields = ['pk', 'user', 'username', 'shift', 'start_date', 'end_date']
