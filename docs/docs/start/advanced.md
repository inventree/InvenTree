---
title: Advanced Topics
---

## Version Information

Starting with version 0.12 (and later), InvenTree includes more version information.

To view this information, navigate to the "About" page in the top menu bar and select "copy version information" on the bottom corner.

### Contained Information

The version information contains the following information extracted form the instance:

| Name | Always | Sample | Source |
| --- | --- | --- | --- |
| InvenTree-Version | Yes | 0.12.0 dev | instance |
| Django Version | Yes | 3.2.19 | instance |
| Commit Hash | No | aebff26 | environment: `INVENTREE_COMMIT_HASH`, git |
| Commit Date | No | 2023-06-10 | environment: `INVENTREE_COMMIT_DATE`, git |
| Commit Branch | No | master | environment: `INVENTREE_PKG_BRANCH`, git |
| Database | Yes | postgresql | environment: `INVENTREE_DB_*`, config: `database` - see [config](./config.md#database-options) |
| Debug-Mode | Yes | False | environment: `INVENTREE_DEBUG`, config: `config` - see [config](./config.md#basic-options) |
| Deployed using Docker | Yes | True | environment: `INVENTREE_DOCKER` |
| Platform | Yes | Linux-5.15.0-67-generic-x86_64 | instance |
| Installer | Yes | PKG | environment: `INVENTREE_PKG_INSTALLER`, instance |
| Target | No | ubuntu:20.04 | environment: `INVENTREE_PKG_TARGET` |
| Active plugins | Yes | [{'name': 'InvenTreeBarcode', 'slug': 'inventreebarcode', 'version': '2.0.0'}] | instance |

### Installer codes

The installer code is used to identify the way InvenTree was installed. If you vendor InvenTree, you can and should set the installer code to your own value to make sure debugging goes smoothly.

| Code | Description | Official |
| --- | --- | --- |
| PKG | Installed using a package manager | Yes |
| GIT | Installed using git | Yes |
| DOC | Installed using docker | Yes |
| DIO | Installed using digital ocean marketplace[^1] | No |

[^1]: Starting with fresh installs of 0.12.0 this code is set. Versions installed before 0.12.0 do not have this code set even after upgrading to 0.12.0.

## Authentication

### LDAP

You can link your InvenTree server to an LDAP server.

!!! warning "Important"
    This feature is currently only available for docker installs.

Next you can start configuring the connection. Either use the config file or set the environment variables.

{{ configtable() }}
{{ configsetting("INVENTREE_LDAP_ENABLED") }} Enable LDAP support |
{{ configsetting("INVENTREE_LDAP_DEBUG") }} Set this to `True` to activate debug mode, useful for troubleshooting ldap configurations. |
| `INVENTREE_LDAP_SERVER_URI` | `ldap.server_uri` | LDAP Server URI, e.g. `ldaps://example.org` |
| `INVENTREE_LDAP_START_TLS` | `ldap.start_tls` | Enable TLS encryption over the standard LDAP port, [see](https://django-auth-ldap.readthedocs.io/en/latest/reference.html#auth-ldap-start-tls). (You can set TLS options via `ldap.global_options`) |
| `INVENTREE_LDAP_BIND_DN` | `ldap.bind_dn` | LDAP bind dn, e.g. `cn=admin,dc=example,dc=org` |
| `INVENTREE_LDAP_BIND_PASSWORD` | `ldap.bind_password` | LDAP bind password |
| `INVENTREE_LDAP_SEARCH_BASE_DN` | `ldap.search_base_dn` | LDAP search base dn, e.g. `cn=Users,dc=example,dc=org` |
| `INVENTREE_LDAP_USER_DN_TEMPLATE` | `ldap.user_dn_template` | use direct bind as auth user, `ldap.bind_dn` and `ldap.bin_password` is not necessary then, e.g. `uid=%(user)s,dc=example,dc=org` |
| `INVENTREE_LDAP_GLOBAL_OPTIONS` | `ldap.global_options` | set advanced options as dict, e.g. TLS settings. For a list of all available options, see [python-ldap docs](https://www.python-ldap.org/en/latest/reference/ldap.html#ldap-options). (keys and values starting with OPT_ get automatically converted to `python-ldap` keys) |
| `INVENTREE_LDAP_SEARCH_FILTER_STR`| `ldap.search_filter_str` | LDAP search filter str, default: `uid=%(user)s` |
| `INVENTREE_LDAP_USER_ATTR_MAP` | `ldap.user_attr_map` | LDAP <-> InvenTree user attribute map, can be json if used as env, in yml directly specify the object. default: `{"first_name": "givenName", "last_name": "sn", "email": "mail"}` |
| `INVENTREE_LDAP_ALWAYS_UPDATE_USER` | `ldap.always_update_user` | Always update the user on each login, default: `true` |
| `INVENTREE_LDAP_CACHE_TIMEOUT` | `ldap.cache_timeout` | cache timeout to reduce traffic with LDAP server, default: `3600` (1h) |
| `INVENTREE_LDAP_GROUP_SEARCH` | `ldap.group_search` | Base LDAP DN for group searching; required to enable group features |
| `INVENTREE_LDAP_GROUP_OBJECT_CLASS` | `ldap.group_object_class` | The string to pass to the LDAP group search `(objectClass=<...>)`, default: `groupOfUniqueNames` |
| `INVENTREE_LDAP_MIRROR_GROUPS` | `ldap.mirror_groups` | If `True`, mirror a user's LDAP group membership in the Django database, default: `False` |
| `INVENTREE_LDAP_GROUP_TYPE_CLASS` | `ldap.group_type_class` | The group class to be imported from `django_auth_ldap.config` as a string, default: `'GroupOfUniqueNamesType'`|
| `INVENTREE_LDAP_GROUP_TYPE_CLASS_ARGS` | `ldap.group_type_class_args` | A `list` of positional args to pass to the LDAP group type class, default `[]` |
| `INVENTREE_LDAP_GROUP_TYPE_CLASS_KWARGS` | `ldap.group_type_class_kwargs` | A `dict` of keyword args to pass to the LDAP group type class, default `{'name_attr': 'cn'}` |
| `INVENTREE_LDAP_REQUIRE_GROUP` | `ldap.require_group` | If set, users _must_ be in this group to log in to InvenTree |
| `INVENTREE_LDAP_DENY_GROUP` | `ldap.deny_group` | If set, users _must not_ be in this group to log in to InvenTree |
| `INVENTREE_LDAP_USER_FLAGS_BY_GROUP` | `ldap.user_flags_by_group` | LDAP group to InvenTree user flag map, can be json if used as env, in yml directly specify the object. See config template for example, default: `{}` |

## Tracing support

Starting with 0.14.0 InvenTree supports sending traces, logs and metrics to OpenTelemetry compatible endpoints (both HTTP and gRPC). A [list of vendors](https://opentelemetry.io/ecosystem/vendors) is available on the project site.
This can be used to track usage and performance of the InvenTree backend and connected services like databases, caches and more.

{{ configtable() }}
{{ configsetting("INVENTREE_TRACING_ENABLED") }} Enable OpenTelemetry |
{{ configsetting("INVENTREE_TRACING_ENDPOINT") }} General endpoint for information (not specific trace/log url) |
{{ configsetting("INVENTREE_TRACING_HEADERS") }} HTTP headers that should be send with every request (often used for authentication). Format as a dict. |
{{ configsetting("INVENTREE_TRACING_AUTH") }} Auth headers that should be send with every requests (will be encoded to b64 and overwrite auth headers) |
{{ configsetting("INVENTREE_TRACING_IS_HTTP") }} Are the endpoints HTTP (True, default) or gRPC (False) |
{{ configsetting("INVENTREE_TRACING_APPEND_HTTP") }} Append default url routes (v1) to `tracing.endpoint` |
{{ configsetting("INVENTREE_TRACING_CONSOLE") }} Print out all exports (additionally) to the console for debugging. Do not use in production |
{{ configsetting("INVENTREE_TRACING_RESOURCES") }} Add additional resources to all exports. This can be used to add custom tags to the traces. Format as a dict. |

## Multi Site Support

If your InvenTree instance is used in a multi-site environment, you can enable multi-site support. Note that supporting multiple sites is well outside the scope of most InvenTree installations. If you know what you are doing, and have a good reason to enable multi-site support, you can do so by setting the `INVENTREE_SITE_MULTI` environment variable to `True`.

!!! tip "Django Documentation"
    For more information on multi-site support, refer to the [Django documentation]({% include "django.html" %}/ref/contrib/sites/).

{{ configtable() }}
{{ configsetting("INVENTREE_SITE_MULTI") }} Enable multiple sites |
{{ configsetting("INVENTREE_SITE_ID") }} Specify a fixed site ID |
