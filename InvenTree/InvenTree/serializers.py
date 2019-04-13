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


class DraftRUDView(generics.RetrieveAPIView, generics.UpdateAPIView, generics.DestroyAPIView):

    def perform_update(self, serializer):

        ctx_data = serializer._context['request'].data

        if ctx_data.get('_is_final', False) in [True, u'true', u'True', 1]:
            super(generics.UpdateAPIView, self).perform_update(serializer)
        else:
            pass
