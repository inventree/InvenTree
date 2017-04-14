from rest_framework import generics, permissions

from InvenTree.models import FilterChildren
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
    """ List projects
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
    """ Project details
    """

    queryset = ProjectCategory.objects.all()
    serializer_class = ProjectCategoryDetailSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class ProjectCategoryList(generics.ListCreateAPIView):
    """ List project categories
    """

    def get_queryset(self):
        params = self.request.query_params

        categories = ProjectCategory.objects.all()

        categories = FilterChildren(categories, params.get('parent', None))

        return categories

    serializer_class = ProjectCategoryDetailSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class ProjectPartsList(generics.ListCreateAPIView):
    """ List project parts
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

    def create(self, request, *args, **kwargs):
        # Ensure project link is set correctly
        prj_id = self.request.query_params.get('project', None)
        if prj_id:
            request.data['project'] = prj_id
        return super(ProjectPartsList, self).create(request, *args, **kwargs)


class ProjectPartDetail(generics.RetrieveUpdateDestroyAPIView):
    """ Detail for a single project part
    """

    queryset = ProjectPart.objects.all()
    serializer_class = ProjectPartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
