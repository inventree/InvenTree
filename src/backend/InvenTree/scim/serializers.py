"""DRF serializers for the SCIM admin configuration API."""

from django.urls import reverse

from rest_framework import serializers

from scim.models import ScimConfiguration


class ScimConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for the (read-only, status-only) SCIM configuration."""

    class Meta:
        """Metaclass options."""

        model = ScimConfiguration
        fields = ['enabled', 'has_secret', 'secret_generated', 'last_used', 'base_url']
        read_only_fields = fields

    has_secret = serializers.BooleanField(read_only=True)

    base_url = serializers.SerializerMethodField()

    def get_base_url(self, obj) -> str:
        """Return the absolute base URL that should be configured in the Identity Provider."""
        request = self.context.get('request')
        path = reverse('scim-service-provider-config').rsplit(
            'ServiceProviderConfig', 1
        )[0]

        if request is not None:
            return request.build_absolute_uri(path)
        return path  # pragma: no cover


class ScimSecretSerializer(serializers.Serializer):
    """Serializer for a freshly (re)generated SCIM bearer secret.

    This is the *only* place the raw secret is ever exposed - it cannot be
    retrieved again afterwards.
    """

    secret = serializers.CharField(read_only=True)
    base_url = serializers.SerializerMethodField()

    def get_base_url(self, obj) -> str:
        """Return the absolute base URL that should be configured in the Identity Provider."""
        request = self.context.get('request')
        path = reverse('scim-service-provider-config').rsplit(
            'ServiceProviderConfig', 1
        )[0]

        if request is not None:
            return request.build_absolute_uri(path)
        return path  # pragma: no cover
