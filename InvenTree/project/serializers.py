from rest_framework import serializers

from .models import ProjectCategory, Project, ProjectPart


class ProjectPartSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = ProjectPart
        fields = ('url',
                  'part',
                  'project',
                  'quantity',
                  'output')


class ProjectSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Project
        fields = ('url',
                  'name',
                  'description',
                  'category')


class ProjectCategorySerializer(serializers.HyperlinkedModelSerializer):

    children = serializers.HyperlinkedRelatedField(many=True,
                                                   read_only=True,
                                                   view_name='projectcategory-detail')

    projects = serializers.HyperlinkedRelatedField(many=True,
                                                   read_only=True,
                                                   view_name='project-detail')

    class Meta:
        model = ProjectCategory
        fields = ('url',
                  'name',
                  'description',
                  'parent',
                  'path',
                  'children',
                  'projects')
