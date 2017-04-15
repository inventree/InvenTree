from rest_framework import generics, permissions

from InvenTree.models import FilterChildren
from .models import ProjectCategory, Project, ProjectPart
from .serializers import ProjectSerializer
from .serializers import ProjectCategorySerializer
from .serializers import ProjectPartSerializer


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


class ProjectList(generics.ListCreateAPIView):
    """

    get:
    Return a list of all Project objects
    (with optional query filters)

    post:
    Create a new Project

    """

    def get_queryset(self):
        projects = Project.objects.all()
        params = self.request.query_params

        cat_id = params.get('category', None)

        if cat_id:
            projects = projects.filter(category=cat_id)

        return projects

    serializer_class = ProjectSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


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


class ProjectPartsList(generics.ListCreateAPIView):
    """

    get:
    Return a list of all ProjectPart objects

    post:
    Create a new ProjectPart

    """

    serializer_class = ProjectPartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        parts = ProjectPart.objects.all()
        params = self.request.query_params

        project_id = params.get('project', None)
        if project_id:
            parts = parts.filter(project=project_id)

        part_id = params.get('part', None)
        if part_id:
            parts = parts.filter(part=part_id)

        return parts


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
