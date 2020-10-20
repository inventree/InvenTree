from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError


class CommonConfig(AppConfig):
    name = 'common'

    def ready(self):

        """ Will be called when the Common app is first loaded """
        self.add_instance_name()
        self.add_default_settings()

    def add_instance_name(self):
        """
        Check if an InstanceName has been defined for this database.
        If not, create a random one!
        """

        # See note above
        from .models import InvenTreeSetting

        """
        Note: The "old" instance name was stored under the key 'InstanceName',
        but has now been renamed to 'INVENTREE_INSTANCE'.
        """

        try:

            # Quick exit if a value already exists for 'inventree_instance'
            if InvenTreeSetting.objects.filter(key='INVENTREE_INSTANCE').exists():
                return

            # Default instance name
            instance_name = 'InvenTree Server'

            # Use the old name if it exists
            if InvenTreeSetting.objects.filter(key='InstanceName').exists():
                instance = InvenTreeSetting.objects.get(key='InstanceName')
                instance_name = instance.value

                # Delete the legacy key
                instance.delete()

            # Create new value
            InvenTreeSetting.objects.create(
                key='INVENTREE_INSTANCE',
                value=instance_name
            )

        except (OperationalError, ProgrammingError):
            # Migrations have not yet been applied - table does not exist
            pass

    def add_default_settings(self):
        """
        Create all required settings, if they do not exist.
        """

        from .models import InvenTreeSetting

        for key in InvenTreeSetting.DEFAULT_VALUES.keys():
            try:
                settings = InvenTreeSetting.objects.filter(key__iexact=key)

                if settings.count() == 0:
                    value = InvenTreeSetting.DEFAULT_VALUES[key]

                    print(f"Creating default setting for {key} -> '{value}'")

                    InvenTreeSetting.objects.create(
                        key=key,
                        value=value
                    )

                    return

                elif settings.count() > 1:
                    # Prevent multiple shadow copies of the same setting!
                    for setting in settings[1:]:
                        setting.delete()

                # Ensure that the key has the correct case
                setting = settings[0]

                if not setting.key == key:
                    setting.key = key
                    setting.save()

            except (OperationalError, ProgrammingError):
                # Table might not yet exist
                pass
