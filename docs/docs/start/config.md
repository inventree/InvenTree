---
title: InvenTree Configuration
---

## InvenTree Configuration

While many InvenTree options can be configured at "run time" (see [System Settings](../settings/admin.md#system-settings)), there are a number of system configuration parameters which need to be set *before* running InvenTree. Admin users will need to adjust the InvenTree installation to meet the particular needs of their setup. For example, pointing to the correct database backend, or specifying a list of allowed hosts.

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

!!! info "Environment Variable Priority"
    Note that a provided environment variable will override the value provided in the configuration file.

#### List Values

To specify a list value in an environment variable, use a comma-separated list. For example, to specify a list of trusted origins:

```bash
INVENTREE_TRUSTED_ORIGINS='https://inventree.example.com:8443,https://stock.example.com:8443'
```

## Basic Options

The following basic options are available:

{{ configtable() }}
{{ configsetting("INVENTREE_SITE_URL") }} Specify a fixed site URL |
{{ configsetting("INVENTREE_TIMEZONE") }} Server timezone |
{{ configsetting("INVENTREE_ADMIN_ENABLED") }} Enable the [django administrator interface]({% include "django.html" %}/ref/contrib/admin/) |
{{ configsetting("INVENTREE_ADMIN_URL") }}  URL for accessing [admin interface](../settings/admin.md) |
{{ configsetting("INVENTREE_LANGUAGE") }} Default language |
{{ configsetting("INVENTREE_AUTO_UPDATE") }} Database migrations will be run automatically |

### Site URL

The *INVENTREE_SITE_URL* option defines the base URL for the InvenTree server. This is a critical setting, and it is required for correct operation of the server. If not specified, the server will attempt to determine the site URL automatically - but this may not always be correct!

The site URL is the URL that users will use to access the InvenTree server. For example, if the server is accessible at `https://inventree.example.com`, the site URL should be set to `https://inventree.example.com`. Note that this is not necessarily the same as the internal URL that the server is running on - the internal URL will depend entirely on your server configuration and may be obscured by a reverse proxy or other such setup.

### Timezone

By default, the InvenTree server is configured to use the UTC timezone. This can be adjusted to your desired local timezone. You can refer to [Wikipedia](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) for a list of available timezones. Use the values specified in the *TZ Identifier* column in the linked page. For example, to change to the United States Pacific timezone, set `INVENTREE_TIMEZONE='America/Los_Angeles'`.

Date and time values are stored in the database in UTC format, and are converted to the selected timezone for display in the user interface or API.

### Auto Update

By default, the InvenTree server will not automatically apply database migrations. When the InvenTree installation is updated (*or a plugin is installed which requires database migrations*), database migrations must be applied manually by the system administrator.

With "auto update" enabled, the InvenTree server will automatically apply database migrations as required when plugins are changed. To enable automatic database updates, set `INVENTREE_AUTO_UPDATE` to `True`. However, this setting is not sufficient when updating your InvenTree installation - you must still ensure that you follow the required steps for updating InvenTree as per your installation method.

## Debugging and Logging Options

The following debugging / logging options are available:

{{ configtable() }}
{{ configsetting("INVENTREE_DEBUG") }} Enable [debug mode](./index.md#debug-mode) |
{{ configsetting("INVENTREE_DB_LOGGING") }} Enable logging of database messages |
{{ configsetting("INVENTREE_LOG_LEVEL") }} Set level of logging to terminal |
{{ configsetting("INVENTREE_JSON_LOG") }} Log messages as json |
{{ configsetting("INVENTREE_WRITE_LOG") }} Enable writing of log messages to file at config base |
{{ configsetting("INVENTREE_CONSOLE_LOG") }} Enable logging to console |
{{ configsetting("INVENTREE_SCHEMA_LEVEL") }} Set level of added schema extensions detail (0-3) 0 = including no additional detail |
{{ configsetting("INVENTREE_DEBUG_QUERYCOUNT") }} Enable support for [django-querycount](../develop/index.md#django-querycount) middleware. |
{{ configsetting("INVENTREE_DEBUG_SILK") }} Enable support for [django-silk](../develop/index.md#django-silk) profiling tool. |
| `INVENTREE_DEBUG_SILK_PROFILING` | `debug_silk_profiling` | False | Enable detailed profiling in django-silk |

### Debug Mode

Enabling the `INVENTREE_DEBUG` setting will turn on [Django debug mode]({% include "django.html" %}/ref/settings/#debug). This mode is intended for development purposes, and should not be enabled in a production environment. Read more about [InvenTree debug mode](./index.md#debug-mode).

In debug mode, there are additional [profiling tools](../develop/index.md#profiling-tools) available to help developers analyze and optimize performance.

## Server Access

Depending on how your InvenTree installation is configured, you will need to pay careful attention to the following settings. If you are running your server behind a proxy, or want to adjust support for [CORS requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS), one or more of the following settings may need to be adjusted.

!!! warning "Advanced Users"
    The following settings require a certain assumed level of knowledge. You should also refer to the [django documentation]({% include "django.html" %}/ref/settings/) for more information.

!!! danger "Not Secure"
    Allowing access from any host is not secure, and should be adjusted for your installation.

!!! success "INVENTREE_SITE_URL"
    If you have specified the `INVENTREE_SITE_URL`, this will automatically be used as a trusted CSRF and CORS host (see below).

{{ configtable() }}
{{ configsetting("INVENTREE_ALLOWED_HOSTS") }} List of allowed hosts |
{{ configsetting("INVENTREE_TRUSTED_ORIGINS", default="Uses the *INVENTREE_SITE_URL* parameter, if set. Otherwise, an empty list.") }} List of trusted origins. Refer to the [django documentation]({% include "django.html" %}/ref/settings/#csrf-trusted-origins) |
{{ configsetting("INVENTREE_CORS_ORIGIN_ALLOW_ALL") }} Allow all remote URLS for CORS checks |
{{ configsetting("INVENTREE_CORS_ORIGIN_WHITELIST", default="Uses the *INVENTREE_SITE_URL* parameter, if set. Otherwise, an empty list.") }} List of whitelisted CORS URLs. Refer to the [django-cors-headers documentation](https://github.com/adamchainz/django-cors-headers#cors_allowed_origins-sequencestr) |
{{ configsetting("INVENTREE_CORS_ORIGIN_REGEX") }} List of regular expressions for CORS whitelisted URL patterns |
{{ configsetting("INVENTREE_CORS_ALLOW_CREDENTIALS") }} Allow cookies in cross-site requests |
{{ configsetting("INVENTREE_SITE_LAX_PROTOCOL") }} Ignore protocol mismatches on INVE-E7 site checks |
{{ configsetting("INVENTREE_USE_X_FORWARDED_HOST") }} Use forwarded host header |
{{ configsetting("INVENTREE_USE_X_FORWARDED_PORT") }} Use forwarded port header |
{{ configsetting("INVENTREE_USE_X_FORWARDED_PROTO") }} Use forwarded protocol header |
| `INVENTREE_X_FORWARDED_PROTO_NAME` | `x_forwarded_proto_name` | `HTTP_X_FORWARDED_PROTO` | Name of the header to use for forwarded protocol information |
{{ configsetting("INVENTREE_SESSION_COOKIE_SECURE") }} Enforce secure session cookies |
{{ configsetting("INVENTREE_COOKIE_SAMESITE") }} Session cookie mode. Must be one of `Strict | Lax | None | False`. Refer to the [mozilla developer docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie) and the [django documentation]({% include "django.html" %}/ref/settings/#std-setting-SESSION_COOKIE_SAMESITE) for more information. |


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

{{ configtable() }}
{{ configsetting("INVENTREE_ADMIN_ENABLED") }} Enable the django administrator interface |
{{ configsetting("INVENTREE_ADMIN_URL") }} URL for accessing the admin interface |

!!! warning "Security"
    Changing the admin URL is a simple way to improve security, but it is not a substitute for proper security practices.

## Administrator Account

An administrator account can be specified using the following environment variables:

{{ configtable() }}
{{ configsetting("INVENTREE_ADMIN_USER") }} Admin account username |
{{ configsetting("INVENTREE_ADMIN_PASSWORD") }} Admin account password |
{{ configsetting("INVENTREE_ADMIN_PASSWORD_FILE") }} Admin account password file |
{{ configsetting("INVENTREE_ADMIN_EMAIL") }} Admin account email address |

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

{{ configtable() }}
{{ configsetting("INVENTREE_SECRET_KEY") }} Raw secret key value |
{{ configsetting("INVENTREE_SECRET_KEY_FILE") }} File containing secret key value |
{{ configsetting("INVENTREE_OIDC_PRIVATE_KEY") }} Raw private key value |
{{ configsetting("INVENTREE_OIDC_PRIVATE_KEY_FILE", default="oidc.pem") }} File containing private key value in PEM format |

## Database Options

InvenTree provides support for multiple database backends - any backend supported natively by Django can be used.

Database options are specified under the *database* heading in the configuration file. Any option available in the Django documentation can be used here - it is passed through transparently to the management scripts.

The following database options can be configured:

{{ configtable() }}
{{ configsetting("INVENTREE_DB_ENGINE") }} Database backend |
{{ configsetting("INVENTREE_DB_NAME") }} Database name |
{{ configsetting("INVENTREE_DB_USER") }} Database username (if required) |
{{ configsetting("INVENTREE_DB_PASSWORD") }} Database password (if required) |
{{ configsetting("INVENTREE_DB_HOST") }} Database host address (if required) |
{{ configsetting("INVENTREE_DB_PORT") }} Database host port (if required) |
{{ configsetting("INVENTREE_DB_OPTIONS") }} Additional database options (as a JSON object) |

!!! tip "Database Password"
    The value specified for `INVENTREE_DB_PASSWORD` should not contain comma `,` or colon `:` characters, otherwise the connection to the database may fail.

### PostgreSQL Settings

If running with a PostgreSQL database backend, the following additional options are available:

{{ configtable() }}
{{ configsetting("INVENTREE_DB_TIMEOUT", default="2") }} Database connection timeout (s) |
| `INVENTREE_DB_TCP_KEEPALIVES` | database.tcp_keepalives | 1 | TCP keepalive |
| `INVENTREE_DB_TCP_KEEPALIVES_IDLE` | database.tcp_keepalives_idle | 1 | Idle TCP keepalive |
| `INVENTREE_DB_TCP_KEEPALIVES_INTERVAL` | database.tcp_keepalives_interval | 1| TCP keepalive interval |
| `INVENTREE_DB_TCP_KEEPALIVES_COUNT` | database.tcp_keepalives_count | 5 | TCP keepalive count |
| `INVENTREE_DB_ISOLATION_SERIALIZABLE` | database.serializable | False | Database isolation level configured to "serializable" |

### MySQL Settings

If running with a MySQL database backend, the following additional options are available:

{{ configtable() }}
| `INVENTREE_DB_ISOLATION_SERIALIZABLE` | database.serializable | False | Database isolation level configured to "serializable" |

### SQLite Settings

!!! warning "SQLite Performance"
    SQLite is not recommended for production use, and should only be used for testing or development purposes. If you are using SQLite in production, you may want to adjust the following settings to improve performance.

If running with a SQLite database backend, the following additional options are available:

{{ configtable() }}
{{ configsetting("INVENTREE_DB_TIMEOUT", default="10") }} Database connection timeout (s) |
| `INVENTREE_DB_WAL_MODE` | database.wal_mode | True | Enable Write-Ahead Logging (WAL) mode for SQLite databases |

## Caching

InvenTree can be configured to use [redis](https://redis.io) as a global cache backend.
Enabling a global cache can provide significant performance improvements for InvenTree.

### Cache Server

Enabling global caching requires connection to a redis server (which is separate from the InvenTree database and web server). Setup and configuration of this server is outside the scope of this documentation. It is assumed that if you are configuring a cache server, you have already set one up, and are comfortable configuring it.

!!! tip "Docker Support"
    If you are running [InvenTree under docker](./docker.md), we provide a redis container as part of our docker compose file - so redis caching works out of the box.

### Cache Settings

The following cache settings are available:

{{ configtable() }}
{{ configsetting("INVENTREE_CACHE_ENABLED") }} Enable redis caching |
{{ configsetting("INVENTREE_CACHE_HOST") }} Cache server host |
{{ configsetting("INVENTREE_CACHE_PORT") }} Cache server port |
{{ configsetting("INVENTREE_CACHE_PASSWORD") }} Cache server password |
{{ configsetting("INVENTREE_CACHE_USER") }} Cache server username |
{{ configsetting("INVENTREE_CACHE_DB") }} Cache server database index |
{{ configsetting("INVENTREE_CACHE_CONNECT_TIMEOUT") }} Cache connection timeout (seconds) |
{{ configsetting("INVENTREE_CACHE_TIMEOUT") }} Cache timeout (seconds) |
{{ configsetting("INVENTREE_CACHE_TCP_KEEPALIVE") }} Cache TCP keepalive |
{{ configsetting("INVENTREE_CACHE_KEEPALIVE_COUNT") }} Cache keepalive count |
{{ configsetting("INVENTREE_CACHE_KEEPALIVE_IDLE") }} Cache keepalive idle |
{{ configsetting("INVENTREE_CACHE_KEEPALIVE_INTERVAL") }} Cache keepalive interval |
{{ configsetting("INVENTREE_CACHE_USER_TIMEOUT") }} Cache user timeout |


!!! tip "Cache Password"
    The value specified for `INVENTREE_CACHE_PASSWORD` should not contain comma `,` or colon `:` characters, otherwise the connection to the cache server may fail.

## Email Settings

To enable [email functionality](../settings/email.md), email settings must be configured here, either via environment variables or within the configuration file.

The following email settings are available:

{{ configtable() }}
{{ configsetting("INVENTREE_EMAIL_BACKEND") }} Email backend module |
{{ configsetting("INVENTREE_EMAIL_HOST") }} Email server host |
{{ configsetting("INVENTREE_EMAIL_PORT") }} Email server port |
{{ configsetting("INVENTREE_EMAIL_USERNAME") }} Email account username |
{{ configsetting("INVENTREE_EMAIL_PASSWORD") }} Email account password |
{{ configsetting("INVENTREE_EMAIL_TLS") }} Enable STARTTLS support (commonly port 567) |
{{ configsetting("INVENTREE_EMAIL_SSL") }} Enable legacy SSL/TLS support (commonly port 465) |
{{ configsetting("INVENTREE_EMAIL_SENDER") }} Sending email address |
{{ configsetting("INVENTREE_EMAIL_PREFIX") }} Prefix for subject text |

### Email Backend

The default email implementation uses the Django STMP backend. This should be sufficient for most implementations, although other backends can be used if required. Note that selection of a different backend requires must use fully qualified module path, and requires advanced knowledge.

### Sender Email

The "sender" email address is the address from which InvenTree emails are sent (by default) and must be specified for outgoing emails to function:

!!! info "Fallback"
    If `INVENTREE_EMAIL_SENDER` is not provided, the system will fall back to `INVENTREE_EMAIL_USERNAME` (if the username is a valid email address)

## File Storage Locations

InvenTree requires some external directories for storing files:

{{ configtable() }}
{{ configsetting("INVENTREE_STATIC_ROOT") }} [Static files](./processes.md#static-files) directory |
{{ configsetting("INVENTREE_MEDIA_ROOT") }} [Media files](./processes.md#media-files) directory |
{{ configsetting("INVENTREE_BACKUP_DIR") }} Directory for backup files |

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


### Storage backends

It is also possible to use alternative storage backends for static and media files, at the moment there is direct provide direct support bundled for S3 and SFTP. Google cloud storage and Azure blob storage would also be supported by the [used library](https://django-storages.readthedocs.io), but require additional packages to be installed.

{{ configtable() }}
{{ configsetting("INVENTREE_STORAGE_TARGET") }} Storage target to use for static and media files, valid options: local, s3, sftp |


#### S3

{{ configtable() }}
| `INVENTREE_S3_ACCESS_KEY` | storage.s3.access_key | *Not specified* | Access key |
| `INVENTREE_S3_SECRET_KEY` | storage.s3.secret_key | *Not specified* | Secret key |
| `INVENTREE_S3_BUCKET_NAME` | storage.s3.bucket_name | *Not specified* | Bucket name, required by most providers |
| `INVENTREE_S3_REGION_NAME` | storage.s3.region_name | *Not specified* | S3 region name |
| `INVENTREE_S3_ENDPOINT_URL` | storage.s3.endpoint_url | *Not specified* | Custom S3 endpoint URL, defaults to AWS endpoints if not set |
| `INVENTREE_S3_LOCATION` | storage.s3.location | inventree-server | Sub-Location that should be used |
| `INVENTREE_S3_DEFAULT_ACL` | storage.s3.default_acl | *Not specified* | Default ACL for uploaded files, defaults to provider default if not set |
| `INVENTREE_S3_VERIFY_SSL` | storage.s3.verify_ssl | True | Verify SSL certificate for S3 endpoint |
| `INVENTREE_S3_OVERWRITE` | storage.s3.overwrite | False | Overwrite existing files in S3 bucket |
| `INVENTREE_S3_VIRTUAL` | storage.s3.virtual | False | Use virtual addressing style - by default False -> `path` style, `virtual` style if True |

#### SFTP

{{ configtable() }}
| `INVENTREE_SFTP_HOST` | storage.sftp.host | *Not specified* | SFTP host |
| `INVENTREE_SFTP_PARAMS` | storage.sftp.params | *Not specified* | SFTP connection parameters, see https://docs.paramiko.org/en/latest/api/client.html#paramiko.client.SSHClient.connect; e.g. `{'port': 22, 'user': 'usr', 'password': 'pwd'}` |
| `INVENTREE_SFTP_UID` | storage.sftp.uid | *Not specified* | SFTP user ID - not required |
| `INVENTREE_SFTP_GID` | storage.sftp.gid | *Not specified* | SFTP group ID - not required |
| `INVENTREE_SFTP_LOCATION` | storage.sftp.location | inventree-server | Sub-Location that should be used |

## Authentication

InvenTree provides allowance for additional sign-in options. The following options are not enabled by default, and care must be taken by the system administrator when configuring these settings.

{{ configtable() }}
{{ configsetting("INVENTREE_MFA_ENABLED") }} Enable multi-factor authentication support for the InvenTree server |
{{ configsetting("INVENTREE_MFA_SUPPORTED_TYPES") }} List of supported multi-factor authentication types |
{{ configsetting("INVENTREE_USE_JWT") }} Enable support for JSON Web Tokens (JWT) for authentication |

### Single Sign On

Single Sign On (SSO) allows users to sign in to InvenTree using a third-party authentication provider. This functionality is provided by the [django-allauth](https://docs.allauth.org/en/latest/) package.

There are multiple configuration parameters which must be specified (either in your configuration file, or via environment variables) to enable SSO functionality. Refer to the [SSO documentation](../settings/SSO.md) for a guide on SSO configuration.

!!! tip "More Info"
    Refer to the [SSO documentation](../settings/SSO.md) for more information.

### Login Options

The login-experience can be altered with the following settings:

{{ configtable() }}
{{ configsetting("INVENTREE_LOGIN_CONFIRM_DAYS") }} Duration for which confirmation links are valid |
{{ configsetting("INVENTREE_LOGIN_ATTEMPTS") }} Count of allowed login attempts before blocking user |
{{ configsetting("INVENTREE_LOGIN_DEFAULT_HTTP_PROTOCOL", default="Uses the protocol specified in `INVENTREE_SITE_URL`, or defaults to *http*") }} Default protocol to use for login callbacks (e.g. using [SSO](#single-sign-on)) |

!!! tip "Default Protocol"
    If you have specified `INVENTREE_SITE_URL`, the default protocol will be used from that setting. Otherwise, the default protocol will be *http*.

### Authentication Backends

Custom authentication backends can be used by specifying them here. These can for example be used to add [LDAP / AD login](https://django-auth-ldap.readthedocs.io/en/latest/) to InvenTree

## Background Worker Options

The following options are available for configuring the InvenTree [background worker process](./processes.md#background-worker):

{{ configtable() }}
{{ configsetting("INVENTREE_BACKGROUND_WORKERS") }} Number of background worker processes |
{{ configsetting("INVENTREE_BACKGROUND_TIMEOUT") }} Timeout for background worker tasks (seconds) |
{{ configsetting("INVENTREE_BACKGROUND_RETRY") }} Time to wait before retrying a background task (seconds) |
{{ configsetting("INVENTREE_BACKGROUND_MAX_ATTEMPTS") }} Maximum number of attempts for a background task |

## Sentry Integration

The InvenTree server can be integrated with the [sentry.io](https://sentry.io) monitoring service, for error logging and performance tracking.

{{ configtable() }}
{{ configsetting("INVENTREE_SENTRY_ENABLED") }} Enable sentry.io integration |
{{ configsetting("INVENTREE_SENTRY_DSN", default="Defaults to InvenTree developer key") }} Sentry DSN (data source name) key |
{{ configsetting("INVENTREE_SENTRY_SAMPLE_RATE") }} How often to send data samples (seconds) |

!!! info "Default DSN"
    If enabled with the default DSN, server errors will be logged to a sentry.io account monitored by the InvenTree developers.

## Customization Options

The logo and custom messages can be changed/set:

{{ configtable() }}
{{ configsetting("INVENTREE_CUSTOM_LOGO") }} Path to custom logo in the static files directory |
{{ configsetting("INVENTREE_CUSTOM_SPLASH") }} Path to custom splash screen in the static files directory |
{{ configsetting("INVENTREE_SITE_HEADER") }} Custom header text for the django admin page |
{{ configsetting("INVENTREE_CUSTOMIZE") }} JSON object containing custom messages for the login page, navbar, and Django admin site |

The INVENTREE_CUSTOMIZE environment variable must contain a json object with the keys from the table above and
the wanted values. Example:

```
INVENTREE_CUSTOMIZE={"login_message":"Hello World"}
```

This example sets a login message. Take care of the double quotes.

If you want to remove the InvenTree branding as far as possible from your end-user also check the [global server settings](../settings/global.md#server-settings).

!!! info "Custom Splash Screen Path"
    The provided *custom splash screen* path must be specified *relative* to the location of the `/static/` directory.

!!! info "Custom Logo Path"
    The provided *custom logo* path must be specified *relative* to the location of the `/static/` directory.

## Frontend Options

Set the `INVENTREE_FRONTEND_SETTINGS` Environment variable to a JSON object or use `frontend_settings` in the configuration file with the following options:

| Option | Description | Default |
| --- | --- | --- |
| `base_url` | Set the base URL for the user interface. This is the UI path e.g. '/web/' | `web` |
| `api_host` | If provided, specify the API host | *None* |
| `server_list` | Set the server list. `{}` | `[]` |
| `debug` | Set the debug mode | *Server debug mode* |
| `environment` | `development` or `production` | *development if Server is in debug mode* |
| `show_server_selector` | In debug mode, show server selector by default. If no servers are specified, show server selector. | |
| `url_compatibility` | Support compatibility with "legacy" URLs? | `true` |
| `sentry_dsn` | Set a Sentry DSN url | *Not specified* |
| `mobile_mode` | Controls if InvenTree web UI can be used by mobile devices. There are 3 options: `default` - does not allow mobile devices; `allow-ignore` - shows a mobile device detected banner with a button to ignore this warning AT THE USERS OWN RISK; `allow-always` - skips the mobile check and allows mobile devices always (of course at the server admins OWN RISK) | `default` |

E.g. to allow mobile devices to ignore the mobile check, use the following Environment variable:

```env
INVENTREE_FRONTEND_SETTINGS='{"mobile_mode": "allow-ignore"}'
```

## Plugin Options

The following [plugin](../plugins/index.md) configuration options are available:

{{ configtable() }}
{{ configsetting("INVENTREE_PLUGINS_ENABLED") }} Enable plugin support |
{{ configsetting("INVENTREE_PLUGIN_NOINSTALL") }} Disable Plugin installation via API |
{{ configsetting("INVENTREE_PLUGIN_FILE") }} Location of plugin installation file |
| `INVENTREE_PLUGIN_DIR` | `plugin_dir` | *Not specified* | Location of external plugin directory |
{{ configsetting("INVENTREE_PLUGIN_RETRY") }} Number of tries to attempt loading a plugin before giving up |
{{ configsetting("INVENTREE_PLUGINS_MANDATORY") }} List of [plugins which are considered mandatory](../plugins/index.md#mandatory-third-party-plugins) |
{{ configsetting("INVENTREE_PLUGIN_DEV_SLUG") }} Specify plugin to run in [development mode](../plugins/creator.md#backend-configuration) |
{{ configsetting("INVENTREE_PLUGIN_DEV_HOST") }} Specify host for development mode plugin |

## Override Global Settings

If required, [global settings values](../settings/global.md#override-global-settings) can be overridden by the system administrator.

To override global settings, provide a "dictionary" of settings overrides in the configuration file, or via an environment variable.

{{ configtable() }}
{{ configsetting("INVENTREE_GLOBAL_SETTINGS") }} JSON object containing global settings overrides |

## Other Settings

Other available settings, not categorized above, are detailed in the table below:

{{ configtable() }}
{{ configsetting("INVENTREE_EXTRA_URL_SCHEMES") }} Allow additional URL schemes for URL validation |
