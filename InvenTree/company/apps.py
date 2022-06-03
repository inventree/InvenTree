"""Config for the 'company' app"""

from django.apps import AppConfig


class CompanyConfig(AppConfig):
    """Config class for the 'company' app"""

    name = 'company'

    def ready(self):
        """This function is called whenever the Company app is loaded."""
        pass
