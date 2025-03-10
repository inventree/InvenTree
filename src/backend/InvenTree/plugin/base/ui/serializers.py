"""Serializers for UI plugin api."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class PluginUIFeatureSerializer(serializers.Serializer):
    """Serializer for a plugin ui feature."""

    class Meta:
        """Meta for serializer."""

        fields = [
            'plugin_name',
            'feature_type',
            'key',
            'title',
            'description',
            'icon',
            'options',
            'context',
            'source',
        ]

    # Required fields

    # The name of the plugin that provides this feature
    plugin_name = serializers.CharField(
        label=_('Plugin Name'), required=True, allow_blank=False
    )

    feature_type = serializers.CharField(
        label=_('Feature Type'), required=True, allow_blank=False
    )

    # Item key to be used in the UI - this should be a DOM identifier and is not user facing
    key = serializers.CharField(
        label=_('Feature Label'), required=True, allow_blank=False
    )

    # Title to be used in the UI - this is user facing (and should be human readable)
    title = serializers.CharField(
        label=_('Feature Title'), required=False, allow_blank=True
    )

    # Long-form description of the feature (optional)
    description = serializers.CharField(
        label=_('Feature Description'), required=False, allow_blank=True
    )

    # Optional icon
    icon = serializers.CharField(
        label=_('Feature Icon'), required=False, allow_blank=True
    )

    # Additional options, specific to the particular UI feature
    options = serializers.DictField(label=_('Feature Options'), default=None)

    # Server side context, supplied to the client side for rendering
    context = serializers.DictField(label=_('Feature Context'), default=None)

    source = serializers.CharField(
        label=_('Feature Source (javascript)'), required=True, allow_blank=False
    )
