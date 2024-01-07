"""DRF API serializers for the 'users' app"""

from django.contrib.auth.models import Group

from rest_framework import serializers

from InvenTree.serializers import InvenTreeModelSerializer

from .models import Owner


class OwnerSerializer(InvenTreeModelSerializer):
    """Serializer for an "Owner" (either a "user" or a "group")"""

    class Meta:
        """Metaclass defines serializer fields."""

        model = Owner
        fields = ['pk', 'owner_id', 'name', 'label']

    name = serializers.CharField(read_only=True)

    label = serializers.CharField(read_only=True)


class GroupSerializer(InvenTreeModelSerializer):
    """Serializer for a 'Group'"""

    class Meta:
        """Metaclass defines serializer fields"""

        model = Group
        fields = ['pk', 'name']
