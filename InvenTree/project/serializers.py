from rest_framework import serializers

from .models import ProjectCategory, Project, ProjectPart


class ProjectPartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectPart
        fields = ('pk',
                  'part',
                  'project',
                  'quantity',
                  'overage',
                  'overage_type')


class ProjectBriefSerializer(serializers.ModelSerializer):
    """ Serializer for displaying brief overview of a project
    """

    class Meta:
        model = Project
        fields = ('pk',
                  'name',
                  'description',
                  'category')


class ProjectDetailSerializer(serializers.ModelSerializer):
    """ Serializer for detailed project information
    """

    class Meta:
        model = Project
        fields = ('pk',
                  'name',
                  'description',
                  'category')


class ProjectCategoryBriefSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectCategory
        fields = ('pk', 'name', 'description')


class ProjectCategoryDetailSerializer(serializers.ModelSerializer):

    projects = ProjectBriefSerializer(many=True)

    children = ProjectCategoryBriefSerializer(many=True)

    class Meta:
        model = ProjectCategory
        fields = ('pk',
                  'name',
                  'description',
                  'parent',
                  'path',
                  'children',
                  'projects')
