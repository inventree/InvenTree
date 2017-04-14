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

    class Meta:
        model = ProjectCategory
        fields = ('url',
                  'name',
                  'description',
                  'parent',
                  'path')
