"""DRF API definition for the 'users' app."""

import datetime

from django.contrib.auth import get_user, login
from django.contrib.auth.models import Group, User
from django.urls import include, path, re_path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic.base import RedirectView

import structlog
from rest_framework import exceptions, permissions
from rest_framework.generics import DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

import InvenTree.helpers
import InvenTree.permissions
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import (
    ListAPI,
    ListCreateAPI,
    RetrieveAPI,
    RetrieveUpdateAPI,
    RetrieveUpdateDestroyAPI,
)
from InvenTree.serializers import (
    ExtendedUserSerializer,
    MeUserSerializer,
    UserCreateSerializer,
)
from InvenTree.settings import FRONTEND_URL_BASE
from users.models import ApiToken, Owner
from users.serializers import (
    ApiTokenSerializer,
    GroupSerializer,
    OwnerSerializer,
    RoleSerializer,
)

logger = structlog.get_logger('inventree')


class OwnerList(ListAPI):
    """List API endpoint for Owner model.

    Cannot create.
    """

    queryset = Owner.objects.all()
    serializer_class = OwnerSerializer

    def filter_queryset(self, queryset):
        """Implement text search for the "owner" model.

        Note that an "owner" can be either a group, or a user,
        so we cannot do a direct text search.

        A "hack" here is to post-process the queryset and simply
        remove any values which do not match.

        It is not necessarily "efficient" to do it this way,
        but until we determine a better way, this is what we have...
        """
        search_term = str(self.request.query_params.get('search', '')).lower()
        is_active = self.request.query_params.get('is_active', None)

        queryset = super().filter_queryset(queryset)

        results = []

        # Get a list of all matching users, depending on the *is_active* flag
        if is_active is not None:
            is_active = InvenTree.helpers.str2bool(is_active)
            matching_user_ids = User.objects.filter(is_active=is_active).values_list(
                'pk', flat=True
            )

        for result in queryset.all():
            name = str(result.name()).lower().strip()
            search_match = True

            # Extract search term f
            if search_term:
                for entry in search_term.strip().split(' '):
                    if entry not in name:
                        search_match = False
                        break

            if not search_match:
                continue

            if is_active is not None:
                # Skip any users which do not match the required *is_active* value
                if (
                    result.owner_type.name == 'user'
                    and result.owner_id not in matching_user_ids
                ):
                    continue

            # If we get here, there is no reason *not* to include this result
            results.append(result)

        return results


class OwnerDetail(RetrieveAPI):
    """Detail API endpoint for Owner model.

    Cannot edit or delete
    """

    queryset = Owner.objects.all()
    serializer_class = OwnerSerializer


class RoleDetails(RetrieveAPI):
    """API endpoint which lists the available role permissions for the current user."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RoleSerializer

    def get_object(self):
        """Overwritten to always return current user."""
        return self.request.user


class UserDetail(RetrieveUpdateDestroyAPI):
    """Detail endpoint for a single user."""

    queryset = User.objects.all()
    serializer_class = ExtendedUserSerializer
    permission_classes = [permissions.IsAuthenticated]


class MeUserDetail(RetrieveUpdateAPI, UserDetail):
    """Detail endpoint for current user."""

    serializer_class = MeUserSerializer

    rolemap = {'POST': 'view', 'PUT': 'view', 'PATCH': 'view'}

    def get_object(self):
        """Always return the current user object."""
        return self.request.user

    def get_permission_model(self):
        """Return the model for the permission check.

        Note that for this endpoint, the current user can *always* edit their own details.
        """
        return None


class UserList(ListCreateAPI):
    """List endpoint for detail on all users."""

    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        InvenTree.permissions.IsSuperuserOrReadOnly,
    ]
    filter_backends = SEARCH_ORDER_FILTER

    search_fields = ['first_name', 'last_name', 'username']

    ordering_fields = [
        'email',
        'username',
        'first_name',
        'last_name',
        'is_staff',
        'is_superuser',
        'is_active',
    ]

    filterset_fields = ['is_staff', 'is_active', 'is_superuser']


class GroupMixin:
    """Mixin for Group API endpoints to add permissions filter."""

    def get_serializer(self, *args, **kwargs):
        """Return serializer instance for this endpoint."""
        # Do we wish to include extra detail?
        params = self.request.query_params
        kwargs['permission_detail'] = InvenTree.helpers.str2bool(
            params.get('permission_detail', None)
        )
        kwargs['context'] = self.get_serializer_context()
        return self.serializer_class(*args, **kwargs)


class GroupDetail(GroupMixin, RetrieveUpdateDestroyAPI):
    """Detail endpoint for a particular auth group."""

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupList(GroupMixin, ListCreateAPI):
    """List endpoint for all auth groups."""

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = SEARCH_ORDER_FILTER

    search_fields = ['name']

    ordering_fields = ['name']


class GetAuthToken(APIView):
    """Return authentication token for an authenticated user."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = None

    def get(self, request, *args, **kwargs):
        """Return an API token if the user is authenticated.

        - If the user already has a matching token, delete it and create a new one
        - Existing tokens are *never* exposed again via the API
        - Once the token is provided, it can be used for auth until it expires
        """
        if request.user.is_authenticated:
            user = request.user
            name = request.query_params.get('name', '')

            name = ApiToken.sanitize_name(name)

            today = datetime.date.today()

            # Find existing token, which has not expired
            token = ApiToken.objects.filter(
                user=user, name=name, revoked=False, expiry__gte=today
            ).first()

            if not token:
                # User is authenticated, and requesting a token against the provided name.
                token = ApiToken.objects.create(user=request.user, name=name)

                logger.info(
                    "Created new API token for user '%s' (name='%s')",
                    user.username,
                    name,
                )

            # Add some metadata about the request
            token.set_metadata('user_agent', request.headers.get('user-agent', ''))
            token.set_metadata('remote_addr', request.META.get('REMOTE_ADDR', ''))
            token.set_metadata('remote_host', request.META.get('REMOTE_HOST', ''))
            token.set_metadata('remote_user', request.META.get('REMOTE_USER', ''))
            token.set_metadata('server_name', request.META.get('SERVER_NAME', ''))
            token.set_metadata('server_port', request.META.get('SERVER_PORT', ''))

            data = {'token': token.key, 'name': token.name, 'expiry': token.expiry}

            # Ensure that the users session is logged in (PUI -> CUI login)
            if not get_user(request).is_authenticated:
                login(request, user)

            return Response(data)

        else:
            raise exceptions.NotAuthenticated()  # pragma: no cover


class TokenListView(DestroyAPIView, ListAPI):
    """List of registered tokens for current users."""

    permission_classes = (IsAuthenticated,)
    serializer_class = ApiTokenSerializer

    def get_queryset(self):
        """Only return data for current user."""
        return ApiToken.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        """Revoke token."""
        instance.revoked = True
        instance.save()


class LoginRedirect(RedirectView):
    """Redirect to the correct starting page after backend login."""

    def get_redirect_url(self, *args, **kwargs):
        """Return the URL to redirect to."""
        return f'/{FRONTEND_URL_BASE}/logged-in/'


user_urls = [
    path('roles/', RoleDetails.as_view(), name='api-user-roles'),
    path('token/', ensure_csrf_cookie(GetAuthToken.as_view()), name='api-token'),
    path(
        'tokens/',
        include([
            path('<int:pk>/', TokenListView.as_view(), name='api-token-detail'),
            path('', TokenListView.as_view(), name='api-token-list'),
        ]),
    ),
    path('me/', MeUserDetail.as_view(), name='api-user-me'),
    path(
        'owner/',
        include([
            path('<int:pk>/', OwnerDetail.as_view(), name='api-owner-detail'),
            path('', OwnerList.as_view(), name='api-owner-list'),
        ]),
    ),
    path(
        'group/',
        include([
            re_path(
                r'^(?P<pk>[0-9]+)/?$', GroupDetail.as_view(), name='api-group-detail'
            ),
            path('', GroupList.as_view(), name='api-group-list'),
        ]),
    ),
    re_path(r'^(?P<pk>[0-9]+)/?$', UserDetail.as_view(), name='api-user-detail'),
    path('', UserList.as_view(), name='api-user-list'),
]
