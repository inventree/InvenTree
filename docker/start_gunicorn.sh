#!/bin/sh

set -e

export DATABASE_HOST=${DATABASE_HOST:-db}
export DATABASE_PORT=${DATABASE_PORT:-5432}
export INVENTREE_SECRET_KEY
export INVENTREE_SECRET_KEY_FILE

export DEBUG=True

if [ -z "$DATABASE_USER" ]; then
    if [ -f "$DATABASE_USER_FILE" ]; then
        export DATABASE_USER=$(cat $DATABASE_USER_FILE)
    else
        echo "No DATABASE_USER or DATABASE_USER_FILE set"
        exit 1
    fi
fi

if [ -z "$DATABASE_PASSWORD" ]; then
    if [ -f "$DATABASE_PASSWORD_FILE" ]; then
        export DATABASE_PASSWORD=$(cat $DATABASE_PASSWORD_FILE)
    else
        echo "No DATABASE_PASSWORD or DATABASE_PASSWORD_FILE set"
        exit 1
    fi
fi

cat > "$INVENTREE_HOME/config.yaml" <<EOF
# Database backend selection - Configure backend database settings
# Ref: https://docs.djangoproject.com/en/2.2/ref/settings/#std:setting-DATABASES
# Specify database parameters below as they appear in the Django docs
database:
  
  ENGINE: ${DATABASE_ENGINE:-django.db.backends.postgresql_psycopg2}
  NAME: ${DATABASE_NAME:-inventree}
  USER: ${DATABASE_USER:-inventree}
  PASSWORD: ${DATABASE_PASSWORD:-CHANGEME}
  HOST: ${DATABASE_HOST:-db}
  PORT: ${DATABASE_PORT:-5432}

# Select default system language (default is 'en-us')
language: ${DEFAULT_LANGUAGE:-en-us}

#Currencies to use
currencies:
  - USD
  - AUD
  - CAD
  - EUR
  - GBP
  - JPY
  - NZD

# Set debug to False to run in production mode
debug: ${DEBUG:-False}

# Set the default logging level:
log_level: ${LOG_LEVEL:-DEBUG}

# Allowed hosts (see ALLOWED_HOSTS in Django settings documentation)
# A list of strings representing the host/domain names that this Django site can serve.
# Default behaviour is to allow all hosts (THIS IS NOT SECURE!)
allowed_hosts:
  - ${ALLOWED_HOSTS:-'*'}

# Cross Origin Resource Sharing (CORS) settings (see https://github.com/ottoyiu/django-cors-headers)
# Following parameters are 
cors:
  # CORS_ORIGIN_ALLOW_ALL - If True, the whitelist will not be used and all origins will be accepted.
  allow_all: ${CORS_ALLOW_ALL:-True}
  
  # CORS_ORIGIN_WHITELIST - A list of origins that are authorized to make cross-site HTTP requests. Defaults to []
  # whitelist:
  # - https://example.com
  # - https://sub.example.com

# MEDIA_ROOT is the local filesystem location for storing uploaded files
# By default, it is stored in a directory named 'media' local to the InvenTree directory
# This should be changed for a production installation
media_root: ${MEDIA_ROOT:-'/usr/src/media'}

# STATIC_ROOT is the local filesystem location for storing static files
# By default it is stored in a directory named 'static' local to the InvenTree directory
static_root: ${STATIC_ROOT:-'/usr/src/static'}

# Optional URL schemes to allow in URL fields
# By default, only the following schemes are allowed: ['http', 'https', 'ftp', 'ftps']
# Uncomment the lines below to allow extra schemes
#extra_url_schemes:
#  - mailto
#  - git
#  - ssh

# Set debug_toolbar to True to enable a debugging toolbar for InvenTree
# Note: This will only be displayed if DEBUG mode is enabled, 
#       and only if InvenTree is accessed from a local IP (127.0.0.1)
debug_toolbar: ${DEBUG_TOOLBAR:-False}

# Backup options
# Set the backup_dir parameter to store backup files in a specific location
# If unspecified, the local user's temp directory will be used
backup_dir: ${BACKUP_DIR:-'/home/inventree/backup/'}

# Sentry.io integration
# If you have a sentry.io account, it can be used to log server errors
# Ensure sentry_sdk is installed by running 'pip install sentry-sdk'
sentry:
  enabled: ${SENTRY_ENABLED:-False}
  dsn: ${SENTRY_DSN:-}

# LaTeX report rendering
# InvenTree uses the django-tex plugin to enable LaTeX report rendering
# Ref: https://pypi.org/project/django-tex/
# Note: Ensure that a working LaTeX toolchain is installed and working *before* starting the server
latex:
  # Select the LaTeX interpreter to use for PDF rendering
  # Note: The intepreter needs to be installed on the system!
  # e.g. to install pdflatex: apt-get texlive-latex-base
  enabled: ${LATEX_ENABLED:-False}
  # interpreter: pdflatex 
  # Extra options to pass through to the LaTeX interpreter
  # options: ''
EOF

if [ ! -f "$INVENTREE_HOME/secret_key.txt" ]; then
  cat > "$INVENTREE_HOME/password.awk" <<EOF
BEGIN {
    srand();
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    s = "";
    for(i=0;i<50;i++) {
        s = s "" substr(chars, int(rand()*62), 1);
    }
    print s
}

EOF
  awk -f password.awk > "$INVENTREE_HOME/secret_key.txt"
  rm password.awk
fi

echo "Test connection to database"

/wait-for.sh ${DATABASE_HOST:-db}:${DATABASE_PORT:-5432} -- echo 'Success!'

echo "Give the database a few seconds to warm up"

sleep 10

echo "Running InvenTree database migrations and collecting static files..."
python manage.py check || exit 1
python manage.py collectstatic --noinput || exit 1
python manage.py migrate --noinput || exit 1
python manage.py clearsessions || exit 1
echo "InvenTree static files collected and database migrations completed!"

if [ "$CREATE_SUPERUSER" = "True" ]; then
  python manage.py createsuperuser --noinput
fi

exec gunicorn --access-logfile=- --error-logfile=- --log-level=INFO --forwarded-allow-ips='*' --workers=2 --threads=4 --worker-class=gthread --bind=0.0.0.0:9767 InvenTree.wsgi


