"""API views for the sample plugin."""

from django.urls import path

from rest_framework import serializers

from InvenTree.filters import SEARCH_ORDER_FILTER_ALIAS
from InvenTree.mixins import ListCreateAPI, RetrieveUpdateDestroyAPI
from InvenTree.serializers import InvenTreeModelSerializer, UserSerializer


class SampleModelSerializer(InvenTreeModelSerializer):
    """Serializes a SampleModel object."""

    content_object = serializers.RelatedField(read_only=True)
    content_model = serializers.SerializerMethodField(
        method_name='get_content_model', read_only=True
    )
    user_field_detail = UserSerializer(source='user_field', read_only=True, many=False)

    def get_content_model(self, obj):
        """Get the content model name."""
        return obj.content_type.model

    class Meta:
        """Meta data for SampleModel."""

        # from .models import SampleModel

        # model = SampleModel
        fields = '__all__'


class SampleModelList(ListCreateAPI):
    """API endpoint for listing all SampleModel objects."""

    filter_backends = SEARCH_ORDER_FILTER_ALIAS
    serializer_class = SampleModelSerializer
    filterset_fields = ['string_field', 'user_field', 'content_type', 'object_id']
    search_fields = ['string_field', 'user_field']
    ordering_fields = ['string_field', 'user_field', 'boolean_field', 'date_field']
    ordering = '-date_field'

    def get_queryset(self):
        """Get the queryset."""
        from .models import SampleModel

        queryset = SampleModel.objects.all()

        return queryset


class SampleModelDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view."""

    serializer_class = SampleModelSerializer

    def get_queryset(self):
        """Get the queryset."""
        from .models import SampleModel

        queryset = SampleModel.objects.all()

        return queryset


api_patterns = [
    path('<int:pk>/', SampleModelDetail.as_view(), name='api-detail'),
    path('', SampleModelList.as_view(), name='api-list'),
]
