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
        # Example logic - this can be customized as needed
        if instance.guide_type == GuideDefinition.GuideType.FirstUseTipp:
            # Check if the user has any prior activity
            user = self.context['request'].user
            if not user.is_authenticated:
                return False
            # Placeholder for actual activity check
            has_activity = GuideExecution.objects.filter(user=user).exists()
            return not has_activity
        return True
