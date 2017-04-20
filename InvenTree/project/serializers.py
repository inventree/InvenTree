from rest_framework import serializers

from .models import ProjectCategory, Project, ProjectPart, ProjectRun


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


class ProjectRunSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = ProjectRun
        fields = ('url',
                  'project',
                  'quantity',
                  'run_date')

        read_only_fields = ('run_date',)
