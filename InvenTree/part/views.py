from rest_framework import generics

from .models import PartCategory, Part
from .serializers import PartBriefSerializer, PartDetailSerializer
from .serializers import PartCategoryBriefSerializer, PartCategoryDetailSerializer


class PartDetail(generics.RetrieveAPIView):

    queryset = Part.objects.all()
    serializer_class = PartDetailSerializer


class PartList(generics.ListAPIView):

    queryset = Part.objects.all()
    serializer_class = PartBriefSerializer


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
    serializer_class = PartCategoryBriefSerializer
