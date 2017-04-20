from django_filters.rest_framework import FilterSet, DjangoFilterBackend

from rest_framework import generics, permissions
from InvenTree.models import FilterChildren
from .models import ProjectCategory, Project, ProjectPart, ProjectRun
from .serializers import ProjectSerializer
from .serializers import ProjectCategorySerializer
from .serializers import ProjectPartSerializer
from .serializers import ProjectRunSerializer


class ProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    """

    get:
    Return a single Project object

    post:
    Update a Project

    delete:
    Remove a Project

    """

    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class ProjectFilter(FilterSet):

    class Meta:
        model = Project
        fields = ['category']


class ProjectList(generics.ListCreateAPIView):
    """

    get:
    Return a list of all Project objects
    (with optional query filters)

    post:
    Create a new Project

    """

    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = ProjectFilter


class ProjectCategoryDetail(generics.RetrieveUpdateAPIView):
    """

    get:
    Return a single ProjectCategory object

    post:
    Update a ProjectCategory

    delete:
    Remove a ProjectCategory

    """

    queryset = ProjectCategory.objects.all()
    serializer_class = ProjectCategorySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class ProjectCategoryList(generics.ListCreateAPIView):
    """

    get:
    Return a list of all ProjectCategory objects

    post:
    Create a new ProjectCategory

    """

    def get_queryset(self):
        params = self.request.query_params

        categories = ProjectCategory.objects.all()

        categories = FilterChildren(categories, params.get('parent', None))

        return categories

    serializer_class = ProjectCategorySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class ProjectPartFilter(FilterSet):

    class Meta:
        model = ProjectPart
        fields = ['project', 'part']


class ProjectPartsList(generics.ListCreateAPIView):
    """

    get:
    Return a list of all ProjectPart objects

    post:
    Create a new ProjectPart

    """

    serializer_class = ProjectPartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = ProjectPart.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_class = ProjectPartFilter


class ProjectPartDetail(generics.RetrieveUpdateDestroyAPIView):
    """

    get:
    Return a single ProjectPart object

    post:
    Update a ProjectPart

    delete:
    Remove a ProjectPart

    """

    queryset = ProjectPart.objects.all()
    serializer_class = ProjectPartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class ProjectRunDetail(generics.RetrieveUpdateDestroyAPIView):
    """

    get:
    Return a single ProjectRun

    post:
    Update a ProjectRun

    delete:
    Remove a ProjectRun
    """

    queryset = ProjectRun.objects.all()
    serializer_class = ProjectRunSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class ProjectRunFilter(FilterSet):

    class Meta:
        model = ProjectRun
        fields = ['project']


class ProjectRunList(generics.ListCreateAPIView):
    """

    get:
    Return a list of all ProjectRun objects

    post:
    Create a new ProjectRun object
    """

    queryset = ProjectRun.objects.all()
    serializer_class = ProjectRunSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = ProjectRunFilter
