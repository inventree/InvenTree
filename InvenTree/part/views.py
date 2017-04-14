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


class PartList(generics.ListCreateAPIView):

    queryset = Part.objects.all()
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
