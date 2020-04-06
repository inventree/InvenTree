from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError

import os
import uuid
import yaml


class CommonConfig(AppConfig):
    name = 'common'

    def ready(self):

        """ Will be called when the Common app is first loaded """
        self.populate_default_settings()
        self.add_instance_name()

    def populate_default_settings(self):
        """ Populate the default values for InvenTree key:value pairs.
        If a setting does not exist, it will be created.
        """

        # Import this here, rather than at the global-level,
        # otherwise it is called all the time, and we don't want that,
        # as the InvenTreeSetting model may have not been instantiated yet.
        from .models import InvenTreeSetting

        here = os.path.dirname(os.path.abspath(__file__))
        settings_file = os.path.join(here, 'kvp.yaml')

        with open(settings_file) as kvp:
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
            except (OperationalError, ProgrammingError):
                # Migrations have not yet been applied - table does not exist
                break

    def add_instance_name(self):
        """
        Check if an InstanceName has been defined for this database.
        If not, create a random one!
        """

        # See note above
        from .models import InvenTreeSetting

        try:
            if not InvenTreeSetting.objects.filter(key='InstanceName').exists():

                val = uuid.uuid4().hex

                print("No 'InstanceName' found - generating random name '{n}'".format(n=val))

                name = InvenTreeSetting(
                    key="InstanceName",
                    value=val,
                    description="Instance name for this InvenTree database installation."
                )

                name.save()
        except (OperationalError, ProgrammingError):
            # Migrations have not yet been applied - table does not exist
            pass
