"""DRF API serializers for the 'web' app."""

from rest_framework import serializers

import web.types as web_types
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

    def get_is_applicable(self, instance: GuideDefinition) -> bool:
        """Determine if this guide is applicable in the current context.

        For example, a 'First Use Tipp' might only be applicable if the user has never used the system before.
        """
        type_def = None
        if instance.guide_type is GuideDefinition.GuideType.FirstUseTipp:
            type_def = web_types.FirstUseTipp
        elif instance.guide_type is GuideDefinition.GuideType.Tipp:
            type_def = web_types.Tipp
        else:
            raise NotImplementedError(
                f'Guide type {instance.guide_type} not implemented'
            )

        # Cast definition and check applicability
        type_instance = type_def(**instance.guide_data)
        user = self.context['request'].user
        executions = GuideExecution.objects.filter(
            user=user, guide__guide_type=instance.guide_type
        )
        return type_instance.is_applicable(user, instance, executions)


class EmptySerializer(serializers.Serializer):
    """An empty serializer, useful for endpoints that do not require any input or output."""

    class Meta:
        """Metaclass defines serializer fields."""

        fields = []
        model = GuideDefinition
