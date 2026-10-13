"""Service-only receipt tools, with server-resolved identity and bounded schemas."""

import hmac
import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError

from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from InvenTree.config import get_setting

from .assistant_models import PartnerBinding
from .assistant_services import CommandConflictError
from .assistant_tools import run_receipt_tool


class ReceiptToolRequestSerializer(serializers.Serializer):
    """Only bounded tool-specific inputs reach the internal dispatcher."""

    partner_id = serializers.UUIDField()
    grant_id = serializers.IntegerField(min_value=1)
    grant_version = serializers.IntegerField(min_value=1)
    tool = serializers.ChoiceField(choices=['receipt_status', 'link_receipt_archive'])
    object_id = serializers.CharField(max_length=100)
    command_id = serializers.CharField(max_length=200, required=False)
    run_id = serializers.CharField(max_length=200, required=False)
    step_id = serializers.CharField(max_length=200, required=False)
    args = serializers.JSONField(default=dict)

    def validate(self, attrs):
        """Reject incomplete writes and unknown top-level or domain arguments."""
        if set(self.initial_data) - set(self.fields):
            raise serializers.ValidationError('Unexpected internal tool fields')
        if not isinstance(attrs['args'], dict):
            raise serializers.ValidationError('Tool args must be an object')
        if attrs['tool'] == 'link_receipt_archive':
            if not all(attrs.get(key) for key in ('command_id', 'run_id', 'step_id')):
                raise serializers.ValidationError(
                    'Writes require stable command, run and step identifiers'
                )
            args = attrs['args']
            if (
                set(args) != {'attachment_id', 'kind'}
                or type(args['attachment_id']) is not int
                or args['attachment_id'] <= 0
            ):
                raise serializers.ValidationError(
                    'Provide an explicit positive attachment ID and kind'
                )
        elif attrs['args']:
            raise serializers.ValidationError(
                'Receipt query accepts no domain arguments'
            )
        return attrs


class AssistantInternalToolsView(APIView):
    """Accept only the configured runtime credential; never browser identity claims."""

    authentication_classes = []
    permission_classes = []

    @extend_schema(exclude=True)
    def post(self, request):
        """Resolve partner under the configured deployment and recheck business rights."""
        token = get_setting(
            'ASSISTANT_RUNTIME_TOKEN', 'assistant_runtime_token', '', typecast=str
        )
        deployment = get_setting(
            'ASSISTANT_DEPLOYMENT_ID', 'assistant_deployment_id', '', typecast=str
        )
        supplied = request.headers.get('Authorization', '')
        if len(token) < 32 or not hmac.compare_digest(supplied, f'Bearer {token}'):
            return Response(
                {'error': 'Invalid assistant service identity'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if (
            not deployment
            or request.headers.get('X-Assistant-Deployment') != deployment
        ):
            raise PermissionDenied('Assistant deployment mismatch')
        # DRF parsing is bounded by Django's request memory limit; enforce the
        # smaller internal protocol limit before evaluating nested payloads.
        if len(request.body) > 65536:
            return Response(
                {'error': 'Tool request is too large'},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )
        serializer = ReceiptToolRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            uuid.UUID(deployment)
            binding = PartnerBinding.objects.get(
                deployment_id=deployment, partner_id=data['partner_id']
            )
            result = run_receipt_tool(binding=binding, payload=data)
        except (ObjectDoesNotExist, ValueError):
            return Response(
                {'error': 'Business reference is unavailable'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(
                'Current business authority does not permit the action'
            ) from exc
        except CommandConflictError:
            return Response(
                {'error': 'Command key conflicts with an existing request'},
                status=status.HTTP_409_CONFLICT,
            )
        except DjangoValidationError as exc:
            return Response({'error': exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)
