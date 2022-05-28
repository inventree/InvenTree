from django.apps import AppConfig


class CompanyConfig(AppConfig):
    name = 'company'

    def ready(self):
        """This function is called whenever the Company app is loaded."""
        pass
