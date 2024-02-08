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

| config key | ENV Variable | Description |
| --- | --- | --- |
| `ldap.enabled` | `INVENTREE_LDAP_ENABLED` | Set this to `True` to enable LDAP. |
| `ldap.debug` | `INVENTREE_LDAP_DEBUG` | Set this to `True` to activate debug mode, useful for troubleshooting ldap configurations. |
| `ldap.server_uri` | `INVENTREE_LDAP_SERVER_URI` | LDAP Server URI, e.g. `ldaps://example.org` |
| `ldap.start_tls` | `INVENTREE_LDAP_START_TLS` | Enable TLS encryption over the standard LDAP port, [see](https://django-auth-ldap.readthedocs.io/en/latest/reference.html#auth-ldap-start-tls). (You can set TLS options via `ldap.global_options`) |
| `ldap.bind_dn` | `INVENTREE_LDAP_BIND_DN` | LDAP bind dn, e.g. `cn=admin,dc=example,dc=org` |
| `ldap.bind_password` | `INVENTREE_LDAP_BIND_PASSWORD` | LDAP bind password |
| `ldap.search_base_dn` | `INVENTREE_LDAP_SEARCH_BASE_DN` | LDAP search base dn, e.g. `cn=Users,dc=example,dc=org` |
| `ldap.user_dn_template` | `INVENTREE_LDAP_USER_DN_TEMPLATE` | use direct bind as auth user, `ldap.bind_dn` and `ldap.bin_password` is not necessary then, e.g. `uid=%(user)s,dc=example,dc=org` |
| `ldap.global_options` | `INVENTREE_LDAP_GLOBAL_OPTIONS` | set advanced options as dict, e.g. TLS settings. For a list of all available options, see [python-ldap docs](https://www.python-ldap.org/en/latest/reference/ldap.html#ldap-options). (keys and values starting with OPT_ get automatically converted to `python-ldap` keys) |
| `ldap.search_filter_str`| `INVENTREE_LDAP_SEARCH_FILTER_STR` | LDAP search filter str, default: `uid=%(user)s` |
| `ldap.user_attr_map` | `INVENTREE_LDAP_USER_ATTR_MAP` | LDAP <-> Inventree user attribute map, can be json if used as env, in yml directly specify the object. default: `{"first_name": "givenName", "last_name": "sn", "email": "mail"}` |
| `ldap.always_update_user` | `INVENTREE_LDAP_ALWAYS_UPDATE_USER` | Always update the user on each login, default: `true` |
| `ldap.cache_timeout` | `INVENTREE_LDAP_CACHE_TIMEOUT` | cache timeout to reduce traffic with LDAP server, default: `3600` (1h) |
| `ldap.group_search` | `INVENTREE_LDAP_GROUP_SEARCH` | Base LDAP DN for group searching; required to enable group features |
| `ldap.require_group` | `INVENTREE_LDAP_REQUIRE_GROUP` | If set, users _must_ be in this group to log in to InvenTree |
| `ldap.deny_group` | `INVENTREE_LDAP_DENY_GROUP` | If set, users _must not_ be in this group to log in to InvenTree |
| `ldap.user_flags_by_group` | `INVENTREE_LDAP_USER_FLAGS_BY_GROUP` | LDAP group to InvenTree user flag map, can be json if used as env, in yml directly specify the object. See config template for example, default: `{}` |


## Tracing support

Starting with 0.14.0 InvenTree supports sending traces, logs and metrics to OpenTelemetry compatible endpoints (both HTTP and gRPC). A [list of vendors](https://opentelemetry.io/ecosystem/vendors) is available on the project site.
This can be used to track usage and performance of the InvenTree backend and connected services like databases, caches and more.

| config key | ENV Variable | Description |
| --- | --- | --- |
| `tracing.enabled` | `INVENTREE_TRACING_ENABLED` | Set this to `True` to enable OpenTelemetry. |
| `tracing.endpoint` | `INVENTREE_TRACING_ENDPOINT` | General endpoint for information (not specific trace/log url) |
| `tracing.headers` | `INVENTREE_TRACING_HEADERS` | HTTP headers that should be send with every request (often used for authentication). Format as a dict. |
| `tracing.auth.basic` | `INVENTREE_TRACING_AUTH_BASIC` | Auth headers that should be send with every requests (will be encoded to b64 and overwrite auth headers) |
| `tracing.is_http` | `INVENTREE_TRACING_IS_HTTP` | Are the endpoints HTTP (True, default) or gRPC (False) |
| `tracing.append_http` | `INVENTREE_TRACING_APPEND_HTTP` | Append default url routes (v1) to `tracing.endpoint` |
| `tracing.console` | `INVENTREE_TRACING_CONSOLE` | Print out all exports (additionally) to the console for debugging. Do not use in production |
| `tracing.resources` | `INVENTREE_TRACING_RESOURCES` | Add additional resources to all exports. This can be used to add custom tags to the traces. Format as a dict. |

## Multi Site Support

If your InvenTree instance is used in a multi-site environment, you can enable multi-site support. Note that supporting multiple sites is well outside the scope of most InvenTree installations. If you know what you are doing, and have a good reason to enable multi-site support, you can do so by setting the `INVENTREE_SITE_MULTI` environment variable to `True`.

!!! tip "Django Documentation"
    For more information on multi-site support, refer to the [Django documentation](https://docs.djangoproject.com/en/3.2/ref/contrib/sites/).

| Environment Variable | Config Key | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_SITE_MULTI | site_multi | Enable multiple sites | False |
| INVENTREE_SITE_ID | site_id | Specify a fixed site ID | *Not specified* |
