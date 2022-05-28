
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.urls import include, path, re_path

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Owner, RuleSet, check_user_role
from users.serializers import OwnerSerializer, UserSerializer


class OwnerList(generics.ListAPIView):
    """List API endpoint for Owner model. Cannot create."""

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


class OwnerDetail(generics.RetrieveAPIView):
    """Detail API endpoint for Owner model. Cannot edit or delete"""

    queryset = Owner.objects.all()
    serializer_class = OwnerSerializer


class RoleDetails(APIView):
    """API endpoint which lists the available role permissions for the current user

    (Requires authentication)
    """

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request, *args, **kwargs):

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


class UserDetail(generics.RetrieveAPIView):
    """Detail endpoint for a single user"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)


class UserList(generics.ListAPIView):
    """List endpoint for detail on all users"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
    ]

    search_fields = [
        'first_name',
        'last_name',
        'username',
    ]


class GetAuthToken(APIView):
    """Return authentication token for an authenticated user."""

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get(self, request, *args, **kwargs):
        return self.login(request)

    def delete(self, request):
        return self.logout(request)

    def login(self, request):

        if request.user.is_authenticated:
            # Get the user token (or create one if it does not exist)
            token, created = Token.objects.get_or_create(user=request.user)
            return Response({
                'token': token.key,
            })

    def logout(self, request):
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

    re_path(r'^owner/', include([
        path('<int:pk>/', OwnerDetail.as_view(), name='api-owner-detail'),
        re_path(r'^.*$', OwnerList.as_view(), name='api-owner-list'),
    ])),

    re_path(r'^(?P<pk>[0-9]+)/?$', UserDetail.as_view(), name='user-detail'),
    path('', UserList.as_view()),
]
