---
title: InvenTree Configuration
---

## InvenTree Configuration

While many InvenTree options can be configured at "run time", there are a number of system configuration parameters which need to be set *before* running InvenTree. Admin users will need to adjust the InvenTree installation to meet the particular needs of their setup. For example, pointing to the correct database backend, or specifying a list of allowed hosts.

InvenTree system settings can be specified either via environment variables, or in a configuration file.

### Configuration File

To support install specific settings, a simple configuration file `config.yaml` is provided. This configuration file is loaded by the InvenTree server at runtime. Settings specific to a given install should be adjusted in `config.yaml`.

#### Configuration File Location

The InvenTree server tries to locate the `config.yaml` configuration file on startup, in the following locations:

1. Location is specified by the `INVENTREE_CONFIG_FILE` environment variable
2. Located in the same local directory as the InvenTree source code

!!! tip "Config File Location"
    When the InvenTree server boots, it will report the location where it expects to find the configuration file

#### Configuration File Template

The configuration file *template* can be found on [GitHub]({{ sourcefile("src/backend/InvenTree/config_template.yaml") }}), and is shown below:

{{ includefile("src/backend/InvenTree/config_template.yaml", "Configuration File Template", fmt="yaml") }}

!!! info "Template File"
    The default configuration file (as defined by the template linked above) will be copied to the specified configuration file location on first run, if a configuration file is not found in that location.

!!! tip "Restart Server"
    The contents of the configuration file are read when the InvenTree server first launches. If any changes are made to the configuration file, ensure that the server is restarted, so that the changes can be made operational.

### Environment Variables

In addition to specifying InvenTree options via the `config.yaml` file, these options can also be specified via environment variables. This can be useful for system administrators who want the flexibility of altering settings without editing the configuration file.

Environment variable settings generally use the `INVENTREE_` prefix, and are all uppercase.

!!! info "Configuration Priority"
    Configuration options set via environment variables will take priority over the values set in the `config.yaml` file. This can be useful for overriding specific settings without needing to edit the configuration file.

!!! warning "Available Variables"
    Some configuration options cannot be set via environment variables. Refer to the documentation below.

#### List Values

To specify a list value in an environment variable, use a comma-separated list. For example, to specify a list of trusted origins:

```bash
INVENTREE_TRUSTED_ORIGINS='https://inventree.example.com:8443,https://stock.example.com:8443'
```

## Basic Options

The following basic options are available:

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_SITE_URL | site_url | Specify a fixed site URL | *Not specified* |
| INVENTREE_TIMEZONE | timezone | Server timezone | UTC |
| INVENTREE_ADMIN_ENABLED | admin_enabled | Enable the [django administrator interface]({% include "django.html" %}/ref/contrib/admin/) | True |
| INVENTREE_ADMIN_URL | admin_url | URL for accessing [admin interface](../settings/admin.md) | admin |
| INVENTREE_LANGUAGE | language | Default language | en-us |
| INVENTREE_AUTO_UPDATE | auto_update | Database migrations will be run automatically | False |

### Site URL

The *INVENTREE_SITE_URL* option defines the base URL for the InvenTree server. This is a critical setting, and it is required for correct operation of the server. If not specified, the server will attempt to determine the site URL automatically - but this may not always be correct!

The site URL is the URL that users will use to access the InvenTree server. For example, if the server is accessible at `https://inventree.example.com`, the site URL should be set to `https://inventree.example.com`. Note that this is not necessarily the same as the internal URL that the server is running on - the internal URL will depend entirely on your server configuration and may be obscured by a reverse proxy or other such setup.

### Timezone

By default, the InvenTree server is configured to use the UTC timezone. This can be adjusted to your desired local timezone. You can refer to [Wikipedia](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) for a list of available timezones. Use the values specified in the *TZ Identifier* column in the linked page. For example, to change to the United States Pacific timezone, set `INVENTREE_TIMEZONE='America/Los_Angeles'`.

Date and time values are stored in the database in UTC format, and are converted to the selected timezone for display in the user interface or API.

### Auto Update

By default, the InvenTree server will not automatically apply database migrations. When the InvenTree installation is updated (*or a plugin is installed which requires database migrations*), database migrations must be applied manually by the system administrator.

With "auto update" enabled, the InvenTree server will automatically apply database migrations as required. To enable automatic database updates, set `INVENTREE_AUTO_UPDATE` to `True`.

## Debugging and Logging Options

The following debugging / logging options are available:

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_DEBUG | debug | Enable [debug mode](./index.md#debug-mode) | False |
| INVENTREE_DEBUG_QUERYCOUNT | debug_querycount | Enable [query count logging](https://github.com/bradmontgomery/django-querycount) in the terminal | False |
| INVENTREE_DB_LOGGING | db_logging | Enable logging of database messages | False |
| INVENTREE_LOG_LEVEL | log_level | Set level of logging to terminal | WARNING |
| INVENTREE_JSON_LOG | json_log | log as json | False |
| INVENTREE_WRITE_LOG | write_log | Enable writing of log messages to file at config base | False |
| INVENTREE_CONSOLE_LOG | console_log | Enable logging to console | True |

### Debug Mode

Enabling the `INVENTREE_DEBUG` setting will turn on [Django debug mode]({% include "django.html" %}/ref/settings/#debug). This mode is intended for development purposes, and should not be enabled in a production environment. Read more about [InvenTree debug mode](./index.md#debug-mode).

### Query Count Logging

Enabling the `INVENTREE_DEBUG_QUERYCOUNT` setting will log the number of database queries executed for each page load. This can be useful for identifying performance bottlenecks in the InvenTree server. Note that this setting is only available if `INVENTREE_DEBUG` is also enabled.

### Database Logging

Enabling the `INVENTREE_DB_LOGGING` setting will log all database queries to the terminal. This can be useful for debugging database-related issues.

## Server Access

Depending on how your InvenTree installation is configured, you will need to pay careful attention to the following settings. If you are running your server behind a proxy, or want to adjust support for [CORS requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS), one or more of the following settings may need to be adjusted.

!!! warning "Advanced Users"
    The following settings require a certain assumed level of knowledge. You should also refer to the [django documentation]({% include "django.html" %}/ref/settings/) for more information.

!!! danger "Not Secure"
    Allowing access from any host is not secure, and should be adjusted for your installation.

!!! info "Environment Variables"
    Note that a provided environment variable will override the value provided in the configuration file.

!!! success "INVENTREE_SITE_URL"
    If you have specified the `INVENTREE_SITE_URL`, this will automatically be used as a trusted CSRF and CORS host (see below).

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_ALLOWED_HOSTS | allowed_hosts | List of allowed hosts | `*` |
| INVENTREE_TRUSTED_ORIGINS | trusted_origins | List of trusted origins. Refer to the [django documentation]({% include "django.html" %}/ref/settings/#csrf-trusted-origins) | Uses the *INVENTREE_SITE_URL* parameter, if set. Otherwise, an empty list. |
| INVENTREE_CORS_ORIGIN_ALLOW_ALL | cors.allow_all | Allow all remote URLS for CORS checks | `False` |
| INVENTREE_CORS_ORIGIN_WHITELIST | cors.whitelist | List of whitelisted CORS URLs. Refer to the [django-cors-headers documentation](https://github.com/adamchainz/django-cors-headers#cors_allowed_origins-sequencestr) | Uses the *INVENTREE_SITE_URL* parameter, if set. Otherwise, an empty list. |
| INVENTREE_CORS_ORIGIN_REGEX | cors.regex | List of regular expressions for CORS whitelisted URL patterns | *Empty list* |
| INVENTREE_CORS_ALLOW_CREDENTIALS | cors.allow_credentials | Allow cookies in cross-site requests | `True` |
| INVENTREE_USE_X_FORWARDED_HOST | use_x_forwarded_host | Use forwarded host header | `False` |
| INVENTREE_USE_X_FORWARDED_PORT | use_x_forwarded_port | Use forwarded port header | `False` |
| INVENTREE_USE_X_FORWARDED_PROTO | use_x_forwarded_proto | Use forwarded protocol header | `False` |
| INVENTREE_SESSION_COOKIE_SECURE | cookie.secure | Enforce secure session cookies | `False` |
| INVENTREE_COOKIE_SAMESITE | cookie.samesite | Session cookie mode. Must be one of `Strict | Lax | None | False`. Refer to the [mozilla developer docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie) and the [django documentation]({% include "django.html" %}/ref/settings/#std-setting-SESSION_COOKIE_SAMESITE) for more information. | False |

### Debug Mode

Note that in [debug mode](./index.md#debug-mode), some of the above settings are automatically adjusted to allow for easier development. The following settings are internally overridden in debug mode with the values specified below:

| Setting | Value in Debug Mode | Description |
| --- | --- | --- |
| `INVENTREE_ALLOWED_HOSTS` | `*` | Allow all host in debug mode |
| `CSRF_TRUSTED_ORIGINS` | Value is appended to allow `http://*.localhost:*` | Allow all connections from localhost, for development purposes |
| `INVENTREE_COOKIE_SAMESITE` | `False` | Disable all same-site cookie checks in debug mode |
| `INVENTREE_SESSION_COOKIE_SECURE` | `False` | Disable secure session cookies in debug mode (allow non-https cookies) |

### Cookie Settings

Note that if you set the `INVENTREE_COOKIE_SAMESITE` to `None`, then `INVENTREE_SESSION_COOKIE_SECURE` is automatically set to `True` to ensure that the session cookie is secure! This means that the session cookie will only be sent over secure (https) connections.

### Proxy Considerations

If you are running InvenTree behind a proxy, or forwarded HTTPS connections, you will need to ensure that the InvenTree server is configured to listen on the correct host and port. You will likely have to adjust the `INVENTREE_ALLOWED_HOSTS` setting to ensure that the server will accept requests from the proxy.

Additionally, you may need to configure the following header to ensure that the InvenTree server is watching for information forwarded by the proxy:

**X-Forwarded-Host**

By default, InvenTree *will not* look at the [X-Forwarded-Host](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Forwarded-Host) header.
If you are running InvenTree behind a proxy which obscures the upstream host information, you will need to ensure that the `INVENTREE_USE_X_FORWARDED_HOST` setting is enabled. This will ensure that the InvenTree server uses the forwarded host header for processing requests.

You can also refer to the [Django documentation]({% include "django.html" %}/ref/settings/#secure-proxy-ssl-header) for more information on this header.

**X-Forwarded-Port**

InvenTree provides support for the `X-Forwarded-Port` header, which can be used to determine if the incoming request is using a forwarded port. If you are running InvenTree behind a proxy which forwards port information, you should ensure that the `INVENTREE_USE_X_FORWARDED_PORT` setting is enabled.

Note: This header is overridden by the `X-Forwarded-Host` header.

You can also refer to the [Django documentation]({% include "django.html" %}/ref/settings/#use-x-forwarded-port) for more information on this header.

**X-Forwarded-Proto**

InvenTree provides support for the [X-Forwarded-Proto](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Forwarded-Proto) header, which can be used to determine if the incoming request is using HTTPS, even if the server is running behind a proxy which forwards SSL connections. If you are running InvenTree behind a proxy which forwards SSL connections, you should ensure that the `INVENTREE_USE_X_FORWARDED_PROTO` setting is enabled.

You can also refer to the [Django documentation]({% include "django.html" %}/ref/settings/#use-x-forwarded-host) for more information on this header.

Proxy configuration can be complex, and any configuration beyond the basic setup is outside the scope of this documentation. You should refer to the documentation for the specific proxy server you are using.

Refer to the [proxy server documentation](./processes.md#proxy-server) for more information.


## Admin Site

Django provides a powerful [administrator interface]({% include "django.html" %}/ref/contrib/admin/) which can be used to manage the InvenTree database. This interface is enabled by default, and available at the `/admin/` URL.

The following admin site configuration options are available:

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_ADMIN_ENABLED | admin_enabled | Enable the django administrator interface | True |
| INVENTREE_ADMIN_URL | admin_url | URL for accessing the admin interface | admin |

!!! warning "Security"
    Changing the admin URL is a simple way to improve security, but it is not a substitute for proper security practices.

## Administrator Account

An administrator account can be specified using the following environment variables:

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_ADMIN_USER | admin_user | Admin account username | *Not specified* |
| INVENTREE_ADMIN_PASSWORD | admin_password | Admin account password | *Not specified* |
| INVENTREE_ADMIN_PASSWORD_FILE | admin_password_file | Admin account password file | *Not specified* |
| INVENTREE_ADMIN_EMAIL | admin_email |Admin account email address | *Not specified* |

You can either specify the password directly using `INVENTREE_ADMIN_PASSWORD`, or you can specify a file containing the password using `INVENTREE_ADMIN_PASSWORD_FILE` (this is useful for nix users).

!!! info "Administrator Account"
    Providing `INVENTREE_ADMIN` credentials will result in the provided account being created with *superuser* permissions when InvenTree is started.

## Secret Key Material

InvenTree requires secret keys for providing cryptographic signing and oidc private keys- this should be a secret (and unpredictable) value.

!!! info "Auto-Generated material"
    If none of the following options are specified, InvenTree will automatically generate a secret key file (stored in `secret_key.txt`) and a oidc key file (stored in `oidc.pem`) on first run.

The secret key material can be provided in multiple ways, with the following (descending) priorities:

**Pass Secret Key Material via Environment Variable**

A secret key string can be passed directly using the environment variable `INVENTREE_SECRET_KEY`
A oidc private key can be passed directly using the environment variable `INVENTREE_OIDC_PRIVATE_KEY`

**Pass Secret Key Material File via Environment Variable**

A file containing the secret key can be passed via the environment variable `INVENTREE_SECRET_KEY_FILE`
A PEM-encoded file containing the oidc private key can be passed via the environment variable `INVENTREE_OIDC_PRIVATE_KEY_FILE`

**Fallback to Default Secret Key Material**

If not specified via environment variables, the fallback files (automatically generated as part of InvenTree installation) will be used.

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_SECRET_KEY | secret_key | Raw secret key value | *Not specified* |
| INVENTREE_SECRET_KEY_FILE | secret_key_file | File containing secret key value | *Not specified* |
| INVENTREE_OIDC_PRIVATE_KEY | oidc_private_key | Raw private key value | *Not specified* |
| INVENTREE_OIDC_PRIVATE_KEY_FILE | oidc_private_key_file | File containing private key value in PEM format | *Not specified* |

## Database Options

InvenTree provides support for multiple database backends - any backend supported natively by Django can be used.

Database options are specified under the *database* heading in the configuration file. Any option available in the Django documentation can be used here - it is passed through transparently to the management scripts.

The following database options can be configured:

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_DB_ENGINE | database.ENGINE | Database backend | *Not specified* |
| INVENTREE_DB_NAME | database.NAME | Database name | *Not specified* |
| INVENTREE_DB_USER | database.USER | Database username (if required) | *Not specified* |
| INVENTREE_DB_PASSWORD | database.PASSWORD | Database password (if required) | *Not specified* |
| INVENTREE_DB_HOST | database.HOST | Database host address (if required) | *Not specified* |
| INVENTREE_DB_PORT | database.PORT | Database host port (if required) | *Not specified* |

### PostgreSQL Settings

If running with a PostgreSQL database backend, the following additional options are available:

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_DB_TIMEOUT | database.timeout | Database connection timeout (s) | 2 |
| INVENTREE_DB_TCP_KEEPALIVES | database.tcp_keepalives | TCP keepalive | 1 |
| INVENTREE_DB_TCP_KEEPALIVES_IDLE | database.tcp_keepalives_idle | Idle TCP keepalive | 1 |
| INVENTREE_DB_TCP_KEEPALIVES_INTERNAL | database.tcp_keepalives_internal | Internal TCP keepalive | 1|
| INVENTREE_DB_TCP_KEEPALIVES_COUNT | database.tcp_keepalives_count | TCP keepalive count | 5 |
| INVENTREE_DB_ISOLATION_SERIALIZABLE | database.serializable | Database isolation level configured to "serializable" | False |

### MySQL Settings

If running with a MySQL database backend, the following additional options are available:

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_DB_ISOLATION_SERIALIZABLE | database.serializable | Database isolation level configured to "serializable" | False |

## Caching

InvenTree can be configured to use [redis](https://redis.io) as a global cache backend.
Enabling a global cache can provide significant performance improvements for InvenTree.

### Cache Server

Enabling global caching requires connection to a redis server (which is separate from the InvenTree database and web server). Setup and configuration of this server is outside the scope of this documentation. It is assumed that if you are configuring a cache server, you have already set one up, and are comfortable configuring it.

!!! tip "Docker Support"
    If you are running [InvenTree under docker](./docker.md), we provide a redis container as part of our docker compose file - so redis caching works out of the box.

### Cache Settings

The following cache settings are available:

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_CACHE_ENABLED | cache.enabled | Enable redis caching | False |
| INVENTREE_CACHE_HOST | cache.host | Cache server host | *Not specified* |
| INVENTREE_CACHE_PORT | cache.port | Cache server port | 6379 |
| INVENTREE_CACHE_CONNECT_TIMEOUT | cache.connect_timeout | Cache connection timeout (seconds) | 3 |
| INVENTREE_CACHE_TIMEOUT | cache.timeout | Cache timeout (seconds) | 3 |
| INVENTREE_CACHE_TCP_KEEPALIVE | cache.tcp_keepalive | Cache TCP keepalive | True |
| INVENTREE_CACHE_KEEPALIVE_COUNT | cache.keepalive_count | Cache keepalive count | 5 |
| INVENTREE_CACHE_KEEPALIVE_IDLE | cache.keepalive_idle | Cache keepalive idle | 1 |
| INVENTREE_CACHE_KEEPALIVE_INTERVAL | cache.keepalive_interval | Cache keepalive interval | 1 |
| INVENTREE_CACHE_USER_TIMEOUT | cache.user_timeout | Cache user timeout | 1000 |

## Email Settings

To enable [email functionality](../settings/email.md), email settings must be configured here, either via environment variables or within the configuration file.

The following email settings are available:

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_EMAIL_BACKEND | email.backend | Email backend module | django.core.mail.backends.smtp.EmailBackend |
| INVENTREE_EMAIL_HOST | email.host | Email server host | *Not specified* |
| INVENTREE_EMAIL_PORT | email.port | Email server port | 25 |
| INVENTREE_EMAIL_USERNAME | email.username | Email account username | *Not specified* |
| INVENTREE_EMAIL_PASSWORD | email.password | Email account password | *Not specified* |
| INVENTREE_EMAIL_TLS | email.tls | Enable TLS support | False |
| INVENTREE_EMAIL_SSL | email.ssl | Enable SSL support | False |
| INVENTREE_EMAIL_SENDER | email.sender | Sending email address | *Not specified* |
| INVENTREE_EMAIL_PREFIX | email.prefix | Prefix for subject text | [InvenTree] |

### Sender Email

The "sender" email address is the address from which InvenTree emails are sent (by default) and must be specified for outgoing emails to function:

!!! info "Fallback"
    If `INVENTREE_EMAIL_SENDER` is not provided, the system will fall back to `INVENTREE_EMAIL_USERNAME` (if the username is a valid email address)

## File Storage Locations

InvenTree requires some external directories for storing files:

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_STATIC_ROOT | static_root | [Static files](./processes.md#static-files) directory | *Not specified* |
| INVENTREE_MEDIA_ROOT | media_root | [Media files](./processes.md#media-files) directory | *Not specified* |
| INVENTREE_BACKUP_DIR | backup_dir | Backup files directory | *Not specified* |

!!! tip "Serving Files"
    Read the [proxy server documentation](./processes.md#proxy-server) for more information on hosting *static* and *media* files

### Static File Storage

Static files **require** a local directory for storage. This directory should be specified with the `static_root` option in the config file based on the particular installation requirements.

Alternatively this location can be specified with the `INVENTREE_STATIC_ROOT` environment variable.

!!! warning "Required"
    The static file directory must be specified, or the server will not start

### Uploaded File Storage

Uploaded media files **require** a local directory for storage. This directory should be specified with the `media_root` option in the config file based on the particular installation requirements.

Alternatively this location can be specified with the `INVENTREE_MEDIA_ROOT` environment variable.

!!! warning "Required"
    The media file directory must be specified, or the server will not start

### Backup File Storage

Database and media backups **require** a local directory for storage. This directory should be specified with the `backup_dir` option in the config file based on the particular installation requirements.

Alternatively this location can be specified with the `INVENTREE_BACKUP_DIR` environment variable.

## Authentication

InvenTree provides allowance for additional sign-in options. The following options are not enabled by default, and care must be taken by the system administrator when configuring these settings.

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_MFA_ENABLED | mfa_enabled | Enable or disable multi-factor authentication support for the InvenTree server | True |
| INVENTREE_MFA_SUPPORTED_TYPES | mfa_supported_types | List of supported multi-factor authentication types | recovery_codes,totp |

### Single Sign On

Single Sign On (SSO) allows users to sign in to InvenTree using a third-party authentication provider. This functionality is provided by the [django-allauth](https://docs.allauth.org/en/latest/) package.

There are multiple configuration parameters which must be specified (either in your configuration file, or via environment variables) to enable SSO functionality. Refer to the [SSO documentation](../settings/SSO.md) for a guide on SSO configuration.

!!! tip "More Info"
    Refer to the [SSO documentation](../settings/SSO.md) for more information.

### Login Options

The login-experience can be altered with the following settings:

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_LOGIN_CONFIRM_DAYS | login_confirm_days | Duration for which confirmation links are valid | 3 |
| INVENTREE_LOGIN_ATTEMPTS | login_attempts | Count of allowed login attempts before blocking user | 5 |
| INVENTREE_LOGIN_DEFAULT_HTTP_PROTOCOL | login_default_protocol | Default protocol to use for login callbacks (e.g. using [SSO](#single-sign-on)) | Uses the protocol specified in `INVENTREE_SITE_URL`, or defaults to *http* |

!!! tip "Default Protocol"
    If you have specified `INVENTREE_SITE_URL`, the default protocol will be used from that setting. Otherwise, the default protocol will be *http*.

### Authentication Backends

Custom authentication backends can be used by specifying them here. These can for example be used to add [LDAP / AD login](https://django-auth-ldap.readthedocs.io/en/latest/) to InvenTree

### Sentry Integration

The InvenTree server can be integrated with the [sentry.io](https://sentry.io) monitoring service, for error logging and performance tracking.

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_SENTRY_ENABLED | sentry_enabled | Enable sentry.io integration | False |
| INVENTREE_SENTRY_DSN | sentry_dsn | Sentry DSN (data source name) key | *Defaults to InvenTree developer key* |
| INVENTREE_SENTRY_SAMPLE_RATE | sentry_sample_rate | How often to send data samples | 0.1 |

!!! info "Default DSN"
    If enabled with the default DSN, server errors will be logged to a sentry.io account monitored by the InvenTree developers.

### Customization Options

The logo and custom messages can be changed/set:

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_CUSTOM_LOGO | customize.logo | Path to custom logo in the static files directory | *Not specified* |
| INVENTREE_CUSTOM_SPLASH | customize.splash | Path to custom splash screen in the static files directory | *Not specified* |
| INVENTREE_CUSTOMIZE | customize.login_message | Custom message for login page | *Not specified* |
| INVENTREE_CUSTOMIZE | customize.navbar_message | Custom message for navbar | *Not specified* |

The INVENTREE_CUSTOMIZE environment variable must contain a json object with the keys from the table above and
the wanted values. Example:

```
INVENTREE_CUSTOMIZE={"login_message":"Hallo Michi"}
```

This example sets a login message. Take care of the double quotes.

If you want to remove the InvenTree branding as far as possible from your end-user also check the [global server settings](../settings/global.md#server-settings).

!!! info "Custom Splash Screen Path"
    The provided *custom splash screen* path must be specified *relative* to the location of the `/static/` directory.

!!! info "Custom Logo Path"
    The provided *custom logo* path must be specified *relative* to the location of the `/static/` directory.

## Plugin Options

The following [plugin](../plugins/index.md) configuration options are available:

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_PLUGINS_ENABLED | plugins_enabled | Enable plugin support | False |
| INVENTREE_PLUGIN_NOINSTALL | plugin_noinstall | Disable Plugin installation via API - only use plugins.txt file | False |
| INVENTREE_PLUGIN_FILE | plugins_plugin_file | Location of plugin installation file | *Not specified* |
| INVENTREE_PLUGIN_DIR | plugins_plugin_dir | Location of external plugin directory | *Not specified* |
