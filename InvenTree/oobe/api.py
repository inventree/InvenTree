"""APIs for setups"""
from django.urls import re_path

from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .registry import setups


class OOBEListView(ListAPIView):
    """Endpoint for listing setups"""
    permission_classes = [IsAuthenticated]

    def list(self, *args, **kwargs):
        data = setups.to_representation()
        return Response(data)


oobe_api_urls = [
    # General setup
    re_path(r'^.*$', OOBEListView.as_view(), name='api-setup-list'),
]
