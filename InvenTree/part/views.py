# import django_filters

from rest_framework import generics, permissions

from InvenTree.models import FilterChildren
from .models import PartCategory, Part, PartParameter, PartParameterTemplate
from .serializers import PartSerializer
from .serializers import PartCategorySerializer
from .serializers import PartParameterSerializer
from .serializers import PartTemplateSerializer


class PartDetail(generics.RetrieveUpdateDestroyAPIView):
    """

    get:
    Return detail on a single Part

    post:
    Update data for a single Part

    delete:
    Remove a part from the database

    """
    queryset = Part.objects.all()
    serializer_class = PartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PartParamList(generics.ListCreateAPIView):
    """

    get:
    Return a list of all part parameters (with optional filters)

    post:
    Create a new part parameter
    """
    def get_queryset(self):
        part_id = self.request.query_params.get('part', None)

        if part_id:
            return PartParameter.objects.filter(part=part_id)
        else:
            return PartParameter.objects.all()

    serializer_class = PartParameterSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PartParamDetail(generics.RetrieveUpdateDestroyAPIView):
    """

    get:
    Detail view of a single PartParameter

    post:
    Update data for a PartParameter

    delete:
    Remove a PartParameter from the database

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
    """

    get:
    List of Parts, with optional filters

    post:
    Create a new Part
    """

    def get_queryset(self):
        parts = Part.objects.all()
        params = self.request.query_params

        cat_id = params.get('category', None)

        if cat_id:
            parts = parts.filter(category=cat_id)

        return parts

    serializer_class = PartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PartCategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    """

    get:
    Return information on a single PartCategory

    post:
    Update a PartCategory

    delete:
    Remove a PartCategory

    """
    queryset = PartCategory.objects.all()
    serializer_class = PartCategorySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PartCategoryList(generics.ListCreateAPIView):
    """

    get:
    Return a list of all categories
    (with optional filters)

    post:
    Create a new PartCategory
    """

    def get_queryset(self):
        params = self.request.query_params

        categories = PartCategory.objects.all()

        categories = FilterChildren(categories, params.get('parent', None))

        return categories

    queryset = PartCategory.objects.filter(parent=None)
    serializer_class = PartCategorySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PartTemplateDetail(generics.RetrieveUpdateDestroyAPIView):
    """

    get:
    Return detail on a single PartParameterTemplate object

    post:
    Update a PartParameterTemplate object

    delete:
    Remove a PartParameterTemplate object

    """

    queryset = PartParameterTemplate.objects.all()
    serializer_class = PartTemplateSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PartTemplateList(generics.ListCreateAPIView):
    """

    get:
    Return a list of all PartParameterTemplate objects
    (with optional query filters)

    post:
    Create a new PartParameterTemplate object

    """

    queryset = PartParameterTemplate.objects.all()
    serializer_class = PartTemplateSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
