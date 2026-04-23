"""Configuration of LDAP support for InvenTree."""

from InvenTree.config import get_boolean_setting, get_setting


def get_ldap_config(debug: bool = False) -> dict:
    """Return a dictionary of LDAP configuration settings.

    The returned settings will be updated into the globals() object,
    and will be used to configure the LDAP authentication backend.
    """
    import django_auth_ldap.config  # type: ignore[unresolved-import]
    import ldap  # type: ignore[unresolved-import]

    # get global options from dict and use ldap.OPT_* as keys and values
    global_options_dict = get_setting(
        'INVENTREE_LDAP_GLOBAL_OPTIONS',
        'ldap.global_options',
        default_value=None,
        typecast=dict,
    )

    global_options = {}

    for k, v in global_options_dict.items():
        # keys are always ldap.OPT_* constants
        k_attr = getattr(ldap, k, None)
        if not k.startswith('OPT_') or k_attr is None:
            print(f"[LDAP] ldap.global_options, key '{k}' not found, skipping...")
            continue

        # values can also be other strings, e.g. paths
        v_attr = v
        if v.startswith('OPT_'):
            v_attr = getattr(ldap, v, None)

        if v_attr is None:
            print(f"[LDAP] ldap.global_options, value key '{v}' not found, skipping...")
            continue

        global_options[k_attr] = v_attr

    if debug:
        print('[LDAP] ldap.global_options =', global_options)

    group_type_class = get_setting(
        'INVENTREE_LDAP_GROUP_TYPE_CLASS',
        'ldap.group_type_class',
        'GroupOfUniqueNamesType',
        str,
    )

    group_type_class_args = get_setting(
        'INVENTREE_LDAP_GROUP_TYPE_CLASS_ARGS', 'ldap.group_type_class_args', [], list
    )

    group_type_class_kwargs = get_setting(
        'INVENTREE_LDAP_GROUP_TYPE_CLASS_KWARGS',
        'ldap.group_type_class_kwargs',
        {'name_attr': 'cn'},
        dict,
    )

    group_object_class = get_setting(
        'INVENTREE_LDAP_GROUP_OBJECT_CLASS',
        'ldap.group_object_class',
        'groupOfUniqueNames',
        str,
    )

    ldap_config = {
        'AUTH_LDAP_GLOBAL_OPTIONS': global_options,
        'AUTH_LDAP_SERVER_URI': get_setting(
            'INVENTREE_LDAP_SERVER_URI', 'ldap.server_uri'
        ),
        'AUTH_LDAP_START_TLS': get_boolean_setting(
            'INVENTREE_LDAP_START_TLS', 'ldap.start_tls', False
        ),
        'AUTH_LDAP_BIND_DN': get_setting('INVENTREE_LDAP_BIND_DN', 'ldap.bind_dn'),
        'AUTH_LDAP_BIND_PASSWORD': get_setting(
            'INVENTREE_LDAP_BIND_PASSWORD', 'ldap.bind_password'
        ),
        'AUTH_LDAP_USER_SEARCH': django_auth_ldap.config.LDAPSearch(
            get_setting('INVENTREE_LDAP_SEARCH_BASE_DN', 'ldap.search_base_dn'),
            ldap.SCOPE_SUBTREE,
            str(
                get_setting(
                    'INVENTREE_LDAP_SEARCH_FILTER_STR',
                    'ldap.search_filter_str',
                    '(uid= %(user)s)',
                )
            ),
        ),
        'AUTH_LDAP_USER_DN_TEMPLATE': get_setting(
            'INVENTREE_LDAP_USER_DN_TEMPLATE', 'ldap.user_dn_template'
        ),
        'AUTH_LDAP_USER_ATTR_MAP': get_setting(
            'INVENTREE_LDAP_USER_ATTR_MAP',
            'ldap.user_attr_map',
            {'first_name': 'givenName', 'last_name': 'sn', 'email': 'mail'},
            dict,
        ),
        'AUTH_LDAP_ALWAYS_UPDATE_USER': get_boolean_setting(
            'INVENTREE_LDAP_ALWAYS_UPDATE_USER', 'ldap.always_update_user', True
        ),
        'AUTH_LDAP_CACHE_TIMEOUT': get_setting(
            'INVENTREE_LDAP_CACHE_TIMEOUT', 'ldap.cache_timeout', 3600, int
        ),
        'AUTH_LDAP_MIRROR_GROUPS': get_boolean_setting(
            'INVENTREE_LDAP_MIRROR_GROUPS', 'ldap.mirror_groups', False
        ),
        'AUTH_LDAP_GROUP_OBJECT_CLASS': group_object_class,
        'AUTH_LDAP_GROUP_SEARCH': django_auth_ldap.config.LDAPSearch(
            get_setting('INVENTREE_LDAP_GROUP_SEARCH', 'ldap.group_search'),
            ldap.SCOPE_SUBTREE,
            f'(objectClass={group_object_class})',
        ),
        'AUTH_LDAP_GROUP_TYPE_CLASS': group_type_class,
        'AUTH_LDAP_GROUP_TYPE_CLASS_ARGS': [*group_type_class_args],
        'AUTH_LDAP_GROUP_TYPE_CLASS_KWARGS': {**group_type_class_kwargs},
        'AUTH_LDAP_GROUP_TYPE': getattr(django_auth_ldap.config, group_type_class)(
            *group_type_class_args, **group_type_class_kwargs
        ),
        'AUTH_LDAP_REQUIRE_GROUP': get_setting(
            'INVENTREE_LDAP_REQUIRE_GROUP', 'ldap.require_group'
        ),
        'AUTH_LDAP_DENY_GROUP': get_setting(
            'INVENTREE_LDAP_DENY_GROUP', 'ldap.deny_group'
        ),
        'AUTH_LDAP_USER_FLAGS_BY_GROUP': get_setting(
            'INVENTREE_LDAP_USER_FLAGS_BY_GROUP',
            'ldap.user_flags_by_group',
            default_value=None,
            typecast=dict,
        ),
        'AUTH_LDAP_FIND_GROUP_PERMS': True,
    }

    return ldap_config
