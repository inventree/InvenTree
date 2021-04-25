# -*- coding: utf-8 -*-

import logging

from django.apps import AppConfig
from django.core.exceptions import AppRegistryNotReady

from InvenTree.ready import canAppAccessDatabase
import InvenTree.tasks


logger = logging.getLogger("inventree")


class InvenTreeConfig(AppConfig):
    name = 'InvenTree'

    def ready(self):

        if canAppAccessDatabase():
            self.start_background_tasks()

    def start_background_tasks(self):

        try:
            from django_q.models import Schedule
        except (AppRegistryNotReady):
            return

        logger.info("Starting background tasks...")

        InvenTree.tasks.schedule_task(
            'InvenTree.tasks.delete_successful_tasks',
            schedule_type=Schedule.DAILY,
        )

        InvenTree.tasks.schedule_task(
            'InvenTree.tasks.check_for_updates',
            schedule_type=Schedule.DAILY
        )

        InvenTree.tasks.schedule_task(
            'InvenTree.tasks.heartbeat',
            schedule_type=Schedule.MINUTES,
            minutes=15
        )
