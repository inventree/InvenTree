"""AppConfig for approval app."""

from django.apps import AppConfig


class ApprovalConfig(AppConfig):
    """AppConfig for approval app."""
    name = 'approval'

    def ready(self):
        """Run setup step when app is ready."""
        self.collect_notification_methods()

    def collect_notification_methods(self):
        """Collect all rule definitions."""
        from approval.rules import registry

        registry.collect()
