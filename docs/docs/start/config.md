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

The configuration file *template* can be found on [GitHub](https://github.com/inventree/InvenTree/blob/master/src/backend/InvenTree/config_template.yaml)

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

## Basic Options

The following basic options are available:

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_DEBUG | debug | Enable [debug mode](./intro.md#debug-mode) | True |
| INVENTREE_LOG_LEVEL | log_level | Set level of logging to terminal | WARNING |
| INVENTREE_DB_LOGGING | db_logging | Enable logging of database messages | False |
| INVENTREE_TIMEZONE | timezone | Server timezone | UTC |
| INVENTREE_SITE_URL | site_url | Specify a fixed site URL | *Not specified* |
| INVENTREE_ADMIN_ENABLED | admin_enabled | Enable the [django administrator interface]({% include "django.html" %}/ref/contrib/admin/) | True |
| INVENTREE_ADMIN_URL | admin_url | URL for accessing [admin interface](../settings/admin.md) | admin |
| INVENTREE_LANGUAGE | language | Default language | en-us |
| INVENTREE_BASE_URL | base_url | Server base URL | *Not specified* |
| INVENTREE_AUTO_UPDATE | auto_update | Database migrations will be run automatically | False |

## Server Access

Depending on how your InvenTree installation is configured, you will need to pay careful attention to the following settings. If you are running your server behind a proxy, or want to adjust support for CORS requests, one or more of the following settings may need to be adjusted.

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
| INVENTREE_CORS_ORIGIN_ALLOW_ALL | cors.allow_all | Allow all remote URLS for CORS checks | False |
| INVENTREE_CORS_ORIGIN_WHITELIST | cors.whitelist | List of whitelisted CORS URLs. Refer to the [django-cors-headers documentation](https://github.com/adamchainz/django-cors-headers#cors_allowed_origins-sequencestr) | Uses the *INVENTREE_SITE_URL* parameter, if set. Otherwise, an empty list. |
| INVENTREE_USE_X_FORWARDED_HOST | use_x_forwarded_host | Use forwarded host header | False |
| INVENTREE_USE_X_FORWARDED_PORT | use_x_forwarded_port | Use forwarded port header | False |
| INVENTREE_CORS_ALLOW_CREDENTIALS | cors.allow_credentials | Allow cookies in cross-site requests | True |

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

## Secret Key

InvenTree requires a secret key for providing cryptographic signing - this should be a secret (and unpredictable) value.

The secret key can be provided in multiple ways, with the following (descending) priorities:

**Pass Secret Key via Environment Variable**

A secret key string can be passed directly using the environment variable `INVENTREE_SECRET_KEY`

**Pass Secret Key File via Environment Variable**

A file containing the secret key can be passed via the environment variable `INVENTREE_SECRET_KEY_FILE`

**Fallback to Default Secret Key File**

If not specified via environment variables, the fallback secret_key file (automatically generated as part of InvenTree installation) will be used.

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_SECRET_KEY | secret_key | Raw secret key value | *Not specified* |
| INVENTREE_SECRET_KEY_FILE | secret_key_file | File containing secret key value | *Not specified* |

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

## Supported Currencies

The currencies supported by InvenTree must be specified in the [configuration file](#configuration-file).

A list of currency codes (e.g. *AUD*, *CAD*, *JPY*, *USD*) can be specified using the `currencies` variable (or using the `INVENTREE_CURRENCIES` environment variable).

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_CURRENCIES | currencies | List of supported currencies| `AUD`, `CAD`, `CNY`, `EUR`, `GBP`, `JPY`, `NZD`, `USD` |

!!! tip "More Info"
    Read the [currencies documentation](../settings/currency.md) for more information on currency support in InvenTree

## File Storage Locations

InvenTree requires some external directories for storing files:

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_STATIC_ROOT | static_root | [Static files](./serving_files.md#static-files) directory | *Not specified* |
| INVENTREE_MEDIA_ROOT | media_root | [Media files](./serving_files.md#media-files) directory | *Not specified* |
| INVENTREE_BACKUP_DIR | backup_dir | Backup files directory | *Not specified* |

!!! tip "Serving Files"
    Read the [Serving Files](./serving_files.md) section for more information on hosting *static* and *media* files

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
| INVENTREE_LOGIN_DEFAULT_HTTP_PROTOCOL | login_default_protocol | Default protocol to use for login callbacks (e.g. using [SSO](#single-sign-on)) | http |

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

If you want to remove the InvenTree branding as far as possible from your end-user also check the [global server settings](../settings/global.md#server-settings).

!!! info "Custom Splash Screen Path"
    The provided *custom splash screen* path must be specified *relative* to the location of the `/static/` directory.

!!! info "Custom Logo Path"
    The provided *custom logo* path must be specified *relative* to the location of the `/static/` directory.

## Plugin Options

The following [plugin](../extend/plugins.md) configuration options are available:

| Environment Variable | Configuration File | Description | Default |
| --- | --- | --- | --- |
| INVENTREE_PLUGINS_ENABLED | plugins_enabled | Enable plugin support | False |
| INVENTREE_PLUGIN_NOINSTALL | plugin_noinstall | Disable Plugin installation via API - only use plugins.txt file | False |
| INVENTREE_PLUGIN_FILE | plugins_plugin_file | Location of plugin installation file | *Not specified* |
| INVENTREE_PLUGIN_DIR | plugins_plugin_dir | Location of external plugin directory | *Not specified* |
