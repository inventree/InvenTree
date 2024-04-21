"""API serializers for the reporting models."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

import report.helpers
import report.models
from InvenTree.serializers import (
    InvenTreeAttachmentSerializerField,
    InvenTreeModelSerializer,
)


class ReportSerializer(InvenTreeModelSerializer):
    """Serializer class for report template model."""

    class Meta:
        """Metaclass options."""

        model = report.models.ReportTemplate
        fields = [
            'pk',
            'name',
            'description',
            'model_type',
            'template',
            'filters',
            'page_size',
            'landscape',
            'enabled',
        ]

    template = InvenTreeAttachmentSerializerField(required=True)

    page_size = serializers.ChoiceField(
        required=False,
        default=report.helpers.report_page_size_default(),
        choices=report.helpers.report_page_size_options(),
    )

    model_type = serializers.ChoiceField(
        label=_('Model Type'), choices=report.helpers.report_model_options()
    )


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
