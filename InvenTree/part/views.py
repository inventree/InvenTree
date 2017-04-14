# import django_filters

from rest_framework import generics, permissions

from .models import PartCategory, Part, PartParameter, PartParameterTemplate
from .serializers import PartSerializer
from .serializers import PartCategoryDetailSerializer
from .serializers import PartParameterSerializer
from .serializers import PartTemplateSerializer


class PartDetail(generics.RetrieveUpdateDestroyAPIView):
    """ Return information on a single part
    """
    queryset = Part.objects.all()
    serializer_class = PartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PartParamList(generics.ListCreateAPIView):
    """ Return all parameters associated with a particular part
    """
    def get_queryset(self):
        part_id = self.request.query_params.get('part', None)

        if part_id:
            return PartParameter.objects.filter(part=part_id)
        else:
            return PartParameter.objects.all()

    serializer_class = PartParameterSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def create(self, request, *args, **kwargs):
        # Ensure part link is set correctly
        part_id = self.request.query_params.get('part', None)
        if part_id:
            request.data['part'] = part_id
        return super(PartParamList, self).create(request, *args, **kwargs)


class PartParamDetail(generics.RetrieveUpdateDestroyAPIView):
    """ Detail view of a single PartParameter
    """

    queryset = PartParameter.objects.all()
    serializer_class = PartParameterSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


"""
class PartFilter(django_filters.rest_framework.FilterSet):
    min_stock = django_filters.NumberFilter(name="stock", lookup_expr="gte")
    max_stock = django_filters.NumberFilter(name="stock", lookup_expr="lte")

    class Meta:
        model = Part
        fields = ['stock']
"""


class PartList(generics.ListCreateAPIView):
    """ Display a list of parts, with optional filters
    Filters are specified in the url, e.g.
    /part/?category=127
    /part/?min_stock=100
    """

    def get_queryset(self):
        parts = Part.objects.all()

        cat_id = self.request.query_params.get('category', None)
        if cat_id:
            parts = parts.filter(category=cat_id)

        return parts

    serializer_class = PartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PartCategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    """ Return information on a single PartCategory
    """
    queryset = PartCategory.objects.all()
    serializer_class = PartCategoryDetailSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PartCategoryList(generics.ListCreateAPIView):
    """ Return a list of all top-level part categories.
    Categories are considered "top-level" if they do not have a parent
    """
    queryset = PartCategory.objects.filter(parent=None)
    serializer_class = PartCategoryDetailSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PartTemplateDetail(generics.RetrieveUpdateDestroyAPIView):

    queryset = PartParameterTemplate.objects.all()
    serializer_class = PartTemplateSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PartTemplateList(generics.ListCreateAPIView):

    queryset = PartParameterTemplate.objects.all()
    serializer_class = PartTemplateSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
