"""DRF API definition for the 'users' app"""

import datetime
import logging

from django.contrib.auth.models import Group, User
from django.urls import include, path, re_path

from rest_framework import exceptions, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

import InvenTree.helpers
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import (ListAPI, ListCreateAPI, RetrieveAPI,
                              RetrieveUpdateAPI, RetrieveUpdateDestroyAPI)
from InvenTree.serializers import ExendedUserSerializer, UserCreateSerializer
from users.models import ApiToken, Owner, RuleSet, check_user_role
from users.serializers import GroupSerializer, OwnerSerializer

logger = logging.getLogger('inventree')


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
            matching_user_ids = User.objects.filter(is_active=is_active).values_list('pk', flat=True)

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
                if result.owner_type.name == 'user' and result.owner_id not in matching_user_ids:
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


class RoleDetails(APIView):
    """API endpoint which lists the available role permissions for the current user.

    (Requires authentication)
    """

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request, *args, **kwargs):
        """Return the list of roles / permissions available to the current user"""
        user = request.user

        roles = {}

        for ruleset in RuleSet.RULESET_CHOICES:

            role, _text = ruleset

            permissions = []

            for permission in RuleSet.RULESET_PERMISSIONS:
                if check_user_role(user, role, permission):

                    permissions.append(permission)

            if len(permissions) > 0:
                roles[role] = permissions
            else:
                roles[role] = None  # pragma: no cover

        data = {
            'user': user.pk,
            'username': user.username,
            'roles': roles,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }

        return Response(data)


class UserDetail(RetrieveUpdateDestroyAPI):
    """Detail endpoint for a single user."""

    queryset = User.objects.all()
    serializer_class = ExendedUserSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]


class MeUserDetail(RetrieveUpdateAPI, UserDetail):
    """Detail endpoint for current user."""

    def get_object(self):
        """Always return the current user object"""
        return self.request.user


class UserList(ListCreateAPI):
    """List endpoint for detail on all users."""

    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    filter_backends = SEARCH_ORDER_FILTER

    search_fields = [
        'first_name',
        'last_name',
        'username',
    ]

    ordering_fields = [
        'email',
        'username',
        'first_name',
        'last_name',
        'is_staff',
        'is_superuser',
        'is_active',
    ]

    filterset_fields = [
        'is_staff',
        'is_active',
        'is_superuser',
    ]


class GroupDetail(RetrieveUpdateDestroyAPI):
    """Detail endpoint for a particular auth group"""

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]


class GroupList(ListCreateAPI):
    """List endpoint for all auth groups"""

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filter_backends = SEARCH_ORDER_FILTER

    search_fields = [
        'name',
    ]

    ordering_fields = [
        'name',
    ]


class GetAuthToken(APIView):
    """Return authentication token for an authenticated user."""

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get(self, request, *args, **kwargs):
        """Return an API token if the user is authenticated

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
            token = ApiToken.objects.filter(user=user, name=name, revoked=False, expiry__gte=today).first()

            if not token:
                # User is authenticated, and requesting a token against the provided name.
                token = ApiToken.objects.create(user=request.user, name=name)

            # Add some metadata about the request
            token.set_metadata('user_agent', request.META.get('HTTP_USER_AGENT', ''))
            token.set_metadata('remote_addr', request.META.get('REMOTE_ADDR', ''))
            token.set_metadata('remote_host', request.META.get('REMOTE_HOST', ''))
            token.set_metadata('remote_user', request.META.get('REMOTE_USER', ''))
            token.set_metadata('server_name', request.META.get('SERVER_NAME', ''))
            token.set_metadata('server_port', request.META.get('SERVER_PORT', ''))

            data = {
                'token': token.key,
                'name': token.name,
                'expiry': token.expiry,
            }

            logger.info("Created new API token for user '%s' (name='%s')", user.username, name)

            return Response(data)

        else:
            raise exceptions.NotAuthenticated()


user_urls = [

    re_path(r'roles/?$', RoleDetails.as_view(), name='api-user-roles'),
    re_path(r'token/?$', GetAuthToken.as_view(), name='api-token'),
    re_path(r'^me/', MeUserDetail.as_view(), name='api-user-me'),

    re_path(r'^owner/', include([
        path('<int:pk>/', OwnerDetail.as_view(), name='api-owner-detail'),
        re_path(r'^.*$', OwnerList.as_view(), name='api-owner-list'),
    ])),

    re_path(r'^group/', include([
        re_path(r'^(?P<pk>[0-9]+)/?$', GroupDetail.as_view(), name='api-group-detail'),
        re_path(r'^.*$', GroupList.as_view(), name='api-group-list'),
    ])),

    re_path(r'^(?P<pk>[0-9]+)/?$', UserDetail.as_view(), name='api-user-detail'),

    path('', UserList.as_view(), name='api-user-list'),
]
