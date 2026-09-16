"""Helper functions for Single Sign On functionality."""

import json

from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

import structlog
from allauth.socialaccount.models import SocialAccount, SocialLogin

from common.settings import get_global_setting

logger = structlog.get_logger('inventree')


def ensure_sso_groups(sender, sociallogin: SocialLogin, **kwargs):
    """Sync groups from IdP each time a SSO user logs on.

    This event listener is registered in the apps ready method.
    """
    if not get_global_setting('LOGIN_ENABLE_SSO_GROUP_SYNC'):
        return

    group_key = get_global_setting('SSO_GROUP_KEY')
    group_map = json.loads(get_global_setting('SSO_GROUP_MAP'))
    # map SSO groups to InvenTree groups
    group_names = []
    for sso_group in sociallogin.account.extra_data.get('userinfo', {}).get(
        group_key, []
    ):
        if mapped_name := group_map.get(sso_group):
            group_names.append(mapped_name)

    # ensure user has groups
    user = sociallogin.account.user

    for group_name in group_names:
        try:
            user.groups.get(name=group_name)
        except Group.DoesNotExist:
            # user not in group yet
            try:
                group = Group.objects.get(name=group_name)
            except Group.DoesNotExist:
                logger.info(f'Creating group {group_name} as it did not exist')
                group = Group(name=group_name)
                group.save()
            logger.info(f'Adding group {group_name} to user {user}')
            user.groups.add(group)

    # remove groups not listed by SSO if not disabled
    if get_global_setting('SSO_REMOVE_GROUPS'):
        for group in user.groups.all():
            if group.name not in group_names:
                logger.info(f'Removing group {group.name} from {user}')
                user.groups.remove(group)


@receiver(post_save, sender=SocialAccount)
def on_social_account_created(sender, instance: SocialAccount, created: bool, **kwargs):
    """Sync SSO groups when new SocialAccount is added.

    Since the allauth `social_account_added` signal is not sent for some reason, this
    signal is simulated using post_save signals. The issue has been reported as
    https://github.com/pennersr/django-allauth/issues/3834
    """
    if created:
        ensure_sso_groups(None, SocialLogin(account=instance))
