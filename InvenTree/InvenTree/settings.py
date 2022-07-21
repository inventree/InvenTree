"""Django settings for InvenTree project.

In practice the settings in this file should not be adjusted,
instead settings can be configured in the config.yaml file
located in the top level project directory.

This allows implementation configuration to be hidden from source control,
as well as separate configuration parameters from the more complex
database setup in this file.
"""

import logging
import os
import random
import socket
import string
import sys

import django.conf.locale
from django.core.files.storage import default_storage
from django.utils.translation import gettext_lazy as _

import moneyed
import sentry_sdk
import yaml
from sentry_sdk.integrations.django import DjangoIntegration

from .config import get_base_dir, get_config_file, get_plugin_file, get_setting


def _is_true(x):
    # Shortcut function to determine if a value "looks" like a boolean
    return str(x).strip().lower() in ['1', 'y', 'yes', 't', 'true']


# Default Sentry DSN (can be overriden if user wants custom sentry integration)
INVENTREE_DSN = 'https://3928ccdba1d34895abde28031fd00100@o378676.ingest.sentry.io/6494600'

# Determine if we are running in "test" mode e.g. "manage.py test"
TESTING = 'test' in sys.argv
# Are enviroment variables manipulated by tests? Needs to be set by testing code
TESTING_ENV = False

# New requirement for django 3.2+
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = get_base_dir()

cfg_filename = get_config_file()

with open(cfg_filename, 'r') as cfg:
    CONFIG = yaml.safe_load(cfg)

# We will place any config files in the same directory as the config file
config_dir = os.path.dirname(cfg_filename)

# Default action is to run the system in Debug mode
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = _is_true(get_setting(
    'INVENTREE_DEBUG',
    CONFIG.get('debug', True)
))

DOCKER = _is_true(get_setting(
    'INVENTREE_DOCKER',
    False
))

# Configure logging settings
log_level = get_setting(
    'INVENTREE_LOG_LEVEL',
    CONFIG.get('log_level', 'WARNING')
)

logging.basicConfig(
    level=log_level,
    format="%(asctime)s %(levelname)s %(message)s",
)

if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
    log_level = 'WARNING'  # pragma: no cover

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': log_level,
    },
    'filters': {
        'require_not_maintenance_mode_503': {
            '()': 'maintenance_mode.logging.RequireNotMaintenanceMode503',
        },
    },
}

# Get a logger instance for this setup file
logger = logging.getLogger("inventree")

"""
Specify a secret key to be used by django.

Following options are tested, in descending order of preference:

A) Check for environment variable INVENTREE_SECRET_KEY => Use raw key data
B) Check for environment variable INVENTREE_SECRET_KEY_FILE => Load key data from file
C) Look for default key file "secret_key.txt"
d) Create "secret_key.txt" if it does not exist
"""

if secret_key := os.getenv("INVENTREE_SECRET_KEY"):
    # Secret key passed in directly
    SECRET_KEY = secret_key.strip()  # pragma: no cover
    logger.info("SECRET_KEY loaded by INVENTREE_SECRET_KEY")  # pragma: no cover
else:
    # Secret key passed in by file location
    key_file = os.getenv("INVENTREE_SECRET_KEY_FILE")

    if key_file:
        key_file = os.path.abspath(key_file)  # pragma: no cover
    else:
        # default secret key location
        key_file = os.path.join(BASE_DIR, "secret_key.txt")
        key_file = os.path.abspath(key_file)

    if not os.path.exists(key_file):  # pragma: no cover
        logger.info(f"Generating random key file at '{key_file}'")
        # Create a random key file
        with open(key_file, 'w') as f:
            options = string.digits + string.ascii_letters + string.punctuation
            key = ''.join([random.choice(options) for i in range(100)])
            f.write(key)

    logger.info(f"Loading SECRET_KEY from '{key_file}'")

    try:
        SECRET_KEY = open(key_file, "r").read().strip()
    except Exception:  # pragma: no cover
        logger.exception(f"Couldn't load keyfile {key_file}")
        sys.exit(-1)

# The filesystem location for served static files
STATIC_ROOT = os.path.abspath(
    get_setting(
        'INVENTREE_STATIC_ROOT',
        CONFIG.get('static_root', None)
    )
)

if STATIC_ROOT is None:  # pragma: no cover
    print("ERROR: INVENTREE_STATIC_ROOT directory not defined")
    sys.exit(1)

# The filesystem location for served static files
MEDIA_ROOT = os.path.abspath(
    get_setting(
        'INVENTREE_MEDIA_ROOT',
        CONFIG.get('media_root', None)
    )
)

if MEDIA_ROOT is None:  # pragma: no cover
    print("ERROR: INVENTREE_MEDIA_ROOT directory is not defined")
    sys.exit(1)

# List of allowed hosts (default = allow all)
ALLOWED_HOSTS = CONFIG.get('allowed_hosts', ['*'])

# Cross Origin Resource Sharing (CORS) options

# Only allow CORS access to API
CORS_URLS_REGEX = r'^/api/.*$'

# Extract CORS options from configuration file
cors_opt = CONFIG.get('cors', None)

if cors_opt:
    CORS_ORIGIN_ALLOW_ALL = cors_opt.get('allow_all', False)

    if not CORS_ORIGIN_ALLOW_ALL:
        CORS_ORIGIN_WHITELIST = cors_opt.get('whitelist', [])  # pragma: no cover

# Web URL endpoint for served static files
STATIC_URL = '/static/'

STATICFILES_DIRS = []

# Translated Template settings
STATICFILES_I18_PREFIX = 'i18n'
STATICFILES_I18_SRC = os.path.join(BASE_DIR, 'templates', 'js', 'translated')
STATICFILES_I18_TRG = os.path.join(BASE_DIR, 'InvenTree', 'static_i18n')
STATICFILES_DIRS.append(STATICFILES_I18_TRG)
STATICFILES_I18_TRG = os.path.join(STATICFILES_I18_TRG, STATICFILES_I18_PREFIX)

STATFILES_I18_PROCESSORS = [
    'InvenTree.context.status_codes',
]

# Color Themes Directory
STATIC_COLOR_THEMES_DIR = os.path.join(STATIC_ROOT, 'css', 'color-themes')

# Web URL endpoint for served media files
MEDIA_URL = '/media/'

if DEBUG:
    logger.info("InvenTree running with DEBUG enabled")

logger.debug(f"MEDIA_ROOT: '{MEDIA_ROOT}'")
logger.debug(f"STATIC_ROOT: '{STATIC_ROOT}'")

# Application definition

INSTALLED_APPS = [

    # InvenTree apps
    'build.apps.BuildConfig',
    'common.apps.CommonConfig',
    'company.apps.CompanyConfig',
    'label.apps.LabelConfig',
    'order.apps.OrderConfig',
    'part.apps.PartConfig',
    'report.apps.ReportConfig',
    'stock.apps.StockConfig',
    'users.apps.UsersConfig',
    'plugin.apps.PluginAppConfig',
    'InvenTree.apps.InvenTreeConfig',       # InvenTree app runs last

    # Core django modules
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'user_sessions',                # db user sessions
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Maintenance
    'maintenance_mode',

    # Third part add-ons
    'django_filters',                       # Extended filter functionality
    'rest_framework',                       # DRF (Django Rest Framework)
    'rest_framework.authtoken',             # Token authentication for API
    'corsheaders',                          # Cross-origin Resource Sharing for DRF
    'crispy_forms',                         # Improved form rendering
    'import_export',                        # Import / export tables to file
    'django_cleanup.apps.CleanupConfig',    # Automatically delete orphaned MEDIA files
    'mptt',                                 # Modified Preorder Tree Traversal
    'markdownify',                          # Markdown template rendering
    'djmoney',                              # django-money integration
    'djmoney.contrib.exchange',             # django-money exchange rates
    'error_report',                         # Error reporting in the admin interface
    'django_q',
    'formtools',                            # Form wizard tools

    'allauth',                              # Base app for SSO
    'allauth.account',                      # Extend user with accounts
    'allauth.socialaccount',                # Use 'social' providers

    'django_otp',                           # OTP is needed for MFA - base package
    'django_otp.plugins.otp_totp',          # Time based OTP
    'django_otp.plugins.otp_static',        # Backup codes

    'allauth_2fa',                          # MFA flow for allauth
]

MIDDLEWARE = CONFIG.get('middleware', [
    'django.middleware.security.SecurityMiddleware',
    'x_forwarded_for.middleware.XForwardedForMiddleware',
    'user_sessions.middleware.SessionMiddleware',                   # db user sessions
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'InvenTree.middleware.InvenTreeRemoteUserMiddleware',       # Remote / proxy auth
    'django_otp.middleware.OTPMiddleware',                      # MFA support
    'InvenTree.middleware.CustomAllauthTwoFactorMiddleware',    # Flow control for allauth
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'InvenTree.middleware.AuthRequiredMiddleware',
    'InvenTree.middleware.Check2FAMiddleware',                  # Check if the user should be forced to use MFA
    'maintenance_mode.middleware.MaintenanceModeMiddleware',
])

# Error reporting middleware
MIDDLEWARE.append('error_report.middleware.ExceptionProcessor')

AUTHENTICATION_BACKENDS = CONFIG.get('authentication_backends', [
    'django.contrib.auth.backends.RemoteUserBackend',           # proxy login
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',      # SSO login via external providers
])

DEBUG_TOOLBAR_ENABLED = DEBUG and CONFIG.get('debug_toolbar', False)

# If the debug toolbar is enabled, add the modules
if DEBUG_TOOLBAR_ENABLED:  # pragma: no cover
    logger.info("Running with DEBUG_TOOLBAR enabled")
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

    DEBUG_TOOLBAR_CONFIG = {
        'RESULTS_CACHE_SIZE': 100,
        'OBSERVE_REQUEST_CALLBACK': lambda x: False,
    }

# Internal IP addresses allowed to see the debug toolbar
INTERNAL_IPS = [
    '127.0.0.1',
]

if DOCKER:
    # Internal IP addresses are different when running under docker
    hostname, ___, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1", "10.0.2.2"]

# Allow secure http developer server in debug mode
if DEBUG:
    INSTALLED_APPS.append('sslserver')

# InvenTree URL configuration

# Base URL for admin pages (default="admin")
INVENTREE_ADMIN_URL = get_setting(
    'INVENTREE_ADMIN_URL',
    CONFIG.get('admin_url', 'admin'),
)

ROOT_URLCONF = 'InvenTree.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            # Allow templates in the reporting directory to be accessed
            os.path.join(MEDIA_ROOT, 'report'),
            os.path.join(MEDIA_ROOT, 'label'),
        ],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Custom InvenTree context processors
                'InvenTree.context.health_status',
                'InvenTree.context.status_codes',
                'InvenTree.context.user_roles',
            ],
            'loaders': [(
                'django.template.loaders.cached.Loader', [
                    'plugin.template.PluginTemplateLoader',
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ])
            ],
        },
    },
]

if DEBUG_TOOLBAR_ENABLED:
    # Note that the APP_DIRS value must be set when using debug_toolbar
    # But this will kill template loading for plugins
    TEMPLATES[0]['APP_DIRS'] = True
    del TEMPLATES[0]['OPTIONS']['loaders']

REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'InvenTree.exceptions.exception_handler',
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.DjangoModelPermissions',
        'InvenTree.permissions.RolePermission',
    ),
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_METADATA_CLASS': 'InvenTree.metadata.InvenTreeMetadata',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ]
}

if DEBUG:
    # Enable browsable API if in DEBUG mode
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'].append('rest_framework.renderers.BrowsableAPIRenderer')

WSGI_APPLICATION = 'InvenTree.wsgi.application'

"""
Configure the database backend based on the user-specified values.

- Primarily this configuration happens in the config.yaml file
- However there may be reason to configure the DB via environmental variables
- The following code lets the user "mix and match" database configuration
"""

logger.debug("Configuring database backend:")

# Extract database configuration from the config.yaml file
db_config = CONFIG.get('database', {})

if not db_config:
    db_config = {}

# Environment variables take preference over config file!

db_keys = ['ENGINE', 'NAME', 'USER', 'PASSWORD', 'HOST', 'PORT']

for key in db_keys:
    # First, check the environment variables
    env_key = f"INVENTREE_DB_{key}"
    env_var = os.environ.get(env_key, None)

    if env_var:
        # Override configuration value
        db_config[key] = env_var

# Check that required database configuration options are specified
reqiured_keys = ['ENGINE', 'NAME']

for key in reqiured_keys:
    if key not in db_config:  # pragma: no cover
        error_msg = f'Missing required database configuration value {key}'
        logger.error(error_msg)

        print('Error: ' + error_msg)
        sys.exit(-1)

"""
Special considerations for the database 'ENGINE' setting.
It can be specified in config.yaml (or envvar) as either (for example):
- sqlite3
- django.db.backends.sqlite3
- django.db.backends.postgresql
"""

db_engine = db_config['ENGINE'].lower()

# Correct common misspelling
if db_engine == 'sqlite':
    db_engine = 'sqlite3'  # pragma: no cover

if db_engine in ['sqlite3', 'postgresql', 'mysql']:
    # Prepend the required python module string
    db_engine = f'django.db.backends.{db_engine}'
    db_config['ENGINE'] = db_engine

db_name = db_config['NAME']
db_host = db_config.get('HOST', "''")

logger.info(f"DB_ENGINE: {db_engine}")
logger.info(f"DB_NAME: {db_name}")
logger.info(f"DB_HOST: {db_host}")

"""
In addition to base-level database configuration, we may wish to specify specific options to the database backend
Ref: https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-OPTIONS
"""

# 'OPTIONS' or 'options' can be specified in config.yaml
# Set useful sensible timeouts for a transactional webserver to communicate
# with its database server, that is, if the webserver is having issues
# connecting to the database server (such as a replica failover) don't sit and
# wait for possibly an hour or more, just tell the client something went wrong
# and let the client retry when they want to.
db_options = db_config.get("OPTIONS", db_config.get("options", {}))

# Specific options for postgres backend
if "postgres" in db_engine:  # pragma: no cover
    from psycopg2.extensions import (ISOLATION_LEVEL_READ_COMMITTED,
                                     ISOLATION_LEVEL_SERIALIZABLE)

    # Connection timeout
    if "connect_timeout" not in db_options:
        # The DB server is in the same data center, it should not take very
        # long to connect to the database server
        # # seconds, 2 is minium allowed by libpq
        db_options["connect_timeout"] = int(
            os.getenv("INVENTREE_DB_TIMEOUT", 2)
        )

    # Setup TCP keepalive
    # DB server is in the same DC, it should not become unresponsive for
    # very long. With the defaults below we wait 5 seconds for the network
    # issue to resolve itself.  It it that doesn't happen whatever happened
    # is probably fatal and no amount of waiting is going to fix it.
    # # 0 - TCP Keepalives disabled; 1 - enabled
    if "keepalives" not in db_options:
        db_options["keepalives"] = int(
            os.getenv("INVENTREE_DB_TCP_KEEPALIVES", "1")
        )
    # # Seconds after connection is idle to send keep alive
    if "keepalives_idle" not in db_options:
        db_options["keepalives_idle"] = int(
            os.getenv("INVENTREE_DB_TCP_KEEPALIVES_IDLE", "1")
        )
    # # Seconds after missing ACK to send another keep alive
    if "keepalives_interval" not in db_options:
        db_options["keepalives_interval"] = int(
            os.getenv("INVENTREE_DB_TCP_KEEPALIVES_INTERVAL", "1")
        )
    # # Number of missing ACKs before we close the connection
    if "keepalives_count" not in db_options:
        db_options["keepalives_count"] = int(
            os.getenv("INVENTREE_DB_TCP_KEEPALIVES_COUNT", "5")
        )
    # # Milliseconds for how long pending data should remain unacked
    # by the remote server
    # TODO: Supported starting in PSQL 11
    # "tcp_user_timeout": int(os.getenv("PGTCP_USER_TIMEOUT", "1000"),

    # Postgres's default isolation level is Read Committed which is
    # normally fine, but most developers think the database server is
    # actually going to do Serializable type checks on the queries to
    # protect against simultaneous changes.
    # https://www.postgresql.org/docs/devel/transaction-iso.html
    # https://docs.djangoproject.com/en/3.2/ref/databases/#isolation-level
    if "isolation_level" not in db_options:
        serializable = _is_true(
            os.getenv("INVENTREE_DB_ISOLATION_SERIALIZABLE", "false")
        )
        db_options["isolation_level"] = (
            ISOLATION_LEVEL_SERIALIZABLE
            if serializable
            else ISOLATION_LEVEL_READ_COMMITTED
        )

# Specific options for MySql / MariaDB backend
if "mysql" in db_engine:  # pragma: no cover
    # TODO TCP time outs and keepalives

    # MariaDB's default isolation level is Repeatable Read which is
    # normally fine, but most developers think the database server is
    # actually going to Serializable type checks on the queries to
    # protect against siumltaneous changes.
    # https://mariadb.com/kb/en/mariadb-transactions-and-isolation-levels-for-sql-server-users/#changing-the-isolation-level
    # https://docs.djangoproject.com/en/3.2/ref/databases/#mysql-isolation-level
    if "isolation_level" not in db_options:
        serializable = _is_true(
            os.getenv("INVENTREE_DB_ISOLATION_SERIALIZABLE", "false")
        )
        db_options["isolation_level"] = (
            "serializable" if serializable else "read committed"
        )

# Specific options for sqlite backend
if "sqlite" in db_engine:
    # TODO: Verify timeouts are not an issue because no network is involved for SQLite

    # SQLite's default isolation level is Serializable due to SQLite's
    # single writer implementation.  Presumably as a result of this, it is
    # not possible to implement any lower isolation levels in SQLite.
    # https://www.sqlite.org/isolation.html
    pass

# Provide OPTIONS dict back to the database configuration dict
db_config['OPTIONS'] = db_options

# Set testing options for the database
db_config['TEST'] = {
    'CHARSET': 'utf8',
}

# Set collation option for mysql test database
if 'mysql' in db_engine:
    db_config['TEST']['COLLATION'] = 'utf8_general_ci'  # pragma: no cover

DATABASES = {
    'default': db_config
}

_cache_config = CONFIG.get("cache", {})
_cache_host = _cache_config.get("host", os.getenv("INVENTREE_CACHE_HOST"))
_cache_port = _cache_config.get(
    "port", os.getenv("INVENTREE_CACHE_PORT", "6379")
)

if _cache_host:  # pragma: no cover
    # We are going to rely upon a possibly non-localhost for our cache,
    # so don't wait too long for the cache as nothing in the cache should be
    # irreplacable.
    _cache_options = {
        "CLIENT_CLASS": "django_redis.client.DefaultClient",
        "SOCKET_CONNECT_TIMEOUT": int(os.getenv("CACHE_CONNECT_TIMEOUT", "2")),
        "SOCKET_TIMEOUT": int(os.getenv("CACHE_SOCKET_TIMEOUT", "2")),
        "CONNECTION_POOL_KWARGS": {
            "socket_keepalive": _is_true(
                os.getenv("CACHE_TCP_KEEPALIVE", "1")
            ),
            "socket_keepalive_options": {
                socket.TCP_KEEPCNT: int(
                    os.getenv("CACHE_KEEPALIVES_COUNT", "5")
                ),
                socket.TCP_KEEPIDLE: int(
                    os.getenv("CACHE_KEEPALIVES_IDLE", "1")
                ),
                socket.TCP_KEEPINTVL: int(
                    os.getenv("CACHE_KEEPALIVES_INTERVAL", "1")
                ),
                socket.TCP_USER_TIMEOUT: int(
                    os.getenv("CACHE_TCP_USER_TIMEOUT", "1000")
                ),
            },
        },
    }
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"redis://{_cache_host}:{_cache_port}/0",
            "OPTIONS": _cache_options,
        },
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        },
    }

try:
    # 4 background workers seems like a sensible default
    background_workers = int(os.environ.get('INVENTREE_BACKGROUND_WORKERS', 4))
except ValueError:  # pragma: no cover
    background_workers = 4

# django-q configuration
Q_CLUSTER = {
    'name': 'InvenTree',
    'workers': background_workers,
    'timeout': 90,
    'retry': 120,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default',
    'sync': False,
}

if _cache_host:  # pragma: no cover
    # If using external redis cache, make the cache the broker for Django Q
    # as well
    Q_CLUSTER["django_redis"] = "worker"

# database user sessions
SESSION_ENGINE = 'user_sessions.backends.db'
LOGOUT_REDIRECT_URL = 'index'
SILENCED_SYSTEM_CHECKS = [
    'admin.E410',
]

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Extra (optional) URL validators
# See https://docs.djangoproject.com/en/2.2/ref/validators/#django.core.validators.URLValidator

EXTRA_URL_SCHEMES = CONFIG.get('extra_url_schemes', [])

if type(EXTRA_URL_SCHEMES) not in [list]:  # pragma: no cover
    logger.warning("extra_url_schemes not correctly formatted")
    EXTRA_URL_SCHEMES = []

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = CONFIG.get('language', 'en-us')

# If a new language translation is supported, it must be added here
LANGUAGES = [
    ('cs', _('Czech')),
    ('de', _('German')),
    ('el', _('Greek')),
    ('en', _('English')),
    ('es', _('Spanish')),
    ('es-mx', _('Spanish (Mexican)')),
    ('fa', _('Farsi / Persian')),
    ('fr', _('French')),
    ('he', _('Hebrew')),
    ('hu', _('Hungarian')),
    ('it', _('Italian')),
    ('ja', _('Japanese')),
    ('ko', _('Korean')),
    ('nl', _('Dutch')),
    ('no', _('Norwegian')),
    ('pl', _('Polish')),
    ('pt', _('Portuguese')),
    ('pt-BR', _('Portuguese (Brazilian)')),
    ('ru', _('Russian')),
    ('sv', _('Swedish')),
    ('th', _('Thai')),
    ('tr', _('Turkish')),
    ('vi', _('Vietnamese')),
    ('zh-cn', _('Chinese')),
]

# Testing interface translations
if get_setting('TEST_TRANSLATIONS', False):  # pragma: no cover
    # Set default language
    LANGUAGE_CODE = 'xx'

    # Add to language catalog
    LANGUAGES.append(('xx', 'Test'))

    # Add custom languages not provided by Django
    EXTRA_LANG_INFO = {
        'xx': {
            'code': 'xx',
            'name': 'Test',
            'name_local': 'Test'
        },
    }
    LANG_INFO = dict(django.conf.locale.LANG_INFO, **EXTRA_LANG_INFO)
    django.conf.locale.LANG_INFO = LANG_INFO

# Currencies available for use
CURRENCIES = CONFIG.get(
    'currencies',
    [
        'AUD', 'CAD', 'CNY', 'EUR', 'GBP', 'JPY', 'NZD', 'USD',
    ],
)

# Check that each provided currency is supported
for currency in CURRENCIES:
    if currency not in moneyed.CURRENCIES:  # pragma: no cover
        print(f"Currency code '{currency}' is not supported")
        sys.exit(1)


# Custom currency exchange backend
EXCHANGE_BACKEND = 'InvenTree.exchange.InvenTreeExchange'

# Extract email settings from the config file
email_config = CONFIG.get('email', {})

EMAIL_BACKEND = get_setting(
    'INVENTREE_EMAIL_BACKEND',
    email_config.get('backend', 'django.core.mail.backends.smtp.EmailBackend')
)

# Email backend settings
EMAIL_HOST = get_setting(
    'INVENTREE_EMAIL_HOST',
    email_config.get('host', '')
)

EMAIL_PORT = get_setting(
    'INVENTREE_EMAIL_PORT',
    email_config.get('port', 25)
)

EMAIL_HOST_USER = get_setting(
    'INVENTREE_EMAIL_USERNAME',
    email_config.get('username', ''),
)

EMAIL_HOST_PASSWORD = get_setting(
    'INVENTREE_EMAIL_PASSWORD',
    email_config.get('password', ''),
)

DEFAULT_FROM_EMAIL = get_setting(
    'INVENTREE_EMAIL_SENDER',
    email_config.get('sender', ''),
)

EMAIL_SUBJECT_PREFIX = '[InvenTree] '

EMAIL_USE_LOCALTIME = False

EMAIL_USE_TLS = get_setting(
    'INVENTREE_EMAIL_TLS',
    email_config.get('tls', False),
)

EMAIL_USE_SSL = get_setting(
    'INVENTREE_EMAIL_SSL',
    email_config.get('ssl', False),
)

EMAIL_TIMEOUT = 60

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale/'),
)

TIME_ZONE = get_setting(
    'INVENTREE_TIMEZONE',
    CONFIG.get('timezone', 'UTC')
)

USE_I18N = True

USE_L10N = True

# Do not use native timezone support in "test" mode
# It generates a *lot* of cruft in the logs
if not TESTING:
    USE_TZ = True  # pragma: no cover

DATE_INPUT_FORMATS = [
    "%Y-%m-%d",
]

# crispy forms use the bootstrap templates
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# Use database transactions when importing / exporting data
IMPORT_EXPORT_USE_TRANSACTIONS = True

SITE_ID = 1

# Load the allauth social backends
SOCIAL_BACKENDS = CONFIG.get('social_backends', [])
for app in SOCIAL_BACKENDS:
    INSTALLED_APPS.append(app)  # pragma: no cover

SOCIALACCOUNT_PROVIDERS = CONFIG.get('social_providers', [])

SOCIALACCOUNT_STORE_TOKENS = True

# settings for allauth
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = get_setting('INVENTREE_LOGIN_CONFIRM_DAYS', CONFIG.get('login_confirm_days', 3))
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = get_setting('INVENTREE_LOGIN_ATTEMPTS', CONFIG.get('login_attempts', 5))
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
ACCOUNT_PREVENT_ENUMERATION = True

# override forms / adapters
ACCOUNT_FORMS = {
    'login': 'allauth.account.forms.LoginForm',
    'signup': 'InvenTree.forms.CustomSignupForm',
    'add_email': 'allauth.account.forms.AddEmailForm',
    'change_password': 'allauth.account.forms.ChangePasswordForm',
    'set_password': 'allauth.account.forms.SetPasswordForm',
    'reset_password': 'allauth.account.forms.ResetPasswordForm',
    'reset_password_from_key': 'allauth.account.forms.ResetPasswordKeyForm',
    'disconnect': 'allauth.socialaccount.forms.DisconnectForm',
}

SOCIALACCOUNT_ADAPTER = 'InvenTree.forms.CustomSocialAccountAdapter'
ACCOUNT_ADAPTER = 'InvenTree.forms.CustomAccountAdapter'

# login settings
REMOTE_LOGIN = get_setting('INVENTREE_REMOTE_LOGIN', CONFIG.get('remote_login', False))
REMOTE_LOGIN_HEADER = get_setting('INVENTREE_REMOTE_LOGIN_HEADER', CONFIG.get('remote_login_header', 'REMOTE_USER'))

# Markdownify configuration
# Ref: https://django-markdownify.readthedocs.io/en/latest/settings.html

MARKDOWNIFY = {
    'default': {
        'BLEACH': True,
        'WHITELIST_ATTRS': [
            'href',
            'src',
            'alt',
        ],
        'WHITELIST_TAGS': [
            'a',
            'abbr',
            'b',
            'blockquote',
            'em',
            'h1', 'h2', 'h3',
            'i',
            'img',
            'li',
            'ol',
            'p',
            'strong',
            'ul'
        ],
    }
}

# Error reporting
SENTRY_ENABLED = get_setting('INVENTREE_SENTRY_ENABLED', CONFIG.get('sentry_enabled', False))
SENTRY_DSN = get_setting('INVENTREE_SENTRY_DSN', CONFIG.get('sentry_dsn', INVENTREE_DSN))

SENTRY_SAMPLE_RATE = float(get_setting('INVENTREE_SENTRY_SAMPLE_RATE', CONFIG.get('sentry_sample_rate', 0.1)))

if SENTRY_ENABLED and SENTRY_DSN:  # pragma: no cover
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), ],
        traces_sample_rate=1.0 if DEBUG else SENTRY_SAMPLE_RATE,
        send_default_pii=True
    )
    inventree_tags = {
        'testing': TESTING,
        'docker': DOCKER,
        'debug': DEBUG,
        'remote': REMOTE_LOGIN,
    }
    for key, val in inventree_tags.items():
        sentry_sdk.set_tag(f'inventree_{key}', val)

# Maintenance mode
MAINTENANCE_MODE_RETRY_AFTER = 60
MAINTENANCE_MODE_STATE_BACKEND = 'maintenance_mode.backends.DefaultStorageBackend'

# Are plugins enabled?
PLUGINS_ENABLED = _is_true(get_setting(
    'INVENTREE_PLUGINS_ENABLED',
    CONFIG.get('plugins_enabled', False),
))

PLUGIN_FILE = get_plugin_file()

# Plugin Directories (local plugins will be loaded from these directories)
PLUGIN_DIRS = ['plugin.builtin', ]

if not TESTING:
    # load local deploy directory in prod
    PLUGIN_DIRS.append('plugins')  # pragma: no cover

if DEBUG or TESTING:
    # load samples in debug mode
    PLUGIN_DIRS.append('plugin.samples')

# Plugin test settings
PLUGIN_TESTING = get_setting('PLUGIN_TESTING', TESTING)  # are plugins beeing tested?
PLUGIN_TESTING_SETUP = get_setting('PLUGIN_TESTING_SETUP', False)  # load plugins from setup hooks in testing?
PLUGIN_TESTING_EVENTS = False                  # Flag if events are tested right now
PLUGIN_RETRY = get_setting('PLUGIN_RETRY', 5)  # how often should plugin loading be tried?
PLUGIN_FILE_CHECKED = False                    # Was the plugin file checked?

# User interface customization values
CUSTOMIZE = get_setting(
    'INVENTREE_CUSTOMIZE',
    CONFIG.get('customize', {}),
    {}
)

CUSTOM_LOGO = get_setting(
    'INVENTREE_CUSTOM_LOGO',
    CUSTOMIZE.get('logo', False)
)

# check that the logo-file exsists in media
if CUSTOM_LOGO and not default_storage.exists(CUSTOM_LOGO):  # pragma: no cover
    logger.warning(f"The custom logo file '{CUSTOM_LOGO}' could not be found in the default media storage")
    CUSTOM_LOGO = False
