from django.apps import AppConfig
from django.db.utils import OperationalError

import yaml


class CommonConfig(AppConfig):
    name = 'common'

    def ready(self):
        """ Will be called when the Common app is first loaded """
        self.populate_default_settings()

    def populate_default_settings(self):
        """ Populate the default values for InvenTree key:value pairs.
        If a setting does not exist, it will be created.
        """

        from .models import InvenTreeSetting

        with open('./common/kvp.yaml') as kvp:
            values = yaml.safe_load(kvp)

        for value in values:
            key = value['key']
            default = value['default']
            description = value['description']

            try:
                # If a particular setting does not exist in the database, create it now
                if not InvenTreeSetting.objects.filter(key=key).exists():
                    setting = InvenTreeSetting(
                        key=key,
                        value=default,
                        description=description
                    )

                    setting.save()

                    print("Creating new key: '{k}' = '{v}'".format(k=key, v=default))
            except OperationalError:
                # Migrations have not yet been applied - table does not exist
                break
