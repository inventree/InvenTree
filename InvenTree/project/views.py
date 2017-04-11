from rest_framework import generics

from .models import ProjectCategory, Project, ProjectPart
from .serializers import ProjectBriefSerializer, ProjectDetailSerializer
from .serializers import ProjectCategoryDetailSerializer
from .serializers import ProjectPartSerializer


class ProjectDetail(generics.RetrieveAPIView):

    queryset = Project.objects.all()
    serializer_class = ProjectDetailSerializer


class ProjectList(generics.ListAPIView):

    queryset = Project.objects.all()
    serializer_class = ProjectBriefSerializer


class ProjectCategoryDetail(generics.RetrieveAPIView):

    queryset = ProjectCategory.objects.all()
    serializer_class = ProjectCategoryDetailSerializer


class ProjectCategoryList(generics.ListAPIView):

    queryset = ProjectCategory.objects.filter(parent=None)
    serializer_class = ProjectCategoryDetailSerializer


class ProjectPartsList(generics.ListAPIView):

    serializer_class = ProjectPartSerializer

    def get_queryset(self):
        project_id = self.kwargs['pk']
        return ProjectPart.objects.filter(project=project_id)
