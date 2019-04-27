""" 
Serializers used in various InvenTree apps
"""


# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """ Serializer for User - provides all fields """

    class Meta:
        model = User
        fields = 'all'


class UserSerializerBrief(serializers.ModelSerializer):
    """ Serializer for User - provides limited information """

    class Meta:
        model = User
        fields = [
            'pk',
            'username',
        ]


class InvenTreeModelSerializer(serializers.ModelSerializer):
    """
    Inherits the standard Django ModelSerializer class,
    but also ensures that the underlying model class data are checked on validation.
    """

    def validate(self, data):
        # Run any native validation checks first (may throw an ValidationError)
        data = super(serializers.ModelSerializer, self).validate(data)

        # Now ensure the underlying model is correct
        instance = self.Meta.model(**data)
        instance.clean()

        return data
