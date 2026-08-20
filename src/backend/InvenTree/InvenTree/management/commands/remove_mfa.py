"""Custom management command to remove MFA for a user."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

import structlog

logger = structlog.get_logger('inventree')


class Command(BaseCommand):
    """Remove MFA for a user."""

    def add_arguments(self, parser):
        """Add the arguments."""
        parser.add_argument('--mail', type=str, nargs='?')
        parser.add_argument('--username', type=str, nargs='?')

    def handle(self, *args, mail, username, **kwargs):
        """Remove MFA for the supplied user (by mail or username)."""
        user = get_user_model()
        mfa_user = []
        success = False

        if mail is not None:
            mfa_user = [
                *set(
                    user.objects.filter(email=mail)
                    | user.objects.filter(emailaddress__email=mail)
                )
            ]
            if len(mfa_user) == 0:
                logger.warning('No user with this mail associated')
            elif len(mfa_user) > 1:
                emails_list = ', '.join(
                    sorted(
                        {b.email for a in mfa_user for b in a.emailaddress_set.all()}
                        | {a.email for a in mfa_user}
                    )
                )
                usernames_list = ', '.join(sorted({a.username for a in mfa_user}))
                logger.error(
                    f"Multiple users found with the provided email; Usernames: '{usernames_list}', Emails: '{emails_list}'"
                )
            else:
                # found exactly one user
                success = True

        elif username is not None:
            mfa_user = user.objects.filter(username=username)
            if len(mfa_user) == 0:
                logger.warning('No user with this username associated')
            elif (
                len(mfa_user) > 1
            ):  # pragma: no cover # Should not be possible due to unique constraint
                logger.error('Multiple users found with the provided username')
            else:
                # found exactly one user
                success = True

        else:
            logger.error('No mail or username provided')
            raise ValueError(
                'Error: one of the following arguments is required: mail, username'
            )

        # Clean out all MFA methods
        if success:
            auths = mfa_user[0].authenticator_set.all()
            length = len(auths)
            auths.delete()

            # log the result
            msg = f'Removed all ({length}) MFA methods for user {mfa_user[0]!s}'
            logger.info(msg)
            print(msg)
            return 'done'
        return False
