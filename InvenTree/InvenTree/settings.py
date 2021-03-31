"""
Django settings for InvenTree project.

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
import tempfile
from datetime import datetime

import yaml
from django.utils.translation import gettext_lazy as _


def _is_true(x):
    # Shortcut function to determine if a value "looks" like a boolean
    return str(x).lower() in ['1', 'y', 'yes', 't', 'true']


def get_setting(environment_var, backup_val, default_value=None):
    """
    Helper function for retrieving a configuration setting value

    - First preference is to look for the environment variable
    - Second preference is to look for the value of the settings file
    - Third preference is the default value
    """

    val = os.getenv(environment_var)

    if val is not None:
        return val

    if backup_val is not None:
        return backup_val

    return default_value


# Determine if we are running in "test" mode e.g. "manage.py test"
TESTING = 'test' in sys.argv

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cfg_filename = os.path.join(BASE_DIR, 'config.yaml')

if not os.path.exists(cfg_filename):
    print("Error: config.yaml not found")
    sys.exit(-1)

with open(cfg_filename, 'r') as cfg:
    CONFIG = yaml.safe_load(cfg)

# Default action is to run the system in Debug mode
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = _is_true(get_setting(
    'INVENTREE_DEBUG',
    CONFIG.get('debug', True)
))

# Configure logging settings
log_level = get_setting(
    'INVENTREE_LOG_LEVEL',
    CONFIG.get('log_level', 'DEBUG')
)

logging.basicConfig(
    level=log_level,
    format="%(asctime)s %(levelname)s %(message)s",
)

if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
    log_level = 'WARNING'

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
}

# Get a logger instance for this setup file
logger = logging.getLogger(__name__)

if os.getenv("INVENTREE_SECRET_KEY"):
    # Secret key passed in directly
    SECRET_KEY = os.getenv("INVENTREE_SECRET_KEY").strip()
    logger.info("SECRET_KEY loaded by INVENTREE_SECRET_KEY")
else:
    # Secret key passed in by file location
    key_file = os.getenv("INVENTREE_SECRET_KEY_FILE")

    if key_file:
        if os.path.isfile(key_file):
            logger.info("SECRET_KEY loaded by INVENTREE_SECRET_KEY_FILE")
        else:
            logger.error(f"Secret key file {key_file} not found")
            exit(-1)
    else:
        # default secret key location
        key_file = os.path.join(BASE_DIR, "secret_key.txt")
        logger.info(f"SECRET_KEY loaded from {key_file}")
    try:
        SECRET_KEY = open(key_file, "r").read().strip()
    except Exception:
        logger.exception(f"Couldn't load keyfile {key_file}")
        sys.exit(-1)

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
        CORS_ORIGIN_WHITELIST = cors_opt.get('whitelist', [])

# Web URL endpoint for served static files
STATIC_URL = '/static/'

# The filesystem location for served static files
STATIC_ROOT = os.path.abspath(
    get_setting(
        'INVENTREE_STATIC_ROOT',
        CONFIG.get('static_root', os.path.join(BASE_DIR, 'static'))
    )
)

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'InvenTree', 'static'),
]

# Color Themes Directory
STATIC_COLOR_THEMES_DIR = os.path.join(STATIC_ROOT, 'css', 'color-themes')

# Web URL endpoint for served media files
MEDIA_URL = '/media/'

# The filesystem location for served static files
MEDIA_ROOT = os.path.abspath(
    get_setting(
        'INVENTREE_MEDIA_ROOT',
        CONFIG.get('media_root', os.path.join(BASE_DIR, 'media'))
    )
)

if DEBUG:
    logger.info("InvenTree running in DEBUG mode")

logger.info(f"MEDIA_ROOT: '{MEDIA_ROOT}'")
logger.info(f"STATIC_ROOT: '{STATIC_ROOT}'")

# Application definition

INSTALLED_APPS = [

    # Core django modules
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

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
    'InvenTree.apps.InvenTreeConfig',       # InvenTree app runs last

    # Third part add-ons
    'django_filters',                       # Extended filter functionality
    'dbbackup',                             # Database backup / restore
    'rest_framework',                       # DRF (Django Rest Framework)
    'rest_framework.authtoken',             # Token authentication for API
    'corsheaders',                          # Cross-origin Resource Sharing for DRF
    'crispy_forms',                         # Improved form rendering
    'import_export',                        # Import / export tables to file
    'django_cleanup.apps.CleanupConfig',    # Automatically delete orphaned MEDIA files
    'mptt',                                 # Modified Preorder Tree Traversal
    'markdownx',                            # Markdown editing
    'markdownify',                          # Markdown template rendering
    'django_admin_shell',                   # Python shell for the admin interface
    'djmoney',                              # django-money integration
    'djmoney.contrib.exchange',             # django-money exchange rates
    'error_report',                         # Error reporting in the admin interface
    'django_q',
]

MIDDLEWARE = CONFIG.get('middleware', [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'InvenTree.middleware.AuthRequiredMiddleware'
])

# Error reporting middleware
MIDDLEWARE.append('error_report.middleware.ExceptionProcessor')

AUTHENTICATION_BACKENDS = CONFIG.get('authentication_backends', [
    'django.contrib.auth.backends.ModelBackend'
])

# If the debug toolbar is enabled, add the modules
if DEBUG and CONFIG.get('debug_toolbar', False):
    logger.info("Running with DEBUG_TOOLBAR enabled")
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

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
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'InvenTree.context.health_status',
                'InvenTree.context.status_codes',
                'InvenTree.context.user_roles',
            ],
        },
    },
]

REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
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
}

WSGI_APPLICATION = 'InvenTree.wsgi.application'

# django-q configuration
Q_CLUSTER = {
    'name': 'InvenTree',
    'workers': 4,
    'timeout': 90,
    'retry': 120,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default',
    'sync': True,
}

# Markdownx configuration
# Ref: https://neutronx.github.io/django-markdownx/customization/
MARKDOWNX_MEDIA_PATH = datetime.now().strftime('markdownx/%Y/%m/%d')

# Markdownify configuration
# Ref: https://django-markdownify.readthedocs.io/en/latest/settings.html

MARKDOWNIFY_WHITELIST_TAGS = [
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
]

MARKDOWNIFY_WHITELIST_ATTRS = [
    'href',
    'src',
    'alt',
]

MARKDOWNIFY_BLEACH = False

DATABASES = {}

"""
Configure the database backend based on the user-specified values.

- Primarily this configuration happens in the config.yaml file
- However there may be reason to configure the DB via environmental variables
- The following code lets the user "mix and match" database configuration
"""

logger.info("Configuring database backend:")

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
        logger.info(f"{env_key}={env_var}")
        # Override configuration value
        db_config[key] = env_var

# Check that required database configuration options are specified
reqiured_keys = ['ENGINE', 'NAME']

for key in reqiured_keys:
    if key not in db_config:
        error_msg = f'Missing required database configuration value {key} in config.yaml'
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

db_engine = db_config['ENGINE']

if db_engine.lower() in ['sqlite3', 'postgresql', 'mysql']:
    # Prepend the required python module string
    db_engine = f'django.db.backends.{db_engine.lower()}'
    db_config['ENGINE'] = db_engine

db_name = db_config['NAME']
db_host = db_config.get('HOST', "''")

print("InvenTree Database Configuration")
print("================================")
print(f"ENGINE: {db_engine}")
print(f"NAME: {db_name}")
print(f"HOST: {db_host}")

DATABASES['default'] = db_config

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
}

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

if not type(EXTRA_URL_SCHEMES) in [list]:
    logger.warning("extra_url_schemes not correctly formatted")
    EXTRA_URL_SCHEMES = []

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = CONFIG.get('language', 'en-us')

# If a new language translation is supported, it must be added here
LANGUAGES = [
    ('en', _('English')),
    ('fr', _('French')),
    ('de', _('German')),
    ('pk', _('Polish')),
    ('tr', _('Turkish')),
]

# Currencies available for use
CURRENCIES = CONFIG.get(
    'currencies',
    [
        'AUD', 'CAD', 'EUR', 'GBP', 'JPY', 'NZD', 'USD',
    ],
)

# TODO - Allow live web-based backends in the future
EXCHANGE_BACKEND = 'InvenTree.exchange.InvenTreeManualExchangeBackend'

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale/'),
)

TIME_ZONE = CONFIG.get('timezone', 'UTC')

USE_I18N = True

USE_L10N = True

# Do not use native timezone support in "test" mode
# It generates a *lot* of cruft in the logs
if not TESTING:
    USE_TZ = True

DATE_INPUT_FORMATS = [
    "%Y-%m-%d",
]

# crispy forms use the bootstrap templates
CRISPY_TEMPLATE_PACK = 'bootstrap3'

# Use database transactions when importing / exporting data
IMPORT_EXPORT_USE_TRANSACTIONS = True

BACKUP_DIR = get_setting(
    'INVENTREE_BACKUP_DIR',
    CONFIG.get('backup_dir', tempfile.gettempdir()),
)

# Settings for dbbsettings app
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {
    'location': BACKUP_DIR,
}

# Internal IP addresses allowed to see the debug toolbar
INTERNAL_IPS = [
    '127.0.0.1',
]
