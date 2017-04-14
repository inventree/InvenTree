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
    """ List all projects
    """

    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class NewProjectCategory(generics.CreateAPIView):
    """ Create a new Project Category
    """
    serializer_class = ProjectCategoryDetailSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class ProjectCategoryDetail(generics.RetrieveUpdateAPIView):
    """ Project details
    """

    queryset = ProjectCategory.objects.all()
    serializer_class = ProjectCategoryDetailSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class ProjectCategoryList(generics.ListCreateAPIView):
    """ Top-level project categories.
    Projects are considered top-level if they do not have a parent
    """

    queryset = ProjectCategory.objects.filter(parent=None)
    serializer_class = ProjectCategoryDetailSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class ProjectPartsList(generics.ListCreateAPIView):
    """ List all parts associated with a particular project
    """

    serializer_class = ProjectPartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        project_id = self.kwargs['pk']
        return ProjectPart.objects.filter(project=project_id)

    def create(self, request, *args, **kwargs):
        # Ensure project link is set correctly
        request.data['project'] = self.kwargs['pk']
        return super(ProjectPartsList, self).create(request, *args, **kwargs)
