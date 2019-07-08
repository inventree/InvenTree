from rest_framework import generics, permissions
from django.contrib.auth.models import User
from .serializers import UserSerializer

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response


class UserDetail(generics.RetrieveAPIView):
    """ Detail endpoint for a single user """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)


class UserList(generics.ListAPIView):
    """ List endpoint for detail on all users """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)


class GetAuthToken(ObtainAuthToken):
    """ Return authentication token for an authenticated user. """

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'pk': user.pk,
            'username': user.username,
            'email': user.email
        })
