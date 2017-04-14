from rest_framework import serializers

from .models import ProjectCategory, Project, ProjectPart


class ProjectPartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectPart
        fields = ('pk',
                  'part',
                  'project',
                  'quantity',
                  'output')


class ProjectSerializer(serializers.ModelSerializer):
    """ Serializer for displaying brief overview of a project
    """

    class Meta:
        model = Project
        fields = ('pk',
                  'name',
                  'description',
                  'category')


class ProjectCategorySerializer(serializers.ModelSerializer):

    children = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    projects = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = ProjectCategory
        fields = ('pk',
                  'name',
                  'description',
                  'parent',
                  'path',
                  'children',
                  'projects')
