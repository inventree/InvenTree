"""Serializers for UI plugin api."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class PluginPanelSerializer(serializers.Serializer):
    """Serializer for a plugin panel."""

    class Meta:
        """Meta for serializer."""

        fields = [
            'plugin',
            'name',
            'label',
            # Following fields are optional
            'icon',
            'content',
            'context',
            'source',
        ]

    # Required fields
    plugin = serializers.CharField(
        label=_('Plugin Key'), required=True, allow_blank=False
    )

    name = serializers.CharField(
        label=_('Panel Name'), required=True, allow_blank=False
    )

    label = serializers.CharField(
        label=_('Panel Title'), required=True, allow_blank=False
    )

    # Optional fields
    icon = serializers.CharField(
        label=_('Panel Icon'), required=False, allow_blank=True
    )

    content = serializers.CharField(
        label=_('Panel Content (HTML)'), required=False, allow_blank=True
    )

    context = serializers.JSONField(
        label=_('Panel Context (JSON)'), required=False, allow_null=True, default=None
    )

    source = serializers.CharField(
        label=_('Panel Source (javascript)'), required=False, allow_blank=True
    )


class PluginUIFeatureSerializer(serializers.Serializer):
    """Serializer for a plugin ui feature."""

    class Meta:
        """Meta for serializer."""

        fields = ['feature_type', 'options', 'source']

    # Required fields
    feature_type = serializers.CharField(
        label=_('Feature Type'), required=True, allow_blank=False
    )

    options = serializers.DictField(label=_('Feature Options'), required=True)

    source = serializers.CharField(
        label=_('Feature Source (javascript)'), required=True, allow_blank=False
    )
