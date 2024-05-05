"""API serializers for the reporting models."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

import plugin.models
import report.helpers
import report.models
from InvenTree.serializers import (
    InvenTreeAttachmentSerializerField,
    InvenTreeModelSerializer,
)


class ReportSerializerBase(InvenTreeModelSerializer):
    """Base serializer class for report and label templates."""

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
        ]

    template = InvenTreeAttachmentSerializerField(required=True)

    revision = serializers.IntegerField(read_only=True)

    model_type = serializers.ChoiceField(
        label=_('Model Type'), choices=report.helpers.report_model_options()
    )


class ReportTemplateSerializer(ReportSerializerBase):
    """Serializer class for report template model."""

    class Meta:
        """Metaclass options."""

        model = report.models.ReportTemplate
        fields = [*ReportSerializerBase.base_fields(), 'page_size', 'landscape']

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
                # self._declared_fields[key] = field
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

    plugin = serializers.PrimaryKeyRelatedField(
        queryset=plugin.models.PluginConfig.objects.all(),
        many=False,
        required=False,
        allow_null=True,
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
        fields = [*ReportSerializerBase().base_fields(), 'width', 'height']


class BaseOutputSerializer(InvenTreeModelSerializer):
    """Base serializer class for template output."""

    @staticmethod
    def base_fields():
        """Basic field set."""
        return [
            'pk',
            'created',
            'user',
            'model_type',
            'items',
            'complete',
            'progress',
            'output',
            'template',
        ]

    output = InvenTreeAttachmentSerializerField()
    model_type = serializers.CharField(source='template.model_type', read_only=True)


class LabelOutputSerializer(BaseOutputSerializer):
    """Serializer class for the LabelOutput model."""

    class Meta:
        """Metaclass options."""

        model = report.models.LabelOutput
        fields = [*BaseOutputSerializer.base_fields(), 'plugin']


class ReportOutputSerializer(BaseOutputSerializer):
    """Serializer class for the ReportOutput model."""

    class Meta:
        """Metaclass options."""

        model = report.models.ReportOutput
        fields = BaseOutputSerializer.base_fields()


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
