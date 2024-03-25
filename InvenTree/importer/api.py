"""API endpoints for the importer app."""

from django.urls import include, path

import importer.models
import importer.serializers
from InvenTree.mixins import ListCreateAPI


class DataImportSessionList(ListCreateAPI):
    """API endpoint for accessing a list of DataImportSession objects."""

    queryset = importer.models.DataImportSession.objects.all()
    serializer_class = importer.serializers.DataImportSessionSerializer


importer_api_urls = [
    path(
        'session/',
        include([
            path('', DataImportSessionList.as_view(), name='importer-session-list')
        ]),
    )
]
