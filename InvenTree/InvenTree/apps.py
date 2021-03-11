# -*- coding: utf-8 -*-

from django.apps import AppConfig


class InvenTreeConfig(AppConfig):
    name = 'InvenTree'

    def ready(self):

        print("Starting background tasks")
        pass
