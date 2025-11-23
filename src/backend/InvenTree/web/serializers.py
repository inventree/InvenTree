"""DRF API serializers for the 'web' app."""

from rest_framework import serializers

from InvenTree.serializers import (
    FilterableCharField,
    FilterableJSONField,
    FilterableSerializerMixin,
    InvenTreeModelSerializer,
    enable_filter,
)

from .models import GuideDefinition, GuideExecution


class GuideDefinitionSerializer(FilterableSerializerMixin, InvenTreeModelSerializer):
    """A Guide Definition is used to describe a tipp or guide that might be available to be shown."""

    class Meta:
        """Metaclass defines serializer fields."""

        model = GuideDefinition
        fields = [
            'uid',
            'slug',
            'guide_type',
            'name',
            'description',
            'guide_data',
            'is_applicable',
        ]
        ordering_fields = ['guide_type', 'slug', 'name']

    description = enable_filter(FilterableCharField(allow_blank=True, required=False))
    guide_data = enable_filter(FilterableJSONField(required=False))
    is_applicable = serializers.SerializerMethodField()

    def get_is_applicable(self, instance) -> bool:
        """Determine if this guide is applicable in the current context.

        For example, a 'First Use Tipp' might only be applicable if the user has never used the system before.
        """
        user = self.context['request'].user
        executions = GuideExecution.objects.filter(user=user, type=instance.guide_type)

        # Specific logic based on guide type

        if instance.guide_type == GuideDefinition.GuideType.FirstUseTipp:
            # Check if the user has any prior activity
            if not user.is_authenticated:
                return False
            # Placeholder for actual activity check
            return not executions.exists()

        elif instance.guide_type == GuideDefinition.GuideType.Tipp:
            # Check if the user has any prior activity
            if not user.is_authenticated:
                return False
            # Tipps are always applicable if not a "done" execution is recorded
            if executions.filter(done=True).exists():
                return False

        return True


class EmptySerializer(serializers.Serializer):
    """An empty serializer, useful for endpoints that do not require any input or output."""

    class Meta:
        """Metaclass defines serializer fields."""

        fields = []
        model = GuideDefinition
