"""Custom management command to remove MFA for a user."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

import structlog

logger = structlog.get_logger('inventree')


class Command(BaseCommand):
    """Remove MFA for a user."""

    def add_arguments(self, parser):
        """Add the arguments."""
        parser.add_argument('mail', type=str)

    def handle(self, *args, mail, **kwargs):
        """Remove MFA for the supplied user (by mail)."""
        user = get_user_model()
        mfa_user = [
            *set(
                user.objects.filter(email=mail)
                | user.objects.filter(emailaddress__email=mail)
            )
        ]

        if len(mfa_user) == 0:
            logger.warning('No user with this mail associated')
        elif len(mfa_user) > 1:
            mails = {a.email for a in mfa_user} | {
                b.email for a in mfa_user for b in a.emailaddress_set.all()
            }
            users = [a.username for a in mfa_user]
            logger.error(
                f"More than one user found with this mail; found users '{', '.join(users)}' with them following mails '{', '.join(mails)}"
            )
        else:
            # and clean out all MFA methods
            auths = mfa_user[0].authenticator_set.all()
            length = len(auths)
            auths.delete()

            # log the result
            msg = f'Removed all ({length}) MFA methods for user {mfa_user[0]!s}'
            logger.info(msg)
            print(msg)
            return 'done'
        return False
