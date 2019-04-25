# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers
from rest_framework import generics

from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = 'all'


class UserSerializerBrief(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'pk',
            'username',
        ]
