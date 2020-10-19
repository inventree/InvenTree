from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError


class CommonConfig(AppConfig):
    name = 'common'

    def ready(self):

        """ Will be called when the Common app is first loaded """
        self.add_instance_name()

    def add_instance_name(self):
        """
        Check if an InstanceName has been defined for this database.
        If not, create a random one!
        """

        # See note above
        from .models import InvenTreeSetting

        try:
            if not InvenTreeSetting.objects.filter(key='InstanceName').exists():

                name = InvenTreeSetting(
                    key="InstanceName",
                    value="InvenTree Server"
                )

                name.save()
        except (OperationalError, ProgrammingError):
            # Migrations have not yet been applied - table does not exist
            pass
