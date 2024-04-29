"""API serializers for the reporting models."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

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


class LabelTemplateSerializer(ReportSerializerBase):
    """Serializer class for label template model."""

    class Meta:
        """Metaclass options."""

        model = report.models.LabelTemplate
        fields = [*ReportSerializerBase().base_fields(), 'width', 'height']


class LabelOutputSerializer(InvenTreeModelSerializer):
    """Serializer class for the LabelOutput model."""

    class Meta:
        """Metaclass options."""

        model = report.models.LabelOutput
        fields = ['pk', 'created', 'user', 'complete', 'progress', 'output', 'template']

    template = InvenTreeAttachmentSerializerField()


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
