# The InvenTree dockerfile provides two build targets:
#
# production:
# - Required files are copied into the image
# - Runs InvenTree web server under gunicorn
#
# dev:
# - Expects source directories to be loaded as a run-time volume
# - Runs InvenTree web server under django development server
# - Monitors source files for any changes, and live-reloads server


FROM python:3.9-slim as base

# Build arguments for this image
ARG commit_hash=""
ARG commit_date=""

ENV PYTHONUNBUFFERED 1

# Ref: https://github.com/pyca/cryptography/issues/5776
ENV CRYPTOGRAPHY_DONT_BUILD_RUST 1

ENV INVENTREE_LOG_LEVEL="INFO"
ENV INVENTREE_DOCKER="true"

# InvenTree paths
ENV INVENTREE_HOME="/home/inventree"
ENV INVENTREE_MNG_DIR="${INVENTREE_HOME}/InvenTree"
ENV INVENTREE_DATA_DIR="${INVENTREE_HOME}/data"
ENV INVENTREE_STATIC_ROOT="${INVENTREE_DATA_DIR}/static"
ENV INVENTREE_MEDIA_ROOT="${INVENTREE_DATA_DIR}/media"
ENV INVENTREE_PLUGIN_DIR="${INVENTREE_DATA_DIR}/plugins"

# InvenTree configuration files
ENV INVENTREE_CONFIG_FILE="${INVENTREE_DATA_DIR}/config.yaml"
ENV INVENTREE_SECRET_KEY_FILE="${INVENTREE_DATA_DIR}/secret_key.txt"
ENV INVENTREE_PLUGIN_FILE="${INVENTREE_DATA_DIR}/plugins.txt"

# Worker configuration (can be altered by user)
ENV INVENTREE_GUNICORN_WORKERS="4"
ENV INVENTREE_BACKGROUND_WORKERS="4"

# Default web server address:port
ENV INVENTREE_WEB_ADDR=0.0.0.0
ENV INVENTREE_WEB_PORT=8000

LABEL org.label-schema.schema-version="1.0" \
      org.label-schema.build-date=${DATE} \
      org.label-schema.vendor="inventree" \
      org.label-schema.name="inventree/inventree" \
      org.label-schema.url="https://hub.docker.com/r/inventree/inventree" \
      org.label-schema.vcs-url="https://github.com/inventree/InvenTree.git"

# RUN apt-get upgrade && apt-get update
RUN apt-get update

# Install required system packages
RUN apt-get install -y  --no-install-recommends \
    git gcc g++ gettext gnupg \
    # Weasyprint requirements : https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#debian-11
    poppler-utils libpango-1.0-0 libpangoft2-1.0-0 \
    # Image format support
    libjpeg-dev webp \
    # SQLite support
    sqlite3 \
    # PostgreSQL support
    libpq-dev \
    # MySQL / MariaDB support
    default-libmysqlclient-dev mariadb-client && \
    apt-get autoclean && apt-get autoremove

# Update pip
RUN pip install --upgrade pip

# Install required base-level python packages
COPY ./docker/requirements.txt base_requirements.txt
RUN pip install --no-cache-dir -U -r base_requirements.txt

# InvenTree production image:
# - Copies required files from local directory
# - Installs required python packages from requirements.txt
# - Starts a gunicorn webserver

FROM base as production

ENV INVENTREE_DEBUG=False

# As .git directory is not available in production image, we pass the commit information via ENV
ENV INVENTREE_COMMIT_HASH="${commit_hash}"
ENV INVENTREE_COMMIT_DATE="${commit_date}"

# Copy source code
COPY InvenTree ${INVENTREE_HOME}/InvenTree

# Copy other key files
COPY requirements.txt ${INVENTREE_HOME}/requirements.txt
COPY tasks.py ${INVENTREE_HOME}/tasks.py
COPY docker/gunicorn.conf.py ${INVENTREE_HOME}/gunicorn.conf.py
COPY docker/init.sh ${INVENTREE_MNG_DIR}/init.sh

# Need to be running from within this directory
WORKDIR ${INVENTREE_MNG_DIR}

# Drop to the inventree user for the production image
RUN adduser inventree
RUN chown -R inventree:inventree ${INVENTREE_HOME}

USER inventree

# Install InvenTree packages
RUN pip3 install --user --no-cache-dir --disable-pip-version-check -r ${INVENTREE_HOME}/requirements.txt

# Server init entrypoint
ENTRYPOINT ["/bin/bash", "./init.sh"]

# Launch the production server
# TODO: Work out why environment variables cannot be interpolated in this command
# TODO: e.g. -b ${INVENTREE_WEB_ADDR}:${INVENTREE_WEB_PORT} fails here
CMD gunicorn -c ./gunicorn.conf.py InvenTree.wsgi -b 0.0.0.0:8000 --chdir ./InvenTree

FROM base as dev

# The development image requires the source code to be mounted to /home/inventree/
# So from here, we don't actually "do" anything, apart from some file management

ENV INVENTREE_DEBUG=True

ENV INVENTREE_DEV_DIR="${INVENTREE_HOME}/dev"

# Location for python virtual environment
# If the INVENTREE_PY_ENV variable is set, the entrypoint script will use it!
ENV INVENTREE_PY_ENV="${INVENTREE_DEV_DIR}/env"

# Override default path settings
ENV INVENTREE_STATIC_ROOT="${INVENTREE_DEV_DIR}/static"
ENV INVENTREE_MEDIA_ROOT="${INVENTREE_DEV_DIR}/media"
ENV INVENTREE_PLUGIN_DIR="${INVENTREE_DEV_DIR}/plugins"

ENV INVENTREE_CONFIG_FILE="${INVENTREE_DEV_DIR}/config.yaml"
ENV INVENTREE_SECRET_KEY_FILE="${INVENTREE_DEV_DIR}/secret_key.txt"
ENV INVENTREE_PLUGIN_FILE="${INVENTREE_DEV_DIR}/plugins.txt"

WORKDIR ${INVENTREE_HOME}

# Entrypoint ensures that we are running in the python virtual environment
ENTRYPOINT ["/bin/bash", "./docker/init.sh"]

# Launch the development server
CMD ["invoke", "server", "-a", "${INVENTREE_WEB_ADDR}:${INVENTREE_WEB_PORT}"]
