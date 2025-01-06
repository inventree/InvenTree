"""Custom management command to cleanup old settings that are not defined anymore."""

from django.core.management.base import BaseCommand

import structlog

logger = structlog.get_logger('inventree')


class Command(BaseCommand):
    """Cleanup old (undefined) settings in the database."""

    def handle(self, *args, **kwargs):
        """Cleanup old (undefined) settings in the database."""
        logger.info('Collecting settings')
        from common.models import InvenTreeSetting, InvenTreeUserSetting

        # general settings
        db_settings = InvenTreeSetting.objects.all()
        model_settings = InvenTreeSetting.SETTINGS

        # check if key exist and delete if not
        for setting in db_settings:
            if setting.key not in model_settings:
                setting.delete()
                logger.info("deleted setting '%s'", setting.key)

        # user settings
        db_settings = InvenTreeUserSetting.objects.all()
        model_settings = InvenTreeUserSetting.SETTINGS

        # check if key exist and delete if not
        for setting in db_settings:
            if setting.key not in model_settings:
                setting.delete()
                logger.info("deleted user setting '%s'", setting.key)

        logger.info('checked all settings')
