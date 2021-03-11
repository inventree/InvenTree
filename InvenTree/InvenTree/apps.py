# -*- coding: utf-8 -*-

from django.apps import AppConfig
import logging

import InvenTree.tasks


logger = logging.getLogger(__name__)


class InvenTreeConfig(AppConfig):
    name = 'InvenTree'

    def ready(self):

        self.start_background_tasks()

    def start_background_tasks(self):

        try:
            from django_q.models import Schedule
        except (AppRegistryNotReady):
            return

        logger.info("Starting background tasks...")

        InvenTree.tasks.schedule_task(
            'InvenTree.tasks.delete_successful_tasks',
            schedule_type=Schedule.WEEKLY,
        )

        InvenTree.tasks.schedule_task(
            'InvenTree.tasks.check_for_updates',
            schedule_type=Schedule.DAILY
        )
