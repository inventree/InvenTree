"""Admin-facing API for managing the SCIM provisioning configuration."""

import structlog
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

import InvenTree.permissions
from scim.models import ScimConfiguration
from scim.serializers import ScimConfigurationSerializer, ScimSecretSerializer

logger = structlog.get_logger('inventree')


class ScimConfigViewSet(viewsets.GenericViewSet):
    """Admin viewset for managing the (singleton) SCIM provisioning configuration."""

    permission_classes = [InvenTree.permissions.IsSuperuserOrSuperScope]
    serializer_class = ScimConfigurationSerializer

    def get_object(self) -> ScimConfiguration:
        """Return the (singleton) SCIM configuration object."""
        return ScimConfiguration.load()

    def list(self, request, *args, **kwargs):
        """Return the current SCIM configuration status."""
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    @extend_schema(request=None, responses={200: ScimSecretSerializer()})
    @action(detail=False, methods=['post'], serializer_class=ScimSecretSerializer)
    def generate(self, request, *args, **kwargs):
        """Generate a new SCIM bearer secret, and enable the endpoint.

        The raw secret is returned exactly once in this response - only its
        HMAC digest is persisted. Generating a new secret invalidates any
        previously issued one.
        """
        config = self.get_object()
        secret = config.generate_secret()
        config.enabled = True
        config.save()

        logger.info('SCIM bearer secret (re)generated', user=str(request.user))

        serializer = self.get_serializer({'secret': secret})
        return Response(serializer.data)

    @extend_schema(request=None, responses={200: ScimConfigurationSerializer()})
    @action(detail=False, methods=['post'])
    def disable(self, request, *args, **kwargs):
        """Disable the SCIM provisioning endpoint and revoke its secret."""
        config = self.get_object()
        config.revoke()

        logger.info('SCIM provisioning disabled', user=str(request.user))

        serializer = ScimConfigurationSerializer(
            config, context=self.get_serializer_context()
        )
        return Response(serializer.data)
