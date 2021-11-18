"""
JSON serializers for Stock app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import subprocess

from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from plugin.models import PluginConfig


class PluginConfigSerializer(serializers.ModelSerializer):
    """ Serializer for a PluginConfig:
    """

    meta = serializers.DictField(read_only=True)
    mixins = serializers.DictField(read_only=True)

    class Meta:
        model = PluginConfig
        fields = [
            'key',
            'name',
            'active',
            'meta',
            'mixins',
        ]


class PluginConfigInstallSerializer(serializers.Serializer):
    """
    Serializer for installing a new plugin
    """

    url = serializers.CharField(
        required=False,
        allow_blank=True,
        label=_('Source URL'),
        help_text=_('Source for the package - this can be a custom registry or a VCS path')
    )
    packagename = serializers.CharField(
        required=False,
        allow_blank=True,
        label=_('Package Name'),
        help_text=_('Name for the Plugin Package - can also contain a version indicator'),
    )
    confirm = serializers.BooleanField(
        label=_('Confirm plugin installation'),
        help_text=_('This will install this plugin now into the current instance. The instance will go into maintenance.')
    )

    class Meta:
        fields = [
            'url',
            'packagename',
            'confirm',
        ]

    def validate(self, data):
        super().validate(data)

        # check the base requirements are met
        if not data.get('confirm'):
            raise ValidationError({'confirm': _('Installation not confirmed')})
        if (not data.get('url')) and (not data.get('packagename')):
            msg = _('Either packagenmae of url must be provided')
            raise ValidationError({'url': msg, 'packagename': msg})

        return data

    def save(self):
        data = self.validated_data

        packagename = data.get('packagename', '')
        url = data.get('url', '')

        # build up the command
        command = 'python -m pip install'.split()

        if url:
            # use custom registration / VCS
            if True in [identifier in url for identifier in ['git+https', 'hg+https', 'svn+svn', ]]:
                # using a VCS provider
                if packagename:
                    command.append(f'{packagename}@{url}')
                else:
                    command.append(url)
            else:
                # using a custom package repositories
                command.append('-i')
                command.append(url)
                command.append(packagename)

        elif packagename:
            # use pypi
            command.append(packagename)

        ret = {'command': command}
        # execute pypi
        try:
            result = subprocess.check_output(command, cwd=os.path.dirname(settings.BASE_DIR))
            ret['result'] = str(result, 'utf-8')
        except subprocess.CalledProcessError as error:
            ret['result'] = str(error.output, 'utf-8')
            ret['error'] = True

        # register plugins
        # TODO

        return ret
