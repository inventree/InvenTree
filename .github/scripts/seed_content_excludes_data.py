"""Script to seed test data for the 'content-excludes' export CI job.

'export-records' can optionally include/exclude several categories of data
(email logs, API tokens, SSO app/token data, user sessions, and group/user
permissions) via --include-x / --exclude-x flags. Toggling one of those flags
only proves anything if the source database actually contains a row in that
category to begin with - otherwise "the export doesn't contain it" is true
regardless of whether the flag/exclusion logic works at all.

This script creates exactly one row in each such category, so the
import_export.yaml workflow's content-excludes job can meaningfully assert
both "included when asked for" and "excluded by default".

Intended to be run from 'src/backend/InvenTree', e.g.:
    cd src/backend/InvenTree && python ../../../.github/scripts/seed_content_excludes_data.py
"""

import os
import sys

sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'InvenTree.settings')

import django

django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.sessions.backends.db import SessionStore

from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from allauth.usersessions.models import UserSession

from common.models import EmailMessage, Priority
from users.models import ApiToken

User = get_user_model()


def main():
    """Seed one row of test data in each optional export/import category."""
    user = User.objects.filter(is_superuser=True).first()

    if user is None:
        print('Error: no superuser found - run `invoke dev.setup-test` first')
        sys.exit(1)

    # Ensure at least one group has a non-empty permission set, so toggling
    # --include-permissions has something real to include/strip. Doesn't need
    # to be a group the superuser belongs to - InvenTree's RuleSet groups
    # already have permissions assigned regardless of membership.
    group = Group.objects.first()

    if group is None:
        print('Error: no groups found - run `invoke dev.setup-test` first')
        sys.exit(1)

    if not group.permissions.exists():
        group.permissions.add(Permission.objects.first())
        print(f"- Added a permission to group '{group.name}' (was empty)")
    else:
        print(f"- Group '{group.name}' already has permissions")

    # Email log entry (thread is auto-created by EmailMessage.save() if omitted)
    EmailMessage.objects.get_or_create(
        subject='CI content-excludes test email',
        defaults={
            'body': 'CI content-excludes test email body',
            'to': 'ci-recipient@example.com',
            'sender': 'ci-sender@example.com',
            'priority': Priority.NORMAL,
        },
    )
    print('- Created email log entry')

    # API token
    ApiToken.objects.get_or_create(user=user, name='ci-content-excludes-token')
    print('- Created API token')

    # SSO application + linked account + token
    app, _ = SocialApp.objects.get_or_create(
        provider='google',
        name='CI Content-Excludes Test App',
        defaults={'client_id': 'ci-test-client-id'},
    )
    account, _ = SocialAccount.objects.get_or_create(
        user=user, provider='google', uid='ci-test-external-uid'
    )
    SocialToken.objects.get_or_create(
        app=app, account=account, defaults={'token': 'ci-test-token-value'}
    )
    print('- Created SSO application, account and token')

    # A real, properly-encoded session (avoids writing an undecodable session_data blob)
    store = SessionStore()
    store['ci_content_excludes_test'] = True
    store.create()
    print('- Created session entry')

    # allauth user-session record (tracked separately from the raw Session table)
    UserSession.objects.get_or_create(
        session_key='ci-content-excludes-user-session',
        defaults={'user': user, 'ip': '127.0.0.1', 'user_agent': 'ci-test-agent'},
    )
    print('- Created user session entry')

    print('Content-excludes seed data created successfully')


if __name__ == '__main__':
    main()
