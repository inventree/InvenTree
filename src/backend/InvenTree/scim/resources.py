"""Mapping helpers between Django User/Group objects and SCIM resource models."""

import re

from django.contrib.auth.models import Group as DjangoGroup
from django.contrib.auth.models import User as DjangoUser
from django.urls import reverse

from scim2_models import Email, Group, GroupMember, GroupMembership, Meta, Name, User

#: Simple filter grammar supported by this SCIM implementation: `<attr> eq "<value>"`
FILTER_RE = re.compile(r'^\s*(\w+)\s+eq\s+"([^"]*)"\s*$', re.IGNORECASE)


def parse_filter(filter_string: str | None) -> tuple[str, str] | None:
    """Parse a (very limited) SCIM filter expression of the form `attribute eq "value"`.

    This covers the filters that Identity Providers actually issue in practice
    (existence checks by userName / displayName before provisioning a new
    resource) - the full SCIM filter grammar is not implemented.
    """
    if not filter_string:
        return None

    match = FILTER_RE.match(filter_string)

    if not match:
        return None

    return match.group(1).lower(), match.group(2)


def user_location(pk) -> str:
    """Return the canonical SCIM location URL for a given user id."""
    return reverse('scim-user-detail', kwargs={'pk': pk})


def group_location(pk) -> str:
    """Return the canonical SCIM location URL for a given group id."""
    return reverse('scim-group-detail', kwargs={'pk': pk})


def user_to_scim(user: DjangoUser) -> User:
    """Convert a Django User instance into a SCIM User resource."""
    name = None
    if user.first_name or user.last_name:
        name = Name(
            given_name=user.first_name or None, family_name=user.last_name or None
        )

    emails = [Email(value=user.email, primary=True)] if user.email else None

    groups = [
        GroupMembership(value=str(group.pk), display=group.name, type='direct')
        for group in user.groups.all()
    ] or None

    return User(
        id=str(user.pk),
        user_name=user.username,
        name=name,
        emails=emails,
        active=user.is_active,
        groups=groups,
        meta=Meta(
            resource_type='User',
            created=user.date_joined,
            last_modified=user.last_login or user.date_joined,
            location=user_location(user.pk),
        ),
    )


def apply_scim_to_user(scim_user: User, user: DjangoUser) -> DjangoUser:
    """Apply the fields of a SCIM User resource onto a Django User instance."""
    if scim_user.user_name:
        user.username = scim_user.user_name

    if scim_user.name:
        if scim_user.name.given_name is not None:
            user.first_name = scim_user.name.given_name
        if scim_user.name.family_name is not None:
            user.last_name = scim_user.name.family_name

    if scim_user.emails:
        primary = next((e for e in scim_user.emails if e.primary), scim_user.emails[0])
        if primary.value:
            user.email = primary.value

    if scim_user.active is not None:
        user.is_active = scim_user.active

    if scim_user.password:
        user.set_password(scim_user.password)

    return user


def group_to_scim(group: DjangoGroup) -> Group:
    """Convert a Django Group instance into a SCIM Group resource."""
    members = [
        GroupMember(value=str(user.pk), display=user.username, type='User')
        for user in group.user_set.all()
    ] or None

    return Group(
        id=str(group.pk),
        display_name=group.name,
        members=members,
        meta=Meta(resource_type='Group', location=group_location(group.pk)),
    )


def apply_scim_to_group(scim_group: Group, group: DjangoGroup) -> DjangoGroup:
    """Apply the fields of a SCIM Group resource onto a Django Group instance."""
    if scim_group.display_name:
        group.name = scim_group.display_name

    return group


def set_group_members(group: DjangoGroup, members: list[GroupMember] | None) -> None:
    """Replace the membership of a Django Group based on a list of SCIM GroupMember entries.

    Membership changes are applied via `user.groups` (rather than
    `group.user_set`) so that InvenTree's own `m2m_changed` signal handlers
    (which assume the changed instance is a User) fire correctly.
    """
    if members is None:
        return

    target_ids = {member.value for member in members if member.value}
    current_ids = {str(pk) for pk in group.user_set.values_list('pk', flat=True)}

    for user in DjangoUser.objects.filter(pk__in=target_ids - current_ids):
        user.groups.add(group)

    for user in DjangoUser.objects.filter(pk__in=current_ids - target_ids):
        user.groups.remove(group)
