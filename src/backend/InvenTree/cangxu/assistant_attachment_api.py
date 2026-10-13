"""Session-authenticated private upload/download and service-only model extraction."""

import hmac

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema
from rest_framework import serializers, viewsets
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.authentication import ApiTokenAuthentication

from .assistant_api import (
    AssistantRequestConflict,
    _current_binding,
    _ensure_selected_binding,
    _no_wildcard,
    _selected_partner_id,
)
from .assistant_attachment_models import AssistantChatAttachment
from .assistant_attachments import (
    attachment_metadata,
    create_upload,
    model_attachment_content,
)
from .assistant_gateway import DeliveryConflictError, runtime_config
from .assistant_models import PartnerBinding


class UploadRequestSerializer(serializers.Serializer):
    """Stable upload identity and one bounded file."""

    client_upload_id = serializers.CharField(max_length=200, validators=[_no_wildcard])
    file = serializers.FileField()


class AssistantAttachmentViewSet(viewsets.ViewSet):
    """Files are always owned by the caller's partner; no public storage URLs."""

    authentication_classes = [
        ApiTokenAuthentication,
        BasicAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    lookup_value_regex = '[0-9a-f-]{36}'

    @extend_schema(request=UploadRequestSerializer, responses={201: dict, 200: dict})
    def create(self, request):
        """Persist an image or document without a second authorization flow."""
        serializer = UploadRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from .assistant_api import _runtime_or_503

        _runtime_or_503()
        binding = _ensure_selected_binding(request)
        if not binding.enabled or not request.user.is_active:
            raise PermissionDenied('This partner is disabled')
        try:
            item, created = create_upload(
                binding,
                serializer.validated_data['file'],
                serializer.validated_data['client_upload_id'],
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        except DeliveryConflictError as exc:
            raise AssistantRequestConflict() from exc
        return Response(attachment_metadata(item), status=201 if created else 200)

    def _owned(self, request, pk):
        binding = _current_binding(request.user, _selected_partner_id(request))
        if not binding or not binding.enabled or not request.user.is_active:
            raise PermissionDenied('This partner is unavailable')
        return get_object_or_404(AssistantChatAttachment, binding=binding, pk=pk)

    @extend_schema(responses={204: None, 409: dict})
    def destroy(self, request, pk=None):
        """Remove unused drafts; submitted conversation evidence stays intact."""
        from django.db import transaction

        with transaction.atomic():
            item = self._owned(request, pk)
            PartnerBinding.objects.select_for_update().get(pk=item.binding_id)
            item.refresh_from_db()
            if item.submitted_at is not None:
                return Response(
                    {
                        'error': 'Submitted conversation attachments cannot be removed as drafts'
                    },
                    status=409,
                )
            storage, name = item.file.storage, item.file.name
            item.delete()
            transaction.on_commit(lambda: storage.delete(name))
        return Response(status=204)

    @extend_schema(responses=dict)
    def retrieve(self, request, pk=None):
        """Return metadata only for the caller's own upload."""
        return Response(attachment_metadata(self._owned(request, pk)))

    @extend_schema(responses={'200': {'type': 'string', 'format': 'binary'}})
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Stream an original through authentication, never redirect to public media."""
        item = self._owned(request, pk)
        response = FileResponse(
            item.file.open('rb'),
            as_attachment=True,
            filename=item.name,
            content_type=item.mime_type,
        )
        response['Cache-Control'] = 'private, no-store'
        response['X-Content-Type-Options'] = 'nosniff'
        return response

    @extend_schema(responses={'200': {'type': 'string', 'format': 'binary'}})
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """Only validated raster images may render inline."""
        item = self._owned(request, pk)
        if item.kind != 'image':
            raise serializers.ValidationError(
                'Inline preview is available for images only'
            )
        response = FileResponse(
            item.file.open('rb'),
            as_attachment=False,
            filename=item.name,
            content_type=item.mime_type,
        )
        response['Cache-Control'] = 'private, no-store'
        response['X-Content-Type-Options'] = 'nosniff'
        response['Content-Security-Policy'] = "default-src 'none'; sandbox"
        return response


class AssistantInternalAttachmentView(APIView):
    """Model input is fetched only under service identity and matching partner."""

    authentication_classes = []
    permission_classes = []

    @extend_schema(exclude=True)
    def get(self, request, attachment_id):
        """Recheck current user/binding before bounded extraction."""
        config = runtime_config()
        if config is None or not hmac.compare_digest(
            request.headers.get('Authorization', ''), f'Bearer {config.token}'
        ):
            return Response({'error': 'Invalid assistant service identity'}, status=401)
        if request.headers.get('X-Assistant-Deployment') != config.deployment_id:
            return Response({'error': 'Assistant deployment mismatch'}, status=403)
        partner_serializer = serializers.UUIDField()
        partner_id = partner_serializer.run_validation(
            request.query_params.get('partner_id')
        )
        binding = get_object_or_404(
            PartnerBinding,
            deployment_id=config.deployment_id,
            partner_id=partner_id,
            enabled=True,
            user__is_active=True,
        )
        item = get_object_or_404(
            AssistantChatAttachment, pk=attachment_id, binding=binding
        )
        try:
            return Response(model_attachment_content(item))
        except (DjangoValidationError, OSError):
            return Response(
                {
                    'error': 'Attachment content is unavailable or failed integrity verification'
                },
                status=409,
            )
