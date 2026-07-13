"""Tests for LDAP configuration handling.

Verifies that missing ``ldap.group_search`` does not cause runtime crashes
and that ``find_group_perms`` is properly configurable.
"""

import importlib
from unittest import mock

import pytest


@pytest.fixture
def ldap_module():
    """Import the ldap setting module fresh for each test."""
    # The module imports django_auth_ldap and ldap at function level,
    # so we can import it directly without those packages installed
    # as long as we mock them for the get_ldap_config call.
    import InvenTree.InvenTree.setting.ldap as ldap_mod
    importlib.reload(ldap_mod)
    return ldap_mod


class TestLdapGroupSearchMissing:
    """Tests for graceful handling of missing ldap.group_search (see #12225)."""

    def test_find_group_perms_disabled_when_group_search_missing(self, ldap_module):
        """When group_search is None, find_group_perms must be False."""
        with mock.patch.object(ldap_module, 'get_setting') as gs, \
             mock.patch.object(ldap_module, 'get_boolean_setting') as gbs:

            # get_setting: return None for group_search, defaults for others
            def gs_side_effect(env_key, yaml_key, *args, **kwargs):
                if 'GROUP_SEARCH' in env_key:
                    return None
                if 'GLOBAL_OPTIONS' in env_key:
                    return kwargs.get('default_value', {}) or {}
                if 'GROUP_TYPE_CLASS_ARGS' in env_key:
                    return kwargs.get('default_value', []) if 'default_value' in kwargs else []
                if 'GROUP_TYPE_CLASS_KWARGS' in env_key:
                    return kwargs.get('default_value', {}) or {}
                return kwargs.get('default_value', None)

            gs.side_effect = gs_side_effect

            # get_boolean_setting: return True for find_group_perms, False for others
            def gbs_side_effect(env_key, yaml_key, default):
                if 'FIND_GROUP_PERMS' in env_key:
                    return True
                return default

            gbs.side_effect = gbs_side_effect

            # Mock the imports inside get_ldap_config
            with mock.patch('django_auth_ldap.config') as mock_config:
                mock_config.LDAPSearch.return_value = mock.MagicMock()
                mock_config.GroupOfUniqueNamesType.return_value = mock.MagicMock()

                with mock.patch('ldap') as mock_ldap:
                    mock_ldap.SCOPE_SUBTREE = 2
                    mock_ldap.OPT_REFERRALS = 0

                    config = ldap_module.get_ldap_config(debug=False)

            assert config['AUTH_LDAP_FIND_GROUP_PERMS'] is False
            assert config['AUTH_LDAP_GROUP_SEARCH'] is None
            assert config['AUTH_LDAP_MIRROR_GROUPS'] is False
            assert config['AUTH_LDAP_REQUIRE_GROUP'] is None
            assert config['AUTH_LDAP_DENY_GROUP'] is None
            assert config['AUTH_LDAP_USER_FLAGS_BY_GROUP'] is None

    def test_find_group_perms_enabled_when_group_search_set(self, ldap_module):
        """When group_search is configured, find_group_perms stays True."""
        with mock.patch.object(ldap_module, 'get_setting') as gs, \
             mock.patch.object(ldap_module, 'get_boolean_setting') as gbs:

            def gs_side_effect(env_key, yaml_key, *args, **kwargs):
                if 'GROUP_SEARCH' in env_key:
                    return 'ou=groups,dc=example,dc=org'
                if 'GLOBAL_OPTIONS' in env_key:
                    return kwargs.get('default_value', {}) or {}
                if 'GROUP_TYPE_CLASS_ARGS' in env_key:
                    return kwargs.get('default_value', []) if 'default_value' in kwargs else []
                if 'GROUP_TYPE_CLASS_KWARGS' in env_key:
                    return kwargs.get('default_value', {}) or {}
                return kwargs.get('default_value', None)

            gs.side_effect = gs_side_effect

            def gbs_side_effect(env_key, yaml_key, default):
                if 'FIND_GROUP_PERMS' in env_key:
                    return True
                return default

            gbs.side_effect = gbs_side_effect

            with mock.patch('django_auth_ldap.config') as mock_config:
                mock_config.LDAPSearch.return_value = mock.MagicMock()
                mock_config.GroupOfUniqueNamesType.return_value = mock.MagicMock()

                with mock.patch('ldap') as mock_ldap:
                    mock_ldap.SCOPE_SUBTREE = 2

                    config = ldap_module.get_ldap_config(debug=False)

            assert config['AUTH_LDAP_FIND_GROUP_PERMS'] is True
            assert config['AUTH_LDAP_GROUP_SEARCH'] is not None

    def test_find_group_perms_can_be_disabled_explicitly(self, ldap_module):
        """User can set find_group_perms=False even when group_search is set."""
        with mock.patch.object(ldap_module, 'get_setting') as gs, \
             mock.patch.object(ldap_module, 'get_boolean_setting') as gbs:

            def gs_side_effect(env_key, yaml_key, *args, **kwargs):
                if 'GROUP_SEARCH' in env_key:
                    return 'ou=groups,dc=example,dc=org'
                if 'GLOBAL_OPTIONS' in env_key:
                    return kwargs.get('default_value', {}) or {}
                if 'GROUP_TYPE_CLASS_ARGS' in env_key:
                    return kwargs.get('default_value', []) if 'default_value' in kwargs else []
                if 'GROUP_TYPE_CLASS_KWARGS' in env_key:
                    return kwargs.get('default_value', {}) or {}
                return kwargs.get('default_value', None)

            gs.side_effect = gs_side_effect

            def gbs_side_effect(env_key, yaml_key, default):
                if 'FIND_GROUP_PERMS' in env_key:
                    return False
                return default

            gbs.side_effect = gbs_side_effect

            with mock.patch('django_auth_ldap.config') as mock_config:
                mock_config.LDAPSearch.return_value = mock.MagicMock()
                mock_config.GroupOfUniqueNamesType.return_value = mock.MagicMock()

                with mock.patch('ldap') as mock_ldap:
                    mock_ldap.SCOPE_SUBTREE = 2

                    config = ldap_module.get_ldap_config(debug=False)

            assert config['AUTH_LDAP_FIND_GROUP_PERMS'] is False
            # Group search is still configured (user might use it for other features)
            assert config['AUTH_LDAP_GROUP_SEARCH'] is not None