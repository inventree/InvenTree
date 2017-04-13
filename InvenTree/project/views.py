from rest_framework import generics, permissions

from .models import ProjectCategory, Project, ProjectPart
from .serializers import ProjectSerializer
from .serializers import ProjectCategoryDetailSerializer
from .serializers import ProjectPartSerializer


class ProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    """ Project details
    """

    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class ProjectList(generics.ListCreateAPIView):

    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class NewProjectCategory(generics.CreateAPIView):
    """ Create a new Project Category
    """
    serializer_class = ProjectCategoryDetailSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class ProjectCategoryDetail(generics.RetrieveUpdateAPIView):

    queryset = ProjectCategory.objects.all()
    serializer_class = ProjectCategoryDetailSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class ProjectCategoryList(generics.ListCreateAPIView):

    queryset = ProjectCategory.objects.filter(parent=None)
    serializer_class = ProjectCategoryDetailSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class ProjectPartsList(generics.ListCreateAPIView):

    serializer_class = ProjectPartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        project_id = self.kwargs['pk']
        return ProjectPart.objects.filter(project=project_id)
