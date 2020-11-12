# -*- coding: utf-8 -*-

from django.apps import AppConfig


class CommonConfig(AppConfig):
    name = 'common'

    def ready(self):
        pass
