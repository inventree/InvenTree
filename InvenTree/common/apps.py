from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError, IntegrityError


class CommonConfig(AppConfig):
    name = 'common'

    def ready(self):
        pass
