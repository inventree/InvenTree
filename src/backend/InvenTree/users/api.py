"""DRF API definition for the 'users' app."""

import datetime

from django.contrib.auth import get_user, login
from django.contrib.auth.models import Group, User
from django.contrib.auth.password_validation import password_changed, validate_password
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.urls import include, path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic.base import RedirectView

import django_filters.rest_framework.filters as rest_filters
import structlog
from django_filters.rest_framework.filterset import FilterSet
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import exceptions
from rest_framework.generics import DestroyAPIView, GenericAPIView
from rest_framework.response import Response

import InvenTree.permissions
from InvenTree.fields import InvenTreeOutputOption, OutputConfiguration
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import (
    ListAPI,
    ListCreateAPI,
    OutputOptionsMixin,
    RetrieveAPI,
    RetrieveUpdateAPI,
    RetrieveUpdateDestroyAPI,
    SerializerContextMixin,
    UpdateAPI,
)
from InvenTree.settings import FRONTEND_URL_BASE
from users.models import ApiToken, Owner, RuleSet, UserProfile
from users.serializers import (
    ApiTokenSerializer,
    ExtendedUserSerializer,
    GetAuthTokenSerializer,
    GroupSerializer,
    MeUserSerializer,
    OwnerSerializer,
    RoleSerializer,
    RuleSetSerializer,
    UserCreateSerializer,
    UserProfileSerializer,
    UserSetPasswordSerializer,
)

logger = structlog.get_logger('inventree')


class OwnerFilter(FilterSet):
    """filter set for OwnerList."""

    is_active = rest_filters.BooleanFilter(method='filter_is_active')

    class Meta:
        """Meta class for owner filter."""

        model = Owner
        fields = ['is_active']

    def filter_is_active(self, queryset, name, value):
        """Filter by active status."""
        if value is None:
            return queryset

        # Get ContentType for User model
        user_content_type = ContentType.objects.get_for_model(User)

        active_user_ids = list(
            User.objects.filter(is_active=value).values_list('pk', flat=True)
        )

        # Filter based on owner type
        q_filter = Q()

        # If owner_type is not 'user', include all
        q_filter |= ~Q(owner_type=user_content_type)

        # If owner_type is 'user', only include active/inactive users
        if active_user_ids:
            q_filter |= Q(owner_type=user_content_type, owner_id__in=active_user_ids)
        elif value is False:
            # If value is False and we want inactive users
            # Get all user IDs that are NOT in active_user_ids
            all_user_ids = list(User.objects.values_list('pk', flat=True))
            inactive_user_ids = [
                uid for uid in all_user_ids if uid not in active_user_ids
            ]
            if inactive_user_ids:
                q_filter |= Q(
                    owner_type=user_content_type, owner_id__in=inactive_user_ids
                )

        return queryset.filter(q_filter)


class OwnerList(ListAPI):
    """List API endpoint for Owner model.

    Cannot create a new Owner object via the API, but can view existing instances.
    """

    queryset = Owner.objects.all()
    serializer_class = OwnerSerializer
    permission_classes = [InvenTree.permissions.IsAuthenticatedOrReadScope]
    filterset_class = OwnerFilter
    filter_backends = SEARCH_ORDER_FILTER

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

        queryset = queryset.select_related('owner_type').prefetch_related('owner')
        queryset = super().filter_queryset(queryset)

        results = []

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

            # If we get here, there is no reason *not* to include this result
            results.append(result)

        return results


class OwnerDetail(RetrieveAPI):
    """Detail API endpoint for Owner model.

    Cannot edit or delete
    """

    queryset = Owner.objects.all()
    serializer_class = OwnerSerializer
    permission_classes = [InvenTree.permissions.IsAuthenticatedOrReadScope]


class RoleDetails(RetrieveAPI):
    """API endpoint which lists the available role permissions for the current user."""

    permission_classes = [InvenTree.permissions.IsAuthenticatedOrReadScope]
    serializer_class = RoleSerializer

    def get_object(self):
        """Overwritten to always return current user."""
        return self.request.user


class UserDetail(RetrieveUpdateDestroyAPI):
    """Detail endpoint for a single user.

    Permissions:
    - Staff users (who also have the 'admin' role) can perform write operations
    - Otherwise authenticated users have read-only access
    """

    queryset = User.objects.all()
    serializer_class = ExtendedUserSerializer
    permission_classes = [InvenTree.permissions.StaffRolePermissionOrReadOnly]

    def perform_destroy(self, instance):
        """Override destroy method to ensure sessions are deleted first."""
        # Remove all sessions for this user
        if sessions := instance.usersession_set.all():
            sessions.delete()
        # Normally delete the user
        return super().perform_destroy(instance)


class UserDetailSetPassword(UpdateAPI):
    """Allows superusers to set the password for a user."""

    queryset = User.objects.all()
    serializer_class = UserSetPasswordSerializer
    permission_classes = [InvenTree.permissions.IsSuperuserOrSuperScope]

    def get_object(self):
        """Return the user object for this endpoint."""
        return self.get_queryset().get(pk=self.kwargs['pk'])

    def perform_update(self, serializer):
        """Set the password for the user."""
        user: User = serializer.instance

        password: str = serializer.validated_data.get('password', None)
        overwrite: bool = serializer.validated_data.get('override_warning', False)

        if password:
            if not overwrite:
                try:
                    validate_password(password=password, user=user)
                except ValidationError as e:
                    raise exceptions.ValidationError({'password': str(e)})

            user.set_password(password)
            password_changed(password=password, user=user)
            user.save()


class MeUserDetail(RetrieveUpdateAPI, UserDetail):
    """Detail endpoint for current user.

    Permissions:
    - User can edit their own details via this endpoint
    - Only a subset of fields are available here
    """

    serializer_class = MeUserSerializer
    permission_classes = [InvenTree.permissions.IsAuthenticatedOrReadScope]

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
    """List endpoint for detail on all users.

    Permissions:
    - Staff users (who also have the 'admin' role) can perform write operations
    - Otherwise authenticated users have read-only access
    """

    queryset = User.objects.all()
    serializer_class = UserCreateSerializer

    # User must have the right role, AND be a staff user, else read-only
    permission_classes = [InvenTree.permissions.StaffRolePermissionOrReadOnly]

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


class GroupMixin(SerializerContextMixin):
    """Mixin for Group API endpoints to add permissions filter.

    Permissions:
    - Staff users (who also have the 'admin' role) can perform write operations
    - Otherwise authenticated users have read-only access
    """

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [InvenTree.permissions.IsStaffOrReadOnlyScope]


class GroupOutputOptions(OutputConfiguration):
    """Holds all available output options for Group views."""

    OPTIONS = [
        InvenTreeOutputOption('user_detail', description='Include user details'),
        InvenTreeOutputOption(
            'permission_detail', description='Include permission details'
        ),
        InvenTreeOutputOption(
            'role_detail', description='Include role details', default=True
        ),
    ]


class GroupDetail(GroupMixin, OutputOptionsMixin, RetrieveUpdateDestroyAPI):
    """Detail endpoint for a particular auth group."""

    output_options = GroupOutputOptions


class GroupList(GroupMixin, OutputOptionsMixin, ListCreateAPI):
    """List endpoint for all auth groups."""

    output_options = GroupOutputOptions
    filter_backends = SEARCH_ORDER_FILTER
    search_fields = ['name']
    ordering_fields = ['name']


class RuleSetMixin:
    """Mixin for RuleSet API endpoints."""

    queryset = RuleSet.objects.all()
    serializer_class = RuleSetSerializer
    permission_classes = [InvenTree.permissions.IsStaffOrReadOnlyScope]


class RuleSetList(RuleSetMixin, ListAPI):
    """List endpoint for all RuleSet instances."""

    filter_backends = SEARCH_ORDER_FILTER

    search_fields = ['name']
    ordering_fields = ['name']
    filterset_fields = ['group', 'name']


class RuleSetDetail(RuleSetMixin, RetrieveUpdateDestroyAPI):
    """Detail endpoint for a particular RuleSet instance."""


class GetAuthToken(GenericAPIView):
    """Return authentication token for an authenticated user."""

    permission_classes = [InvenTree.permissions.IsAuthenticatedOrReadScope]
    serializer_class = GetAuthTokenSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='name',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Name of the token',
            )
        ],
        responses={200: OpenApiResponse(response=GetAuthTokenSerializer())},
    )
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

            # Ensure that the users session is logged in
            if not get_user(request).is_authenticated:
                login(
                    request, user, backend='django.contrib.auth.backends.ModelBackend'
                )

            return Response(data)

        else:
            raise exceptions.NotAuthenticated()  # pragma: no cover


class TokenMixin:
    """Mixin for API token endpoints."""

    permission_classes = (InvenTree.permissions.IsAuthenticatedOrReadScope,)
    serializer_class = ApiTokenSerializer

    def get_queryset(self):
        """Only return data for current user."""
        if self.request.user.is_superuser and self.request.query_params.get(
            'all_users', False
        ):
            return ApiToken.objects.all()
        return ApiToken.objects.filter(user=self.request.user)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='all_users',
                type=bool,
                location=OpenApiParameter.QUERY,
                description='Display tokens for all users (superuser only)',
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        """Details for a user token."""
        return super().get(request, *args, **kwargs)


class TokenListView(TokenMixin, ListCreateAPI):
    """List of user tokens for current user."""

    filter_backends = SEARCH_ORDER_FILTER
    search_fields = ['name', 'key']
    ordering_fields = [
        'created',
        'expiry',
        'last_seen',
        'user',
        'name',
        'revoked',
        'revoked',
    ]
    filterset_fields = ['revoked', 'user']
    queryset = ApiToken.objects.none()

    def create(self, request, *args, **kwargs):
        """Create token and show key to user."""
        resp = super().create(request, *args, **kwargs)
        resp.data['token'] = self.serializer_class.Meta.model.objects.get(
            id=resp.data['id']
        ).key
        return resp

    def get(self, request, *args, **kwargs):
        """List of user tokens for current user."""
        return super().get(request, *args, **kwargs)


class TokenDetailView(TokenMixin, DestroyAPIView, RetrieveAPI):
    """Details for a user token."""

    def perform_destroy(self, instance):
        """Revoke token."""
        instance.revoked = True
        instance.save()


class LoginRedirect(RedirectView):
    """Redirect to the correct starting page after backend login."""

    def get_redirect_url(self, *args, **kwargs):
        """Return the URL to redirect to."""
        return f'/{FRONTEND_URL_BASE}/logged-in/'


class UserProfileDetail(RetrieveUpdateAPI):
    """Detail endpoint for the user profile.

    Permissions:
    - Any authenticated user has write access against this endpoint
    - The endpoint always returns the profile associated with the current user
    """

    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [InvenTree.permissions.IsAuthenticatedOrReadScope]

    def get_object(self):
        """Return the profile of the current user."""
        return self.request.user.profile


user_urls = [
    path('roles/', RoleDetails.as_view(), name='api-user-roles'),
    path('token/', ensure_csrf_cookie(GetAuthToken.as_view()), name='api-token'),
    path(
        'tokens/',
        include([
            path('<int:pk>/', TokenDetailView.as_view(), name='api-token-detail'),
            path('', TokenListView.as_view(), name='api-token-list'),
        ]),
    ),
    path('me/', MeUserDetail.as_view(), name='api-user-me'),
    path('profile/', UserProfileDetail.as_view(), name='api-user-profile'),
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
            path('<int:pk>/', GroupDetail.as_view(), name='api-group-detail'),
            path('', GroupList.as_view(), name='api-group-list'),
        ]),
    ),
    path(
        'ruleset/',
        include([
            path('<int:pk>/', RuleSetDetail.as_view(), name='api-ruleset-detail'),
            path('', RuleSetList.as_view(), name='api-ruleset-list'),
        ]),
    ),
    path(
        '<int:pk>/',
        include([
            path(
                'set-password/',
                UserDetailSetPassword.as_view(),
                name='api-user-set-password',
            ),
            path('', UserDetail.as_view(), name='api-user-detail'),
        ]),
    ),
    path('', UserList.as_view(), name='api-user-list'),
]
