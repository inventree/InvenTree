"""SCIM 2.0 protocol views (RFC7643 / RFC7644).

Implements the minimal set of endpoints required by common Identity
Providers (Okta, Microsoft Entra ID, OneLogin, ...) to provision Users and
Groups: discovery (ServiceProviderConfig / ResourceTypes / Schemas), and CRUD
+ PATCH on Users and Groups.
"""

from django.contrib.auth.models import Group as DjangoGroup
from django.contrib.auth.models import User as DjangoUser
from django.http import Http404
from django.shortcuts import get_object_or_404

import structlog
from pydantic import ValidationError
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
)
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from scim2_models import (
    AuthenticationScheme,
    Bulk,
    ChangePassword,
    Error,
    ETag,
    Filter,
    Group,
    ListResponse,
    Patch,
    PatchOp,
    ResourceType,
    Schema,
    ServiceProviderConfig,
    Sort,
    User,
)
from scim2_models.exceptions import SCIMException

from scim.authentication import ScimBearerAuthentication
from scim.permissions import IsScimAuthenticated
from scim.resources import (
    apply_scim_to_group,
    apply_scim_to_user,
    group_location,
    group_to_scim,
    parse_filter,
    set_group_members,
    user_location,
    user_to_scim,
)

logger = structlog.get_logger('inventree')


class ScimRenderer(JSONRenderer):
    """JSON renderer which advertises the `application/scim+json` media type."""

    media_type = 'application/scim+json'


class ScimParser(JSONParser):
    """JSON parser which also accepts the `application/scim+json` media type."""

    media_type = 'application/scim+json'


def scim_dump(obj) -> dict:
    """Serialize a scim2_models object to a plain (JSON-safe) dict."""
    return obj.model_dump(mode='json', exclude_none=True, by_alias=True)


def scim_error(status: int, detail: str, scim_type: str | None = None) -> Response:
    """Build a SCIM-formatted error response."""
    error = Error(status=status, scim_type=scim_type, detail=detail)
    return Response(
        scim_dump(error), status=status, content_type='application/scim+json'
    )


class ScimAPIView(APIView):
    """Base class for all SCIM protocol views.

    These endpoints follow the SCIM 2.0 protocol (not InvenTree's own REST
    API conventions) and authenticate via a bearer secret rather than any of
    InvenTree's normal authentication schemes - they are excluded from the
    OpenAPI schema entirely (`schema = None`) rather than being documented
    alongside the versioned `/api/` surface.
    """

    schema = None

    authentication_classes = [ScimBearerAuthentication]
    permission_classes = [IsScimAuthenticated]
    renderer_classes = [ScimRenderer]
    parser_classes = [ScimParser, JSONParser]

    def handle_exception(self, exc):
        """Convert SCIM/pydantic exceptions into RFC7644-formatted error responses."""
        if isinstance(exc, SCIMException):
            return scim_error(
                exc.status, exc.detail, exc.scim_type or None
            )  # pragma: no cover

        if isinstance(exc, ValidationError):
            return scim_error(400, str(exc), 'invalidValue')  # pragma: no cover

        if isinstance(exc, Http404):
            return scim_error(404, 'Resource not found')

        if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
            return scim_error(
                exc.status_code,
                str(exc.detail) if hasattr(exc, 'detail') else str(exc),
                None,
            )

        if isinstance(exc, APIException):  # pragma: no cover
            detail = exc.detail
            if isinstance(detail, (list, dict)):
                detail = str(detail)
            return scim_error(exc.status_code, str(detail), None)
        return super().handle_exception(exc)  # pragma: no cover


class ScimNotFoundView(ScimAPIView):
    """Return a SCIM Error object for routes that are not part of the SCIM surface."""

    authentication_classes = []
    permission_classes = []

    def dispatch(self, request, *args, **kwargs):
        """Always return a SCIM-formatted 404 error, rather than a Django 404 page."""
        return scim_error(404, f"Resource '{request.path}' not found")


class ServiceProviderConfigView(ScimAPIView):
    """Advertise the SCIM features supported by this service provider."""

    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        """Return the service provider configuration."""
        config = ServiceProviderConfig(
            documentation_uri='https://docs.inventree.org/en/latest/settings/scim/',
            patch=Patch(supported=True),
            bulk=Bulk(supported=False, max_operations=0, max_payload_size=0),
            filter=Filter(supported=True, max_results=200),
            change_password=ChangePassword(supported=False),
            sort=Sort(supported=False),
            etag=ETag(supported=False),
            authentication_schemes=[
                AuthenticationScheme(
                    type=AuthenticationScheme.Type.oauthbearertoken,
                    name='Bearer Token',
                    description='Authentication using a single admin-generated bearer secret',
                )
            ],
        )
        return Response(scim_dump(config), content_type='application/scim+json')


class ResourceTypesView(ScimAPIView):
    """List the resource types supported by this service provider."""

    authentication_classes = []
    permission_classes = []

    resource_types = {
        'User': ResourceType(
            id='User',
            name='User',
            endpoint='/scim/v2/Users',
            description='User Account',
            schema_='urn:ietf:params:scim:schemas:core:2.0:User',
        ),
        'Group': ResourceType(
            id='Group',
            name='Group',
            endpoint='/scim/v2/Groups',
            description='Group',
            schema_='urn:ietf:params:scim:schemas:core:2.0:Group',
        ),
    }

    def get(self, request, name=None, *args, **kwargs):
        """Return either a single resource type, or the full list."""
        if name:
            resource_type = self.resource_types.get(name)
            if not resource_type:
                return scim_error(404, f"ResourceType '{name}' not found")
            return Response(
                scim_dump(resource_type), content_type='application/scim+json'
            )

        resources = list(self.resource_types.values())
        response = ListResponse[ResourceType](
            total_results=len(resources),
            items_per_page=len(resources),
            start_index=1,
            resources=resources,
        )
        return Response(scim_dump(response), content_type='application/scim+json')


class SchemasView(ScimAPIView):
    """Expose the SCIM schema definitions for the supported resource types."""

    authentication_classes = []
    permission_classes = []

    def get(self, request, schema_id=None, *args, **kwargs):
        """Return either a single schema, or the full list."""
        schemas = {
            schema.id: schema for schema in (User.to_schema(), Group.to_schema())
        }

        if schema_id:
            schema = schemas.get(schema_id)
            if not schema:
                return scim_error(404, f"Schema '{schema_id}' not found")
            return Response(scim_dump(schema), content_type='application/scim+json')

        resources = list(schemas.values())
        response = ListResponse[Schema](
            total_results=len(resources),
            items_per_page=len(resources),
            start_index=1,
            resources=resources,
        )
        return Response(scim_dump(response), content_type='application/scim+json')


class BaseResourceView(ScimAPIView):
    """Shared list/create logic for the Users and Groups endpoints."""

    django_model = None
    scim_model = None
    filterable_fields = {}

    def get_queryset(self):
        """Return the base queryset for this resource type."""
        return self.django_model.objects.all().order_by('pk')

    def to_scim(self, instance):
        """Convert a Django model instance into its SCIM representation. Implemented by subclasses."""
        raise NotImplementedError  # pragma: no cover

    def list(self, request):
        """Handle GET (list) requests, with minimal filter and pagination support."""
        queryset = self.get_queryset()

        parsed_filter = parse_filter(request.query_params.get('filter'))
        if parsed_filter:
            attr, value = parsed_filter
            field = self.filterable_fields.get(attr)
            if field is None:
                return scim_error(
                    400, f"Filtering on '{attr}' is not supported", 'invalidFilter'
                )
            queryset = queryset.filter(**{field: value})

        start_index = max(int(request.query_params.get('startIndex', 1)), 1)
        count = int(request.query_params.get('count', 100))

        total_results = queryset.count()
        page = queryset[start_index - 1 : start_index - 1 + count]
        resources = [self.to_scim(obj) for obj in page]

        response = ListResponse[self.scim_model](
            total_results=total_results,
            items_per_page=len(resources),
            start_index=start_index,
            resources=resources,
        )
        return Response(scim_dump(response), content_type='application/scim+json')


class UsersView(BaseResourceView):
    """`/scim/v2/Users` - list and create Users."""

    django_model = DjangoUser
    scim_model = User
    filterable_fields = {'username': 'username__iexact', 'useremail': 'email__iexact'}

    def get(self, request, *args, **kwargs):
        """List users."""
        return self.list(request)

    def to_scim(self, instance):
        """Convert a Django User into its SCIM representation."""
        return user_to_scim(instance)

    def post(self, request, *args, **kwargs):
        """Provision a new user."""
        scim_user = User.model_validate(request.data)

        if DjangoUser.objects.filter(username__iexact=scim_user.user_name).exists():
            return scim_error(
                409, 'A user with this userName already exists', 'uniqueness'
            )  # pragma: no cover

        user = DjangoUser(username=scim_user.user_name)
        user.set_unusable_password()
        apply_scim_to_user(scim_user, user)
        user.save()

        logger.info('SCIM: provisioned new user', username=user.username)

        return Response(
            scim_dump(user_to_scim(user)),
            status=201,
            content_type='application/scim+json',
            headers={'Location': user_location(user.pk)},
        )


class UserDetailView(ScimAPIView):
    """`/scim/v2/Users/<id>` - retrieve, replace, patch and remove a single User."""

    def get_object(self, pk):
        """Look up a user by primary key, raising a SCIM-formatted 404 if not found."""
        return get_object_or_404(DjangoUser, pk=pk)

    def get(self, request, pk, *args, **kwargs):
        """Retrieve a single user."""
        user = self.get_object(pk)
        return Response(
            scim_dump(user_to_scim(user)), content_type='application/scim+json'
        )

    def put(self, request, pk, *args, **kwargs):
        """Replace a user's attributes."""
        user = self.get_object(pk)
        scim_user = User.model_validate(request.data)
        apply_scim_to_user(scim_user, user)
        user.save()
        return Response(
            scim_dump(user_to_scim(user)), content_type='application/scim+json'
        )

    def patch(self, request, pk, *args, **kwargs):
        """Apply a SCIM PATCH operation set to a user."""
        user = self.get_object(pk)
        scim_user = user_to_scim(user)

        patch_op = PatchOp[User].model_validate(request.data)
        patch_op.patch(scim_user)

        apply_scim_to_user(scim_user, user)
        user.save()

        return Response(
            scim_dump(user_to_scim(user)), content_type='application/scim+json'
        )

    def delete(self, request, pk, *args, **kwargs):
        """Deactivate a user.

        Users are deactivated rather than deleted, to preserve historical
        ownership references (e.g. on stock items, orders, audit trails).
        """
        user = self.get_object(pk)
        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response(status=204)


class GroupsView(BaseResourceView):
    """`/scim/v2/Groups` - list and create Groups."""

    django_model = DjangoGroup
    scim_model = Group
    filterable_fields = {'displayname': 'name__iexact'}

    def get(self, request, *args, **kwargs):
        """List groups."""
        return self.list(request)

    def to_scim(self, instance):
        """Convert a Django Group into its SCIM representation."""
        return group_to_scim(instance)

    def post(self, request, *args, **kwargs):
        """Provision a new group."""
        scim_group = Group.model_validate(request.data)

        if DjangoGroup.objects.filter(name__iexact=scim_group.display_name).exists():
            return scim_error(
                409, 'A group with this displayName already exists', 'uniqueness'
            )  # pragma: no cover

        group = DjangoGroup(name=scim_group.display_name)
        group.save()
        set_group_members(group, scim_group.members)

        logger.info('SCIM: provisioned new group', name=group.name)

        return Response(
            scim_dump(group_to_scim(group)),
            status=201,
            content_type='application/scim+json',
            headers={'Location': group_location(group.pk)},
        )


class GroupDetailView(ScimAPIView):
    """`/scim/v2/Groups/<id>` - retrieve, replace, patch and remove a single Group."""

    def get_object(self, pk):
        """Look up a group by primary key, raising a SCIM-formatted 404 if not found."""
        return get_object_or_404(DjangoGroup, pk=pk)

    def get(self, request, pk, *args, **kwargs):
        """Retrieve a single group."""
        group = self.get_object(pk)
        return Response(
            scim_dump(group_to_scim(group)), content_type='application/scim+json'
        )

    def put(self, request, pk, *args, **kwargs):
        """Replace a group's attributes and membership."""
        group = self.get_object(pk)
        scim_group = Group.model_validate(request.data)
        apply_scim_to_group(scim_group, group)
        group.save()
        set_group_members(group, scim_group.members)
        return Response(
            scim_dump(group_to_scim(group)), content_type='application/scim+json'
        )

    def patch(self, request, pk, *args, **kwargs):
        """Apply a SCIM PATCH operation set to a group (used mainly for membership changes)."""
        group = self.get_object(pk)
        scim_group = group_to_scim(group)

        patch_op = PatchOp[Group].model_validate(request.data)
        patch_op.patch(scim_group)

        apply_scim_to_group(scim_group, group)
        group.save()
        set_group_members(group, scim_group.members)

        return Response(
            scim_dump(group_to_scim(group)), content_type='application/scim+json'
        )

    def delete(self, request, pk, *args, **kwargs):
        """Remove a group."""
        group = self.get_object(pk)
        group.delete()
        return Response(status=204)
