"""DRF API definition for the 'users' app"""

from django.contrib.auth.models import Group, User
from django.core.exceptions import ObjectDoesNotExist
from django.urls import include, path, re_path

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from InvenTree.filters import InvenTreeSearchFilter
from InvenTree.mixins import ListAPI, RetrieveAPI, RetrieveUpdateAPI
from InvenTree.serializers import UserSerializer
from users.models import Owner, RuleSet, check_user_role
from users.serializers import GroupSerializer, OwnerSerializer


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

        queryset = super().filter_queryset(queryset)

        if not search_term:
            return queryset

        results = []

        # Extract search term f

        for result in queryset.all():
            if search_term in result.name().lower():
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

            role, text = ruleset

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


class UserDetail(RetrieveAPI):
    """Detail endpoint for a single user."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]


class MeUserDetail(RetrieveUpdateAPI, UserDetail):
    """Detail endpoint for current user."""

    def get_object(self):
        """Always return the current user object"""
        return self.request.user


class UserList(ListAPI):
    """List endpoint for detail on all users."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend,
        InvenTreeSearchFilter,
    ]

    search_fields = [
        'first_name',
        'last_name',
        'username',
    ]


class GroupDetail(RetrieveAPI):
    """Detail endpoint for a particular auth group"""

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]


class GroupList(ListAPI):
    """List endpoint for all auth groups"""

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend,
        InvenTreeSearchFilter,
    ]

    search_fields = [
        'name',
    ]


class GetAuthToken(APIView):
    """Return authentication token for an authenticated user."""

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get(self, request, *args, **kwargs):
        """Return an API token if the user is authenticated

        - If the user already has a token, return it
        - Otherwise, create a new token
        """
        if request.user.is_authenticated:
            # Get the user token (or create one if it does not exist)
            token, created = Token.objects.get_or_create(user=request.user)
            return Response({
                'token': token.key,
            })

    def delete(self, request):
        """User has requested deletion of API token"""
        try:
            request.user.auth_token.delete()
            return Response({"success": "Successfully logged out."},
                            status=status.HTTP_202_ACCEPTED)
        except (AttributeError, ObjectDoesNotExist):
            return Response({"error": "Bad request"},
                            status=status.HTTP_400_BAD_REQUEST)


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
