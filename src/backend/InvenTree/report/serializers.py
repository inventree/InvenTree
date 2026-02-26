"""API serializers for the reporting models."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

import plugin.serializers
import report.helpers
import report.models
from InvenTree.serializers import (
    InvenTreeAttachmentSerializerField,
    InvenTreeModelSerializer,
)


class ReportSerializerBase(InvenTreeModelSerializer):
    """Base serializer class for report and label templates."""

    def __init__(self, *args, **kwargs):
        """Override the constructor for the ReportSerializerBase.

        The primary goal here is to ensure that the 'choices' attribute
        is set correctly for the 'model_type' field.
        """
        super().__init__(*args, **kwargs)

        if len(self.fields['model_type'].choices) == 0:
            self.fields['model_type'].choices = report.helpers.report_model_options()

    @staticmethod
    def base_fields():
        """Base serializer field set."""
        return [
            'pk',
            'name',
            'description',
            'model_type',
            'template',
            'filters',
            'filename_pattern',
            'enabled',
            'revision',
            'attach_to_model',
        ]

    template = InvenTreeAttachmentSerializerField(required=True)

    revision = serializers.IntegerField(read_only=True)

    # Note: The choices are overridden at run-time
    model_type = serializers.ChoiceField(
        label=_('Model Type'),
        choices=report.helpers.report_model_options(),
        required=True,
        allow_blank=False,
        allow_null=False,
    )


class ReportTemplateSerializer(ReportSerializerBase):
    """Serializer class for report template model."""

    class Meta:
        """Metaclass options."""

        model = report.models.ReportTemplate
        fields = [
            *ReportSerializerBase.base_fields(),
            'page_size',
            'landscape',
            'merge',
        ]

    page_size = serializers.ChoiceField(
        required=False,
        default=report.helpers.report_page_size_default(),
        choices=report.helpers.report_page_size_options(),
    )


class ReportPrintSerializer(serializers.Serializer):
    """Serializer class for printing a report."""

    class Meta:
        """Metaclass options."""

        fields = ['template', 'items']

    template = serializers.PrimaryKeyRelatedField(
        queryset=report.models.ReportTemplate.objects.all(),
        many=False,
        required=True,
        allow_null=False,
        label=_('Template'),
        help_text=_('Select report template'),
    )

    items = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        allow_empty=False,
        label=_('Items'),
        help_text=_('List of item primary keys to include in the report'),
    )


class LabelPrintSerializer(serializers.Serializer):
    """Serializer class for printing a label."""

    # List of extra plugin field names
    plugin_fields = []

    class Meta:
        """Metaclass options."""

        fields = ['template', 'items', 'plugin']

    def __init__(self, *args, **kwargs):
        """Override the constructor to add the extra plugin fields."""
        # Reset to a known state
        self.Meta.fields = ['template', 'items', 'plugin']

        if plugin_serializer := kwargs.pop('plugin_serializer', None):
            for key, field in plugin_serializer.fields.items():
                self.Meta.fields.append(key)
                setattr(self, key, field)

        super().__init__(*args, **kwargs)

    template = serializers.PrimaryKeyRelatedField(
        queryset=report.models.LabelTemplate.objects.all(),
        many=False,
        required=True,
        allow_null=False,
        label=_('Template'),
        help_text=_('Select label template'),
    )

    # Plugin field - note that we use the 'key' (not the pk) for lookup
    plugin = plugin.serializers.PluginRelationSerializer(
        many=False,
        required=False,
        allow_null=False,
        label=_('Printing Plugin'),
        help_text=_('Select plugin to use for label printing'),
    )

    items = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        allow_empty=False,
        label=_('Items'),
        help_text=_('List of item primary keys to include in the report'),
    )


class LabelTemplateSerializer(ReportSerializerBase):
    """Serializer class for label template model."""

    class Meta:
        """Metaclass options."""

        model = report.models.LabelTemplate
        fields = [*ReportSerializerBase.base_fields(), 'width', 'height']


class ReportSnippetSerializer(InvenTreeModelSerializer):
    """Serializer class for the ReportSnippet model."""

    class Meta:
        """Metaclass options."""

        model = report.models.ReportSnippet

        fields = ['pk', 'snippet', 'description']

    snippet = InvenTreeAttachmentSerializerField()


class ReportAssetSerializer(InvenTreeModelSerializer):
    """Serializer class for the ReportAsset model."""

    class Meta:
        """Meta class options."""

        model = report.models.ReportAsset
        fields = ['pk', 'asset', 'description']

    asset = InvenTreeAttachmentSerializerField()
