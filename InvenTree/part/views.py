from rest_framework import generics

from .models import PartCategory, Part, PartParameter
from .serializers import PartSerializer
from .serializers import PartCategoryDetailSerializer
from .serializers import PartParameterSerializer


class PartDetail(generics.RetrieveAPIView):

    queryset = Part.objects.all()
    serializer_class = PartSerializer


class PartParameters(generics.ListAPIView):

    def get_queryset(self):
        part_id = self.kwargs['pk']
        return PartParameter.objects.filter(part=part_id)

    serializer_class = PartParameterSerializer


class PartList(generics.ListAPIView):

    queryset = Part.objects.all()
    serializer_class = PartSerializer


class PartCategoryDetail(generics.RetrieveAPIView):
    """ Return information on a single PartCategory
    """
    queryset = PartCategory.objects.all()
    serializer_class = PartCategoryDetailSerializer


class PartCategoryList(generics.ListAPIView):
    """ Return a list of all top-level part categories.
    Categories are considered "top-level" if they do not have a parent
    """
    queryset = PartCategory.objects.filter(parent=None)
    serializer_class = PartCategoryDetailSerializer
