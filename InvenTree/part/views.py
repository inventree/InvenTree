from rest_framework import generics, permissions

from .models import PartCategory, Part, PartParameter
from .serializers import PartSerializer
from .serializers import PartCategoryBriefSerializer
from .serializers import PartCategoryDetailSerializer
from .serializers import PartParameterSerializer


class PartDetail(generics.RetrieveUpdateDestroyAPIView):
    """ Return information on a single part
    """
    queryset = Part.objects.all()
    serializer_class = PartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PartParameters(generics.ListCreateAPIView):
    """ Return all parameters associated with a particular part
    """
    def get_queryset(self):
        part_id = self.kwargs['pk']
        return PartParameter.objects.filter(part=part_id)

    serializer_class = PartParameterSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PartList(generics.ListCreateAPIView):

    queryset = Part.objects.all()
    serializer_class = PartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PartCategoryDetail(generics.RetrieveUpdateAPIView):
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
