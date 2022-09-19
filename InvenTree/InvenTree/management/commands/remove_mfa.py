"""Custom management command to remove MFA for a user."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Remove MFA for a user."""

    def add_arguments(self, parser):
        """Add the arguments."""
        parser.add_argument('mail', type=str)

    def handle(self, *args, **kwargs):
        """Remove MFA for the supplied user (by mail)."""
        # general settings
        mail = kwargs.get('mail')
        if not mail:
            raise KeyError('A mail is required')
        user = get_user_model()
        mfa_user = [*set(user.objects.filter(email=mail) | user.objects.filter(emailaddress__email=mail))]

        if len(mfa_user) == 0:
            print('No user with this mail associated')
        elif len(mfa_user) > 1:
            print('More than one user found with this mail')
        else:
            # and clean out all MFA methods
            # backup codes
            mfa_user[0].staticdevice_set.all().delete()
            # TOTP tokens
            mfa_user[0].totpdevice_set.all().delete()
            print(f'Removed all MFA methods for user {str(mfa_user[0])}')
