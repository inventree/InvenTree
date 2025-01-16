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
import sys
from pathlib import Path

import django.conf.locale
import django.core.exceptions
from django.core.validators import URLValidator
from django.http import Http404

import structlog
from dotenv import load_dotenv
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from InvenTree.cache import get_cache_config, is_global_cache_enabled
from InvenTree.config import get_boolean_setting, get_custom_file, get_setting
from InvenTree.ready import isInMainThread
from InvenTree.sentry import default_sentry_dsn, init_sentry
from InvenTree.version import checkMinPythonVersion, inventreeApiVersion

from . import config, locales

checkMinPythonVersion()

INVENTREE_BASE_URL = 'https://inventree.org'
INVENTREE_NEWS_URL = f'{INVENTREE_BASE_URL}/news/feed.atom'

# Determine if we are running in "test" mode e.g. "manage.py test"
TESTING = 'test' in sys.argv or 'TESTING' in os.environ

if TESTING:
    # Use a weaker password hasher for testing (improves testing speed)
    PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

    # Enable slow-test-runner
    TEST_RUNNER = 'django_slowtests.testrunner.DiscoverSlowestTestsRunner'
    NUM_SLOW_TESTS = 25

    # Note: The following fix is "required" for docker build workflow
    # Note: 2022-12-12 still unsure why...
    if os.getenv('INVENTREE_DOCKER'):
        # Ensure that sys.path includes global python libs
        site_packages = '/usr/local/lib/python3.9/site-packages'

        if site_packages not in sys.path:
            print('Adding missing site-packages path:', site_packages)
            sys.path.append(site_packages)

# Are environment variables manipulated by tests? Needs to be set by testing code
TESTING_ENV = False

# New requirement for django 3.2+
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Build paths inside the project like this: BASE_DIR.joinpath(...)
BASE_DIR = config.get_base_dir()

# Load configuration data
CONFIG = config.load_config_data(set_cache=True)

# Load VERSION data if it exists
version_file = BASE_DIR.parent.joinpath('VERSION')
if version_file.exists():
    print('load version from file')
    load_dotenv(version_file)

# Default action is to run the system in Debug mode
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = get_boolean_setting('INVENTREE_DEBUG', 'debug', False)

# Configure logging settings
LOG_LEVEL = get_setting('INVENTREE_LOG_LEVEL', 'log_level', 'WARNING')
JSON_LOG = get_boolean_setting('INVENTREE_JSON_LOG', 'json_log', False)
WRITE_LOG = get_boolean_setting('INVENTREE_WRITE_LOG', 'write_log', False)

logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(levelname)s %(message)s')

if LOG_LEVEL not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
    LOG_LEVEL = 'WARNING'  # pragma: no cover
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_not_maintenance_mode_503': {
            '()': 'maintenance_mode.logging.RequireNotMaintenanceMode503'
        }
    },
    'formatters': {
        'json_formatter': {
            '()': structlog.stdlib.ProcessorFormatter,
            'processor': structlog.processors.JSONRenderer(),
        },
        'plain_console': {
            '()': structlog.stdlib.ProcessorFormatter,
            'processor': structlog.dev.ConsoleRenderer(),
        },
        'key_value': {
            '()': structlog.stdlib.ProcessorFormatter,
            'processor': structlog.processors.KeyValueRenderer(
                key_order=['timestamp', 'level', 'event', 'logger']
            ),
        },
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'plain_console'}
    },
    'loggers': {
        'django_structlog': {'handlers': ['console'], 'level': LOG_LEVEL},
        'inventree': {'handlers': ['console'], 'level': LOG_LEVEL},
    },
}


# Add handlers
if WRITE_LOG and JSON_LOG:  # pragma: no cover
    LOGGING['handlers']['log_file'] = {
        'class': 'logging.handlers.WatchedFileHandler',
        'filename': str(BASE_DIR.joinpath('logs.json')),
        'formatter': 'json_formatter',
    }
    LOGGING['loggers']['django_structlog']['handlers'] += ['log_file']
elif WRITE_LOG:  # pragma: no cover
    LOGGING['handlers']['log_file'] = {
        'class': 'logging.handlers.WatchedFileHandler',
        'filename': str(BASE_DIR.joinpath('logs.log')),
        'formatter': 'key_value',
    }
    LOGGING['loggers']['django_structlog']['handlers'] += ['log_file']

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
# Optionally add database-level logging
if get_setting('INVENTREE_DB_LOGGING', 'db_logging', False):
    LOGGING['loggers'] = {'django.db.backends': {'level': LOG_LEVEL or 'DEBUG'}}

# Get a logger instance for this setup file
logger = structlog.getLogger('inventree')

# Load SECRET_KEY
SECRET_KEY = config.get_secret_key()

# The filesystem location for served static files
STATIC_ROOT = config.get_static_dir()

# The filesystem location for uploaded meadia files
MEDIA_ROOT = config.get_media_dir()

# Needed for the parts importer, directly impacts the maximum parts that can be uploaded
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

# Web URL endpoint for served static files
STATIC_URL = '/static/'

# Web URL endpoint for served media files
MEDIA_URL = '/media/'

# Are plugins enabled?
PLUGINS_ENABLED = get_boolean_setting(
    'INVENTREE_PLUGINS_ENABLED', 'plugins_enabled', False
)

PLUGINS_INSTALL_DISABLED = get_boolean_setting(
    'INVENTREE_PLUGIN_NOINSTALL', 'plugin_noinstall', False
)

PLUGIN_FILE = config.get_plugin_file()

# Plugin test settings
PLUGIN_TESTING = get_setting(
    'INVENTREE_PLUGIN_TESTING', 'PLUGIN_TESTING', TESTING
)  # Are plugins being tested?

PLUGIN_TESTING_SETUP = get_setting(
    'INVENTREE_PLUGIN_TESTING_SETUP', 'PLUGIN_TESTING_SETUP', False
)  # Load plugins from setup hooks in testing?

PLUGIN_TESTING_EVENTS = False  # Flag if events are tested right now
PLUGIN_TESTING_EVENTS_ASYNC = False  # Flag if events are tested asynchronously

PLUGIN_RETRY = get_setting(
    'INVENTREE_PLUGIN_RETRY', 'PLUGIN_RETRY', 3, typecast=int
)  # How often should plugin loading be tried?

# Hash of the plugin file (will be updated on each change)
PLUGIN_FILE_HASH = ''

STATICFILES_DIRS = []

# Append directory for compiled react files if debug server is running
if DEBUG and 'collectstatic' not in sys.argv:
    web_dir = BASE_DIR.joinpath('..', 'web', 'static').absolute()
    if web_dir.exists():
        STATICFILES_DIRS.append(web_dir)

    # Append directory for sample plugin static content (if in debug mode)
    if PLUGINS_ENABLED:
        logger.info('Adding plugin sample static content')
        STATICFILES_DIRS.append(BASE_DIR.joinpath('plugin', 'samples', 'static'))

# Database backup options
# Ref: https://django-dbbackup.readthedocs.io/en/master/configuration.html
DBBACKUP_SEND_EMAIL = False
DBBACKUP_STORAGE = get_setting(
    'INVENTREE_BACKUP_STORAGE',
    'backup_storage',
    'django.core.files.storage.FileSystemStorage',
)

# Default backup configuration
DBBACKUP_STORAGE_OPTIONS = get_setting(
    'INVENTREE_BACKUP_OPTIONS',
    'backup_options',
    default_value={'location': config.get_backup_dir()},
    typecast=dict,
)

INVENTREE_ADMIN_ENABLED = get_boolean_setting(
    'INVENTREE_ADMIN_ENABLED', config_key='admin_enabled', default_value=True
)

# Base URL for admin pages (default="admin")
INVENTREE_ADMIN_URL = get_setting(
    'INVENTREE_ADMIN_URL', config_key='admin_url', default_value='admin'
)

INSTALLED_APPS = [
    # Admin site integration
    'django.contrib.admin',
    # InvenTree apps
    'build.apps.BuildConfig',
    'common.apps.CommonConfig',
    'company.apps.CompanyConfig',
    'plugin.apps.PluginAppConfig',  # Plugin app runs before all apps that depend on the isPluginRegistryLoaded function
    'order.apps.OrderConfig',
    'part.apps.PartConfig',
    'report.apps.ReportConfig',
    'stock.apps.StockConfig',
    'users.apps.UsersConfig',
    'machine.apps.MachineConfig',
    'importer.apps.ImporterConfig',
    'web',
    'generic',
    'InvenTree.apps.InvenTreeConfig',  # InvenTree app runs last
    # Core django modules
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'user_sessions',  # db user sessions
    'whitenoise.runserver_nostatic',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    # Maintenance
    'maintenance_mode',
    # Third part add-ons
    'django_filters',  # Extended filter functionality
    'rest_framework',  # DRF (Django Rest Framework)
    'corsheaders',  # Cross-origin Resource Sharing for DRF
    'django_cleanup.apps.CleanupConfig',  # Automatically delete orphaned MEDIA files
    'mptt',  # Modified Preorder Tree Traversal
    'markdownify',  # Markdown template rendering
    'djmoney',  # django-money integration
    'djmoney.contrib.exchange',  # django-money exchange rates
    'error_report',  # Error reporting in the admin interface
    'django_q',
    'dbbackup',  # Backups - django-dbbackup
    'taggit',  # Tagging
    'flags',  # Flagging - django-flags
    'django_structlog',  # Structured logging
    'allauth',  # Base app for SSO
    'allauth.account',  # Extend user with accounts
    'allauth.socialaccount',  # Use 'social' providers
    'django_otp',  # OTP is needed for MFA - base package
    'django_otp.plugins.otp_totp',  # Time based OTP
    'django_otp.plugins.otp_static',  # Backup codes
    'allauth_2fa',  # MFA flow for allauth
    'dj_rest_auth',  # Authentication APIs - dj-rest-auth
    'dj_rest_auth.registration',  # Registration APIs - dj-rest-auth'
    'drf_spectacular',  # API documentation
    'django_ical',  # For exporting calendars
]

MIDDLEWARE = CONFIG.get(
    'middleware',
    [
        'django.middleware.security.SecurityMiddleware',
        'x_forwarded_for.middleware.XForwardedForMiddleware',
        'user_sessions.middleware.SessionMiddleware',  # db user sessions
        'django.middleware.locale.LocaleMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'corsheaders.middleware.CorsMiddleware',
        'whitenoise.middleware.WhiteNoiseMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'InvenTree.middleware.InvenTreeRemoteUserMiddleware',  # Remote / proxy auth
        'django_otp.middleware.OTPMiddleware',  # MFA support
        'InvenTree.middleware.CustomAllauthTwoFactorMiddleware',  # Flow control for allauth
        'allauth.account.middleware.AccountMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'InvenTree.middleware.AuthRequiredMiddleware',
        'InvenTree.middleware.Check2FAMiddleware',  # Check if the user should be forced to use MFA
        'maintenance_mode.middleware.MaintenanceModeMiddleware',
        'InvenTree.middleware.InvenTreeExceptionProcessor',  # Error reporting
        'django_structlog.middlewares.RequestMiddleware',  # Structured logging
    ],
)

# In DEBUG mode, add support for django-querycount
# Ref: https://github.com/bradmontgomery/django-querycount
if DEBUG and get_boolean_setting(
    'INVENTREE_DEBUG_QUERYCOUNT', 'debug_querycount', False
):
    MIDDLEWARE.append('querycount.middleware.QueryCountMiddleware')
    logger.debug('Running with debug_querycount middleware enabled')

QUERYCOUNT = {
    'THRESHOLDS': {
        'MEDIUM': 50,
        'HIGH': 200,
        'MIN_TIME_TO_LOG': 0.1,
        'MIN_QUERY_COUNT_TO_LOG': 25,
    },
    'IGNORE_REQUEST_PATTERNS': [r'^(?!\/(api)?(plugin)?\/).*'],
    'IGNORE_SQL_PATTERNS': [],
    'DISPLAY_DUPLICATES': 1,
    'RESPONSE_HEADER': 'X-Django-Query-Count',
}


AUTHENTICATION_BACKENDS = CONFIG.get(
    'authentication_backends',
    [
        'django.contrib.auth.backends.RemoteUserBackend',  # proxy login
        'django.contrib.auth.backends.ModelBackend',
        'allauth.account.auth_backends.AuthenticationBackend',  # SSO login via external providers
        'sesame.backends.ModelBackend',  # Magic link login django-sesame
    ],
)

# LDAP support
LDAP_AUTH = get_boolean_setting('INVENTREE_LDAP_ENABLED', 'ldap.enabled', False)
if LDAP_AUTH:
    import django_auth_ldap.config
    import ldap

    AUTHENTICATION_BACKENDS.append('django_auth_ldap.backend.LDAPBackend')

    # debug mode to troubleshoot configuration
    LDAP_DEBUG = get_boolean_setting('INVENTREE_LDAP_DEBUG', 'ldap.debug', False)
    if LDAP_DEBUG:
        if 'loggers' not in LOGGING:
            LOGGING['loggers'] = {}
        LOGGING['loggers']['django_auth_ldap'] = {
            'level': 'DEBUG',
            'handlers': ['console'],
        }

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
    AUTH_LDAP_GLOBAL_OPTIONS = global_options
    if LDAP_DEBUG:
        print('[LDAP] ldap.global_options =', global_options)

    AUTH_LDAP_SERVER_URI = get_setting('INVENTREE_LDAP_SERVER_URI', 'ldap.server_uri')
    AUTH_LDAP_START_TLS = get_boolean_setting(
        'INVENTREE_LDAP_START_TLS', 'ldap.start_tls', False
    )
    AUTH_LDAP_BIND_DN = get_setting('INVENTREE_LDAP_BIND_DN', 'ldap.bind_dn')
    AUTH_LDAP_BIND_PASSWORD = get_setting(
        'INVENTREE_LDAP_BIND_PASSWORD', 'ldap.bind_password'
    )
    AUTH_LDAP_USER_SEARCH = django_auth_ldap.config.LDAPSearch(
        get_setting('INVENTREE_LDAP_SEARCH_BASE_DN', 'ldap.search_base_dn'),
        ldap.SCOPE_SUBTREE,
        str(
            get_setting(
                'INVENTREE_LDAP_SEARCH_FILTER_STR',
                'ldap.search_filter_str',
                '(uid= %(user)s)',
            )
        ),
    )
    AUTH_LDAP_USER_DN_TEMPLATE = get_setting(
        'INVENTREE_LDAP_USER_DN_TEMPLATE', 'ldap.user_dn_template'
    )
    AUTH_LDAP_USER_ATTR_MAP = get_setting(
        'INVENTREE_LDAP_USER_ATTR_MAP',
        'ldap.user_attr_map',
        {'first_name': 'givenName', 'last_name': 'sn', 'email': 'mail'},
        dict,
    )
    AUTH_LDAP_ALWAYS_UPDATE_USER = get_boolean_setting(
        'INVENTREE_LDAP_ALWAYS_UPDATE_USER', 'ldap.always_update_user', True
    )
    AUTH_LDAP_CACHE_TIMEOUT = get_setting(
        'INVENTREE_LDAP_CACHE_TIMEOUT', 'ldap.cache_timeout', 3600, int
    )

    AUTH_LDAP_MIRROR_GROUPS = get_boolean_setting(
        'INVENTREE_LDAP_MIRROR_GROUPS', 'ldap.mirror_groups', False
    )
    AUTH_LDAP_GROUP_OBJECT_CLASS = get_setting(
        'INVENTREE_LDAP_GROUP_OBJECT_CLASS',
        'ldap.group_object_class',
        'groupOfUniqueNames',
        str,
    )
    AUTH_LDAP_GROUP_SEARCH = django_auth_ldap.config.LDAPSearch(
        get_setting('INVENTREE_LDAP_GROUP_SEARCH', 'ldap.group_search'),
        ldap.SCOPE_SUBTREE,
        f'(objectClass={AUTH_LDAP_GROUP_OBJECT_CLASS})',
    )
    AUTH_LDAP_GROUP_TYPE_CLASS = get_setting(
        'INVENTREE_LDAP_GROUP_TYPE_CLASS',
        'ldap.group_type_class',
        'GroupOfUniqueNamesType',
        str,
    )
    AUTH_LDAP_GROUP_TYPE_CLASS_ARGS = get_setting(
        'INVENTREE_LDAP_GROUP_TYPE_CLASS_ARGS', 'ldap.group_type_class_args', [], list
    )
    AUTH_LDAP_GROUP_TYPE_CLASS_KWARGS = get_setting(
        'INVENTREE_LDAP_GROUP_TYPE_CLASS_KWARGS',
        'ldap.group_type_class_kwargs',
        {'name_attr': 'cn'},
        dict,
    )
    AUTH_LDAP_GROUP_TYPE = getattr(django_auth_ldap.config, AUTH_LDAP_GROUP_TYPE_CLASS)(
        *AUTH_LDAP_GROUP_TYPE_CLASS_ARGS, **AUTH_LDAP_GROUP_TYPE_CLASS_KWARGS
    )
    AUTH_LDAP_REQUIRE_GROUP = get_setting(
        'INVENTREE_LDAP_REQUIRE_GROUP', 'ldap.require_group'
    )
    AUTH_LDAP_DENY_GROUP = get_setting('INVENTREE_LDAP_DENY_GROUP', 'ldap.deny_group')
    AUTH_LDAP_USER_FLAGS_BY_GROUP = get_setting(
        'INVENTREE_LDAP_USER_FLAGS_BY_GROUP',
        'ldap.user_flags_by_group',
        default_value=None,
        typecast=dict,
    )
    AUTH_LDAP_FIND_GROUP_PERMS = True

# Internal flag to determine if we are running in docker mode
DOCKER = get_boolean_setting('INVENTREE_DOCKER', default_value=False)

# Allow secure http developer server in debug mode
if DEBUG:
    INSTALLED_APPS.append('sslserver')

# InvenTree URL configuration
ROOT_URLCONF = 'InvenTree.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR.joinpath('templates'), MEDIA_ROOT.joinpath('report')],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                (
                    'InvenTree.template.InvenTreeTemplateLoader',
                    [
                        'plugin.template.PluginTemplateLoader',
                        'django.template.loaders.filesystem.Loader',
                        'django.template.loaders.app_directories.Loader',
                    ],
                )
            ],
        },
    }
]

REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'InvenTree.exceptions.exception_handler',
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.authentication.ApiTokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.DjangoModelPermissions',
        'InvenTree.permissions.RolePermission',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_METADATA_CLASS': 'InvenTree.metadata.InvenTreeMetadata',
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'TOKEN_MODEL': 'users.models.ApiToken',
}

if DEBUG:
    # Enable browsable API if in DEBUG mode
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'].append(
        'rest_framework.renderers.BrowsableAPIRenderer'
    )

# JWT switch
USE_JWT = get_boolean_setting('INVENTREE_USE_JWT', 'use_jwt', False)
REST_USE_JWT = USE_JWT

# dj-rest-auth
REST_AUTH = {
    'SESSION_LOGIN': True,
    'TOKEN_MODEL': 'users.models.ApiToken',
    'TOKEN_CREATOR': 'users.models.default_create_token',
    'USE_JWT': USE_JWT,
    'REGISTER_SERIALIZER': 'InvenTree.auth_overrides.RegisterSerializer',
}

OLD_PASSWORD_FIELD_ENABLED = True

# JWT settings - rest_framework_simplejwt
if USE_JWT:
    JWT_AUTH_COOKIE = 'inventree-auth'
    JWT_AUTH_REFRESH_COOKIE = 'inventree-token'
    REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'].append(
        'dj_rest_auth.jwt_auth.JWTCookieAuthentication'
    )
    INSTALLED_APPS.append('rest_framework_simplejwt')


# WSGI default setting
WSGI_APPLICATION = 'InvenTree.wsgi.application'

"""
Configure the database backend based on the user-specified values.

- Primarily this configuration happens in the config.yaml file
- However there may be reason to configure the DB via environmental variables
- The following code lets the user "mix and match" database configuration
"""

logger.debug('Configuring database backend:')

# Extract database configuration from the config.yaml file
db_config = CONFIG.get('database', None)

if not db_config:
    db_config = {}

# Environment variables take preference over config file!

db_keys = ['ENGINE', 'NAME', 'USER', 'PASSWORD', 'HOST', 'PORT']

for key in db_keys:
    # First, check the environment variables
    env_key = f'INVENTREE_DB_{key}'
    env_var = os.environ.get(env_key, None)

    if env_var:
        # Make use PORT is int
        if key == 'PORT':
            try:
                env_var = int(env_var)
            except ValueError:
                logger.exception('Invalid number for %s: %s', env_key, env_var)
        # Override configuration value
        db_config[key] = env_var

# Check that required database configuration options are specified
required_keys = ['ENGINE', 'NAME']

# Ensure all database keys are upper case
db_config = {key.upper(): value for key, value in db_config.items()}

for key in required_keys:
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

if 'sqlite' in db_engine:
    db_name = str(Path(db_name).resolve())
    db_config['NAME'] = db_name

logger.info('DB_ENGINE: %s', db_engine)
logger.info('DB_NAME: %s', db_name)
logger.info('DB_HOST: %s', db_host)

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
db_options = db_config.get('OPTIONS', db_config.get('options', None))

if db_options is None:
    db_options = {}

# Specific options for postgres backend
if 'postgres' in db_engine:  # pragma: no cover
    from django.db.backends.postgresql.psycopg_any import IsolationLevel

    # Connection timeout
    if 'connect_timeout' not in db_options:
        # The DB server is in the same data center, it should not take very
        # long to connect to the database server
        # # seconds, 2 is minimum allowed by libpq
        db_options['connect_timeout'] = int(
            get_setting('INVENTREE_DB_TIMEOUT', 'database.timeout', 2)
        )

    # Setup TCP keepalive
    # DB server is in the same DC, it should not become unresponsive for
    # very long. With the defaults below we wait 5 seconds for the network
    # issue to resolve itself.  It it that doesn't happen whatever happened
    # is probably fatal and no amount of waiting is going to fix it.
    # # 0 - TCP Keepalives disabled; 1 - enabled
    if 'keepalives' not in db_options:
        db_options['keepalives'] = int(
            get_setting('INVENTREE_DB_TCP_KEEPALIVES', 'database.tcp_keepalives', 1)
        )

    # Seconds after connection is idle to send keep alive
    if 'keepalives_idle' not in db_options:
        db_options['keepalives_idle'] = int(
            get_setting(
                'INVENTREE_DB_TCP_KEEPALIVES_IDLE', 'database.tcp_keepalives_idle', 1
            )
        )

    # Seconds after missing ACK to send another keep alive
    if 'keepalives_interval' not in db_options:
        db_options['keepalives_interval'] = int(
            get_setting(
                'INVENTREE_DB_TCP_KEEPALIVES_INTERVAL',
                'database.tcp_keepalives_internal',
                '1',
            )
        )

    # Number of missing ACKs before we close the connection
    if 'keepalives_count' not in db_options:
        db_options['keepalives_count'] = int(
            get_setting(
                'INVENTREE_DB_TCP_KEEPALIVES_COUNT',
                'database.tcp_keepalives_count',
                '5',
            )
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
    if 'isolation_level' not in db_options:
        serializable = get_boolean_setting(
            'INVENTREE_DB_ISOLATION_SERIALIZABLE', 'database.serializable', False
        )
        db_options['isolation_level'] = (
            IsolationLevel.SERIALIZABLE
            if serializable
            else IsolationLevel.READ_COMMITTED
        )

# Specific options for MySql / MariaDB backend
elif 'mysql' in db_engine:  # pragma: no cover
    # TODO TCP time outs and keepalives

    # MariaDB's default isolation level is Repeatable Read which is
    # normally fine, but most developers think the database server is
    # actually going to Serializable type checks on the queries to
    # protect against siumltaneous changes.
    # https://mariadb.com/kb/en/mariadb-transactions-and-isolation-levels-for-sql-server-users/#changing-the-isolation-level
    # https://docs.djangoproject.com/en/3.2/ref/databases/#mysql-isolation-level
    if 'isolation_level' not in db_options:
        serializable = get_boolean_setting(
            'INVENTREE_DB_ISOLATION_SERIALIZABLE', 'database.serializable', False
        )
        db_options['isolation_level'] = (
            'serializable' if serializable else 'read committed'
        )

# Specific options for sqlite backend
elif 'sqlite' in db_engine:
    # TODO: Verify timeouts are not an issue because no network is involved for SQLite

    # SQLite's default isolation level is Serializable due to SQLite's
    # single writer implementation.  Presumably as a result of this, it is
    # not possible to implement any lower isolation levels in SQLite.
    # https://www.sqlite.org/isolation.html
    pass

# Provide OPTIONS dict back to the database configuration dict
db_config['OPTIONS'] = db_options

# Set testing options for the database
db_config['TEST'] = {'CHARSET': 'utf8'}

# Set collation option for mysql test database
if 'mysql' in db_engine:
    db_config['TEST']['COLLATION'] = 'utf8_general_ci'  # pragma: no cover

DATABASES = {'default': db_config}

# login settings
REMOTE_LOGIN = get_boolean_setting(
    'INVENTREE_REMOTE_LOGIN', 'remote_login_enabled', False
)
REMOTE_LOGIN_HEADER = get_setting(
    'INVENTREE_REMOTE_LOGIN_HEADER', 'remote_login_header', 'REMOTE_USER'
)

# region Tracing / error tracking
inventree_tags = {
    'testing': TESTING,
    'docker': DOCKER,
    'debug': DEBUG,
    'remote': REMOTE_LOGIN,
}

# sentry.io integration for error reporting
SENTRY_ENABLED = get_boolean_setting(
    'INVENTREE_SENTRY_ENABLED', 'sentry_enabled', False
)

# Default Sentry DSN (can be overridden if user wants custom sentry integration)
SENTRY_DSN = get_setting('INVENTREE_SENTRY_DSN', 'sentry_dsn', default_sentry_dsn())
SENTRY_SAMPLE_RATE = float(
    get_setting('INVENTREE_SENTRY_SAMPLE_RATE', 'sentry_sample_rate', 0.1)
)

if SENTRY_ENABLED and SENTRY_DSN:  # pragma: no cover
    init_sentry(SENTRY_DSN, SENTRY_SAMPLE_RATE, inventree_tags)

# OpenTelemetry tracing
TRACING_ENABLED = get_boolean_setting(
    'INVENTREE_TRACING_ENABLED', 'tracing.enabled', False
)

if TRACING_ENABLED:  # pragma: no cover
    from InvenTree.tracing import setup_instruments, setup_tracing

    _t_endpoint = get_setting('INVENTREE_TRACING_ENDPOINT', 'tracing.endpoint', None)
    _t_headers = get_setting('INVENTREE_TRACING_HEADERS', 'tracing.headers', None, dict)

    if _t_headers is None:
        _t_headers = {}

    if _t_endpoint:
        logger.info('OpenTelemetry tracing enabled')

        _t_resources = get_setting(
            'INVENTREE_TRACING_RESOURCES',
            'tracing.resources',
            default_value=None,
            typecast=dict,
        )
        cstm_tags = {'inventree.env.' + k: v for k, v in inventree_tags.items()}
        tracing_resources = {**cstm_tags, **_t_resources}

        setup_tracing(
            _t_endpoint,
            _t_headers,
            resources_input=tracing_resources,
            console=get_boolean_setting(
                'INVENTREE_TRACING_CONSOLE', 'tracing.console', False
            ),
            auth=get_setting(
                'INVENTREE_TRACING_AUTH',
                'tracing.auth',
                default_value=None,
                typecast=dict,
            ),
            is_http=get_setting('INVENTREE_TRACING_IS_HTTP', 'tracing.is_http', True),
            append_http=get_boolean_setting(
                'INVENTREE_TRACING_APPEND_HTTP', 'tracing.append_http', True
            ),
        )
        # Run tracing/logging instrumentation
        setup_instruments()
    else:
        logger.warning('OpenTelemetry tracing not enabled because endpoint is not set')

# endregion

# Cache configuration
GLOBAL_CACHE_ENABLED = is_global_cache_enabled()

CACHES = {'default': get_cache_config(GLOBAL_CACHE_ENABLED)}

_q_worker_timeout = int(
    get_setting('INVENTREE_BACKGROUND_TIMEOUT', 'background.timeout', 90)
)


# Prevent running multiple background workers if global cache is disabled
# This is to prevent scheduling conflicts due to the lack of a shared cache
BACKGROUND_WORKER_COUNT = (
    int(get_setting('INVENTREE_BACKGROUND_WORKERS', 'background.workers', 4))
    if GLOBAL_CACHE_ENABLED
    else 1
)

# django-q background worker configuration
Q_CLUSTER = {
    'name': 'InvenTree',
    'label': 'Background Tasks',
    'workers': BACKGROUND_WORKER_COUNT,
    'timeout': _q_worker_timeout,
    'retry': max(120, _q_worker_timeout + 30),
    'max_attempts': int(
        get_setting('INVENTREE_BACKGROUND_MAX_ATTEMPTS', 'background.max_attempts', 5)
    ),
    'queue_limit': 50,
    'catch_up': False,
    'bulk': 10,
    'orm': 'default',
    'cache': 'default',
    'sync': False,
    'poll': 1.5,
}

# Configure django-q sentry integration
if SENTRY_ENABLED and SENTRY_DSN:
    Q_CLUSTER['error_reporter'] = {'sentry': {'dsn': SENTRY_DSN}}

if GLOBAL_CACHE_ENABLED:  # pragma: no cover
    # If using external redis cache, make the cache the broker for Django Q
    # as well
    Q_CLUSTER['django_redis'] = 'worker'

# database user sessions
SESSION_ENGINE = 'user_sessions.backends.db'
LOGOUT_REDIRECT_URL = get_setting(
    'INVENTREE_LOGOUT_REDIRECT_URL', 'logout_redirect_url', 'index'
)

SILENCED_SYSTEM_CHECKS = ['admin.E410', 'templates.E003', 'templates.W003']

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
    },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Extra (optional) URL validators
# See https://docs.djangoproject.com/en/2.2/ref/validators/#django.core.validators.URLValidator

EXTRA_URL_SCHEMES = get_setting('INVENTREE_EXTRA_URL_SCHEMES', 'extra_url_schemes', [])

if type(EXTRA_URL_SCHEMES) not in [list]:  # pragma: no cover
    logger.warning('extra_url_schemes not correctly formatted')
    EXTRA_URL_SCHEMES = []

LANGUAGES = locales.LOCALES

LOCALE_CODES = [lang[0] for lang in LANGUAGES]

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/
LANGUAGE_CODE = get_setting('INVENTREE_LANGUAGE', 'language', 'en-us')

if (
    LANGUAGE_CODE not in LOCALE_CODES
    and LANGUAGE_CODE.split('-')[0] not in LOCALE_CODES
):  # pragma: no cover
    logger.warning(
        'Language code %s not supported - defaulting to en-us', LANGUAGE_CODE
    )
    LANGUAGE_CODE = 'en-us'

# Store language settings for 30 days
LANGUAGE_COOKIE_AGE = 2592000

# Testing interface translations
if get_boolean_setting('TEST_TRANSLATIONS', default_value=False):  # pragma: no cover
    # Set default language
    LANGUAGE_CODE = 'xx'

    # Add to language catalog
    LANGUAGES.append(('xx', 'Test'))

    # Add custom languages not provided by Django
    EXTRA_LANG_INFO = {'xx': {'code': 'xx', 'name': 'Test', 'name_local': 'Test'}}
    LANG_INFO = dict(django.conf.locale.LANG_INFO, **EXTRA_LANG_INFO)
    django.conf.locale.LANG_INFO = LANG_INFO

# Maximum number of decimal places for currency rendering
CURRENCY_DECIMAL_PLACES = 6

# Custom currency exchange backend
EXCHANGE_BACKEND = 'InvenTree.exchange.InvenTreeExchange'

# Email configuration options
EMAIL_BACKEND = get_setting(
    'INVENTREE_EMAIL_BACKEND',
    'email.backend',
    'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = get_setting('INVENTREE_EMAIL_HOST', 'email.host', '')
EMAIL_PORT = get_setting('INVENTREE_EMAIL_PORT', 'email.port', 25, typecast=int)
EMAIL_HOST_USER = get_setting('INVENTREE_EMAIL_USERNAME', 'email.username', '')
EMAIL_HOST_PASSWORD = get_setting('INVENTREE_EMAIL_PASSWORD', 'email.password', '')
EMAIL_SUBJECT_PREFIX = get_setting(
    'INVENTREE_EMAIL_PREFIX', 'email.prefix', '[InvenTree] '
)
EMAIL_USE_TLS = get_boolean_setting('INVENTREE_EMAIL_TLS', 'email.tls', False)
EMAIL_USE_SSL = get_boolean_setting('INVENTREE_EMAIL_SSL', 'email.ssl', False)

DEFAULT_FROM_EMAIL = get_setting('INVENTREE_EMAIL_SENDER', 'email.sender', '')

# If "from" email not specified, default to the username
if not DEFAULT_FROM_EMAIL:
    DEFAULT_FROM_EMAIL = get_setting('INVENTREE_EMAIL_USERNAME', 'email.username', '')

EMAIL_USE_LOCALTIME = False
EMAIL_TIMEOUT = 60

LOCALE_PATHS = (BASE_DIR.joinpath('locale/'),)

TIME_ZONE = get_setting('INVENTREE_TIMEZONE', 'timezone', 'UTC')

# Check that the timezone is valid
try:
    ZoneInfo(TIME_ZONE)
except ZoneInfoNotFoundError:  # pragma: no cover
    raise ValueError(f"Specified timezone '{TIME_ZONE}' is not valid")

USE_I18N = True

# Do not use native timezone support in "test" mode
# It generates a *lot* of cruft in the logs
USE_TZ = bool(not TESTING)

DATE_INPUT_FORMATS = ['%Y-%m-%d']

# Site URL can be specified statically, or via a run-time setting
SITE_URL = get_setting('INVENTREE_SITE_URL', 'site_url', None)

if SITE_URL:
    logger.info('Using Site URL: %s', SITE_URL)

    # Check that the site URL is valid
    try:
        validator = URLValidator()
        validator(SITE_URL)
    except Exception:
        msg = f"Invalid SITE_URL value: '{SITE_URL}'. InvenTree server cannot start."
        logger.error(msg)
        print(msg)
        sys.exit(-1)

else:
    logger.warning('No SITE_URL specified. Some features may not work correctly')
    logger.warning(
        'Specify a SITE_URL in the configuration file or via an environment variable'
    )

# Enable or disable multi-site framework
SITE_MULTI = get_boolean_setting('INVENTREE_SITE_MULTI', 'site_multi', False)

# If a SITE_ID is specified
SITE_ID = get_setting('INVENTREE_SITE_ID', 'site_id', 1 if SITE_MULTI else None)

# Load the allauth social backends
SOCIAL_BACKENDS = get_setting(
    'INVENTREE_SOCIAL_BACKENDS', 'social_backends', [], typecast=list
)

if not SITE_MULTI:
    INSTALLED_APPS.remove('django.contrib.sites')

# List of allowed hosts (default = allow all)
# Ref: https://docs.djangoproject.com/en/4.2/ref/settings/#allowed-hosts
ALLOWED_HOSTS = get_setting(
    'INVENTREE_ALLOWED_HOSTS',
    config_key='allowed_hosts',
    default_value=[],
    typecast=list,
)

if SITE_URL and SITE_URL not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(SITE_URL)

if not ALLOWED_HOSTS:
    if DEBUG:
        logger.info(
            'No ALLOWED_HOSTS specified. Defaulting to ["*"] for debug mode. This is not recommended for production use'
        )
        ALLOWED_HOSTS = ['*']
    elif not TESTING:
        logger.error(
            'No ALLOWED_HOSTS specified. Please provide a list of allowed hosts, or specify INVENTREE_SITE_URL'
        )

        # Server cannot run without ALLOWED_HOSTS
        if isInMainThread():
            sys.exit(-1)

# Ensure that the ALLOWED_HOSTS do not contain any scheme info
for i, host in enumerate(ALLOWED_HOSTS):
    if '://' in host:
        ALLOWED_HOSTS[i] = host = host.split('://')[1]

    if ':' in host:
        ALLOWED_HOSTS[i] = host = host.split(':')[0]

# List of trusted origins for unsafe requests
# Ref: https://docs.djangoproject.com/en/4.2/ref/settings/#csrf-trusted-origins
CSRF_TRUSTED_ORIGINS = get_setting(
    'INVENTREE_TRUSTED_ORIGINS',
    config_key='trusted_origins',
    default_value=[],
    typecast=list,
)

# If a list of trusted is not specified, but a site URL has been specified, use that
if SITE_URL and SITE_URL not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(SITE_URL)

if DEBUG:
    for origin in [
        'http://localhost',
        'http://*.localhost',
        'http://*localhost:8000',
        'http://*localhost:5173',
    ]:
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)

if (
    not TESTING and len(CSRF_TRUSTED_ORIGINS) == 0 and isInMainThread()
):  # pragma: no cover
    # Server thread cannot run without CSRF_TRUSTED_ORIGINS
    logger.error(
        'No CSRF_TRUSTED_ORIGINS specified. Please provide a list of trusted origins, or specify INVENTREE_SITE_URL'
    )
    sys.exit(-1)

COOKIE_MODE = (
    str(get_setting('INVENTREE_COOKIE_SAMESITE', 'cookie.samesite', 'False'))
    .lower()
    .strip()
)

# Valid modes (as per the django settings documentation)
valid_cookie_modes = ['lax', 'strict', 'none']

COOKIE_MODE = COOKIE_MODE.capitalize() if COOKIE_MODE in valid_cookie_modes else False

# Additional CSRF settings
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_COOKIE_NAME = 'csrftoken'

CSRF_COOKIE_SAMESITE = COOKIE_MODE
SESSION_COOKIE_SAMESITE = COOKIE_MODE
LANGUAGE_COOKIE_SAMESITE = COOKIE_MODE

"""Set the SESSION_COOKIE_SECURE value based on the following rules:
- False if the server is running in DEBUG mode
- True if samesite cookie setting is set to 'None'
- Otherwise, use the value specified in the configuration file (or env var)
"""
COOKIE_SECURE = (
    False
    if DEBUG
    else (
        SESSION_COOKIE_SAMESITE == 'None'
        or get_boolean_setting(
            'INVENTREE_SESSION_COOKIE_SECURE', 'cookie.secure', False
        )
    )
)

CSRF_COOKIE_SECURE = COOKIE_SECURE
SESSION_COOKIE_SECURE = COOKIE_SECURE
LANGUAGE_COOKIE_SECURE = COOKIE_SECURE

# Ref: https://docs.djangoproject.com/en/4.2/ref/settings/#std-setting-SECURE_PROXY_SSL_HEADER
if ssl_header := get_boolean_setting(
    'INVENTREE_USE_X_FORWARDED_PROTO', 'use_x_forwarded_proto', False
):
    # The default header name is 'HTTP_X_FORWARDED_PROTO', but can be adjusted
    ssl_header_name = get_setting(
        'INVENTREE_X_FORWARDED_PROTO_NAME',
        'x_forwarded_proto_name',
        'HTTP_X_FORWARDED_PROTO',
    )
    SECURE_PROXY_SSL_HEADER = (ssl_header_name, 'https')

USE_X_FORWARDED_HOST = get_boolean_setting(
    'INVENTREE_USE_X_FORWARDED_HOST',
    config_key='use_x_forwarded_host',
    default_value=False,
)

USE_X_FORWARDED_PORT = get_boolean_setting(
    'INVENTREE_USE_X_FORWARDED_PORT',
    config_key='use_x_forwarded_port',
    default_value=False,
)

# Cross Origin Resource Sharing (CORS) options
# Refer to the django-cors-headers documentation for more information
# Ref: https://github.com/adamchainz/django-cors-headers

# Extract CORS options from configuration file
CORS_ALLOW_ALL_ORIGINS = get_boolean_setting(
    'INVENTREE_CORS_ORIGIN_ALLOW_ALL', config_key='cors.allow_all', default_value=DEBUG
)

CORS_ALLOW_CREDENTIALS = get_boolean_setting(
    'INVENTREE_CORS_ALLOW_CREDENTIALS',
    config_key='cors.allow_credentials',
    default_value=True,
)

# Only allow CORS access to the following URL endpoints
CORS_URLS_REGEX = r'^/(api|auth|media|plugin|static)/.*$'

CORS_ALLOWED_ORIGINS = get_setting(
    'INVENTREE_CORS_ORIGIN_WHITELIST',
    config_key='cors.whitelist',
    default_value=[],
    typecast=list,
)

# If no CORS origins are specified, but a site URL has been specified, use that
if SITE_URL and SITE_URL not in CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS.append(SITE_URL)

CORS_ALLOWED_ORIGIN_REGEXES = get_setting(
    'INVENTREE_CORS_ORIGIN_REGEX',
    config_key='cors.regex',
    default_value=[],
    typecast=list,
)

# In debug mode allow CORS requests from localhost
# This allows connection from the frontend development server
if DEBUG:
    CORS_ALLOWED_ORIGIN_REGEXES.append(r'^http://localhost:\d+$')

if CORS_ALLOW_ALL_ORIGINS:
    logger.info('CORS: All origins allowed')
else:
    if CORS_ALLOWED_ORIGINS:
        logger.info('CORS: Whitelisted origins: %s', CORS_ALLOWED_ORIGINS)

    if CORS_ALLOWED_ORIGIN_REGEXES:
        logger.info('CORS: Whitelisted origin regexes: %s', CORS_ALLOWED_ORIGIN_REGEXES)

for app in SOCIAL_BACKENDS:
    # Ensure that the app starts with 'allauth.socialaccount.providers'
    social_prefix = 'allauth.socialaccount.providers.'

    if not app.startswith(social_prefix):  # pragma: no cover
        app = social_prefix + app

    INSTALLED_APPS.append(app)  # pragma: no cover

SOCIALACCOUNT_PROVIDERS = get_setting(
    'INVENTREE_SOCIAL_PROVIDERS', 'social_providers', None, typecast=dict
)

SOCIALACCOUNT_STORE_TOKENS = True

# Explicitly set empty URL prefix for OIDC
# The SOCIALACCOUNT_OPENID_CONNECT_URL_PREFIX setting was introduced in v0.60.0
# Ref: https://github.com/pennersr/django-allauth/blob/0.60.0/ChangeLog.rst#backwards-incompatible-changes
SOCIALACCOUNT_OPENID_CONNECT_URL_PREFIX = ''

# settings for allauth
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = get_setting(
    'INVENTREE_LOGIN_CONFIRM_DAYS', 'login_confirm_days', 3, typecast=int
)

# allauth rate limiting: https://docs.allauth.org/en/latest/account/rate_limits.html
# The default login rate limit is "5/m/user,5/m/ip,5/m/key"
login_attempts = get_setting('INVENTREE_LOGIN_ATTEMPTS', 'login_attempts', 5)

try:
    login_attempts = int(login_attempts)
    login_attempts = f'{login_attempts}/m,{login_attempts}/m'
except ValueError:
    pass

ACCOUNT_RATE_LIMITS = {'login_failed': login_attempts}

# Default protocol for login
ACCOUNT_DEFAULT_HTTP_PROTOCOL = get_setting(
    'INVENTREE_LOGIN_DEFAULT_HTTP_PROTOCOL', 'login_default_protocol', None
)

if ACCOUNT_DEFAULT_HTTP_PROTOCOL is None:
    if SITE_URL and SITE_URL.startswith('https://'):
        # auto-detect HTTPS prtoocol
        ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
    else:
        # default to http
        ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'

ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
ACCOUNT_PREVENT_ENUMERATION = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = EMAIL_SUBJECT_PREFIX
# 2FA
REMOVE_SUCCESS_URL = 'settings'

# override forms / adapters
ACCOUNT_FORMS = {
    'login': 'InvenTree.auth_overrides.CustomLoginForm',
    'signup': 'InvenTree.auth_overrides.CustomSignupForm',
    'add_email': 'allauth.account.forms.AddEmailForm',
    'change_password': 'allauth.account.forms.ChangePasswordForm',
    'set_password': 'allauth.account.forms.SetPasswordForm',
    'reset_password': 'allauth.account.forms.ResetPasswordForm',
    'reset_password_from_key': 'allauth.account.forms.ResetPasswordKeyForm',
    'disconnect': 'allauth.socialaccount.forms.DisconnectForm',
}

ALLAUTH_2FA_FORMS = {'setup': 'InvenTree.auth_overrides.CustomTOTPDeviceForm'}
# Determine if multi-factor authentication is enabled for this server (default = True)
MFA_ENABLED = get_boolean_setting('INVENTREE_MFA_ENABLED', 'mfa_enabled', True)

SOCIALACCOUNT_ADAPTER = 'InvenTree.auth_overrides.CustomSocialAccountAdapter'
ACCOUNT_ADAPTER = 'InvenTree.auth_overrides.CustomAccountAdapter'

# Markdownify configuration
# Ref: https://django-markdownify.readthedocs.io/en/latest/settings.html

MARKDOWNIFY = {
    'default': {
        'BLEACH': True,
        'WHITELIST_ATTRS': ['href', 'src', 'alt'],
        'MARKDOWN_EXTENSIONS': ['markdown.extensions.extra'],
        'WHITELIST_TAGS': [
            'a',
            'abbr',
            'b',
            'blockquote',
            'code',
            'em',
            'h1',
            'h2',
            'h3',
            'h4',
            'h5',
            'hr',
            'i',
            'img',
            'li',
            'ol',
            'p',
            'pre',
            's',
            'strong',
            'table',
            'thead',
            'tbody',
            'th',
            'tr',
            'td',
            'ul',
        ],
    }
}

# Ignore these error typeps for in-database error logging
IGNORED_ERRORS = [Http404, django.core.exceptions.PermissionDenied]

# Maintenance mode
MAINTENANCE_MODE_RETRY_AFTER = 10
MAINTENANCE_MODE_STATE_BACKEND = 'InvenTree.backends.InvenTreeMaintenanceModeBackend'

# Flag to allow table events during testing
TESTING_TABLE_EVENTS = False

# Flag to allow pricing recalculations during testing
TESTING_PRICING = False

# User interface customization values
CUSTOM_LOGO = get_custom_file(
    'INVENTREE_CUSTOM_LOGO', 'customize.logo', 'custom logo', lookup_media=True
)
CUSTOM_SPLASH = get_custom_file(
    'INVENTREE_CUSTOM_SPLASH', 'customize.splash', 'custom splash'
)

CUSTOMIZE = get_setting(
    'INVENTREE_CUSTOMIZE', 'customize', default_value=None, typecast=dict
)

# Load settings for the frontend interface
FRONTEND_SETTINGS = config.get_frontend_settings(debug=DEBUG)
FRONTEND_URL_BASE = FRONTEND_SETTINGS['base_url']

if DEBUG:
    logger.info('InvenTree running with DEBUG enabled')

logger.info("MEDIA_ROOT: '%s'", MEDIA_ROOT)
logger.info("STATIC_ROOT: '%s'", STATIC_ROOT)

# Flags
FLAGS = {
    'EXPERIMENTAL': [
        {'condition': 'boolean', 'value': DEBUG},
        {'condition': 'parameter', 'value': 'experimental='},
    ],  # Should experimental features be turned on?
    'NEXT_GEN': [
        {'condition': 'parameter', 'value': 'ngen='}
    ],  # Should next-gen features be turned on?
}

# Get custom flags from environment/yaml
CUSTOM_FLAGS = get_setting('INVENTREE_FLAGS', 'flags', None, typecast=dict)
if CUSTOM_FLAGS:
    if not isinstance(CUSTOM_FLAGS, dict):
        logger.error('Invalid custom flags, must be valid dict: %s', str(CUSTOM_FLAGS))
    else:
        logger.info('Custom flags: %s', str(CUSTOM_FLAGS))
        FLAGS.update(CUSTOM_FLAGS)

# Magic login django-sesame
SESAME_MAX_AGE = 300
LOGIN_REDIRECT_URL = '/api/auth/login-redirect/'

# Configuratino for API schema generation
SPECTACULAR_SETTINGS = {
    'TITLE': 'InvenTree API',
    'DESCRIPTION': 'API for InvenTree - the intuitive open source inventory management system',
    'LICENSE': {
        'name': 'MIT',
        'url': 'https://github.com/inventree/InvenTree/blob/master/LICENSE',
    },
    'EXTERNAL_DOCS': {
        'description': 'More information about InvenTree in the official docs',
        'url': 'https://docs.inventree.org',
    },
    'VERSION': str(inventreeApiVersion()),
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/',
}

if SITE_URL and not TESTING:
    SPECTACULAR_SETTINGS['SERVERS'] = [{'url': SITE_URL}]
