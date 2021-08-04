"""
Custom management command to cleanup old settings that are not defined anymore
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Cleanup old (undefined) settings in the database
    """

    def handle(self, *args, **kwargs):

        print("Collecting settings")
        from common.models import InvenTreeSetting, InvenTreeUserSetting

        # general settings
        db_settings = InvenTreeSetting.objects.all()
        model_settings = InvenTreeSetting.GLOBAL_SETTINGS

        # check if key exist and delete if not
        for setting in db_settings:
            if setting.key not in model_settings:
                setting.delete()
                print(f"deleted setting '{setting.key}'")

        # user settings
        db_settings = InvenTreeUserSetting.objects.all()
        model_settings = InvenTreeUserSetting.GLOBAL_SETTINGS

        # check if key exist and delete if not
        for setting in db_settings:
            if setting.key not in model_settings:
                setting.delete()
                print(f"deleted user setting '{setting.key}'")

        print("checked all settings")
