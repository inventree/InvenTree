"""Service bridge for model-callable APIs under the existing application identity."""

import hmac

from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from InvenTree.config import get_setting

from .assistant_business_tools import (
    business_action,
    business_capabilities,
    business_query,
)
from .assistant_knowledge import workflow_knowledge
from .assistant_models import PartnerBinding
from .assistant_services import CommandConflictError


class BusinessToolRequestSerializer(serializers.Serializer):
    """The model can select only tools and data, never identity or arbitrary routes."""

    partner_id = serializers.UUIDField()
    tool = serializers.ChoiceField(
        choices=[
            'business_query',
            'business_action',
            'business_capabilities',
            'workflow_knowledge',
        ]
    )
    arguments = serializers.JSONField(default=dict)
    command_id = serializers.CharField(max_length=200)
    run_id = serializers.CharField(max_length=200)
    step_id = serializers.CharField(max_length=200)

    def validate(self, attrs):
        """Keep protocol and nested input sizes explicit."""
        if set(self.initial_data) - set(self.fields) or not isinstance(
            attrs['arguments'], dict
        ):
            raise serializers.ValidationError('Unexpected tool protocol fields')
        return attrs


class AssistantBusinessToolsView(APIView):
    """Resolve the user's binding server-side; original APIs enforce business rights."""

    authentication_classes = []
    permission_classes = []

    @extend_schema(exclude=True)
    def post(self, request):
        """Execute a fixed tool contract without a separate grant step."""
        token = get_setting(
            'ASSISTANT_RUNTIME_TOKEN', 'assistant_runtime_token', '', typecast=str
        )
        deployment = get_setting(
            'ASSISTANT_DEPLOYMENT_ID', 'assistant_deployment_id', '', typecast=str
        )
        if len(token) < 32 or not hmac.compare_digest(
            request.headers.get('Authorization', ''), f'Bearer {token}'
        ):
            return Response(
                {'status': 'failed', 'error': 'Invalid assistant service identity'},
                status=401,
            )
        if (
            not deployment
            or request.headers.get('X-Assistant-Deployment') != deployment
        ):
            return Response(
                {'status': 'failed', 'error': 'Assistant deployment mismatch'},
                status=403,
            )
        if len(request.body) > 65536:
            return Response(
                {'status': 'failed', 'error': 'Tool request is too large'}, status=413
            )
        serializer = BusinessToolRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        try:
            binding = PartnerBinding.objects.get(
                deployment_id=deployment, partner_id=payload['partner_id']
            )
            if not binding.enabled or not binding.user.is_active:
                raise DjangoPermissionDenied(
                    'Application user or assistant is disabled'
                )
            if payload['tool'] == 'business_query':
                result = business_query(binding, payload['arguments'])
            elif payload['tool'] == 'business_action':
                result = business_action(binding, payload)
            elif payload['tool'] == 'business_capabilities':
                if payload['arguments']:
                    raise ValueError('Capabilities accepts no arguments')
                result = business_capabilities(binding)
            else:
                result = workflow_knowledge(payload['arguments'])
        except ObjectDoesNotExist:
            return Response(
                {'status': 'failed', 'error': 'Business reference is unavailable'},
                status=404,
            )
        except DjangoPermissionDenied:
            return Response(
                {
                    'status': 'failed',
                    'error': 'Current application permission does not allow this action',
                },
                status=403,
            )
        except CommandConflictError:
            return Response(
                {
                    'status': 'failed',
                    'error': 'The command key identifies a different action',
                },
                status=409,
            )
        except (DjangoValidationError, ValueError) as exc:
            return Response(
                {'status': 'failed', 'error': getattr(exc, 'messages', [str(exc)])},
                status=400,
            )
        return Response(result)
