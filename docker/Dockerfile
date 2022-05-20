FROM python:3.9-slim as base

# GitHub source
ARG repository="https://github.com/inventree/InvenTree.git"
ARG branch="master"

# Optionally specify a particular tag to checkout
ARG tag=""

ENV PYTHONUNBUFFERED 1

# Ref: https://github.com/pyca/cryptography/issues/5776
ENV CRYPTOGRAPHY_DONT_BUILD_RUST 1

# InvenTree key settings

# The INVENTREE_HOME directory is where the InvenTree source repository will be located
ENV INVENTREE_HOME="/home/inventree"

# GitHub settings
ENV INVENTREE_GIT_REPO="${repository}"
ENV INVENTREE_GIT_BRANCH="${branch}"
ENV INVENTREE_GIT_TAG="${tag}"

ENV INVENTREE_LOG_LEVEL="INFO"
ENV INVENTREE_DOCKER="true"

# InvenTree paths
ENV INVENTREE_MNG_DIR="${INVENTREE_HOME}/InvenTree"
ENV INVENTREE_DATA_DIR="${INVENTREE_HOME}/data"
ENV INVENTREE_STATIC_ROOT="${INVENTREE_DATA_DIR}/static"
ENV INVENTREE_MEDIA_ROOT="${INVENTREE_DATA_DIR}/media"
ENV INVENTREE_PLUGIN_DIR="${INVENTREE_DATA_DIR}/plugins"

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
      org.label-schema.vcs-url=${INVENTREE_GIT_REPO} \
      org.label-schema.vcs-branch=${INVENTREE_GIT_BRANCH} \
      org.label-schema.vcs-ref=${INVENTREE_GIT_TAG}

# Create user account and group
RUN adduser inventree
RUN addgroup inventreegroup
RUN usermod -aG inventreegroup inventree

# RUN apt-get upgrade && apt-get update
RUN apt-get update

# Install required system packages
RUN apt-get install -y \
    git build-essential \
    # Weasyprint requirements : https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#debian-11
    libpango-1.0-0 libpangoft2-1.0-0 \
    # Image format support
    libjpeg-dev webp libffi-dev \
    # SQLite support
    sqlite3 \
    # PostgreSQL support
    libpq-dev \
    # MySQL / MariaDB support
    default-libmysqlclient-dev mariadb-client

# Update pip
RUN pip install --upgrade pip

# Install required base-level python packages
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -U -r requirements.txt

# Production code (pulled from tagged github release)
FROM base as production

# Clone source code
RUN echo "Downloading InvenTree from ${INVENTREE_GIT_REPO}"

RUN git clone --branch ${INVENTREE_GIT_BRANCH} --depth 1 ${INVENTREE_GIT_REPO} ${INVENTREE_HOME}

# Ref: https://github.blog/2022-04-12-git-security-vulnerability-announced/
RUN git config --global --add safe.directory ${INVENTREE_HOME}

# Checkout against a particular git tag
RUN if [ -n "${INVENTREE_GIT_TAG}" ] ; then cd ${INVENTREE_HOME} && git fetch --all --tags && git checkout tags/${INVENTREE_GIT_TAG} -b v${INVENTREE_GIT_TAG}-branch ; fi

RUN chown -R inventree:inventreegroup ${INVENTREE_HOME}/*

# Drop to the inventree user
USER inventree

# Install InvenTree packages
RUN pip3 install --user --no-cache-dir --disable-pip-version-check -r ${INVENTREE_HOME}/requirements.txt

# Need to be running from within this directory
WORKDIR ${INVENTREE_MNG_DIR}

# Server init entrypoint
ENTRYPOINT ["/bin/bash", "../docker/init.sh"]

# Launch the production server
# TODO: Work out why environment variables cannot be interpolated in this command
# TODO: e.g. -b ${INVENTREE_WEB_ADDR}:${INVENTREE_WEB_PORT} fails here
CMD gunicorn -c ./docker/gunicorn.conf.py InvenTree.wsgi -b 0.0.0.0:8000 --chdir ./InvenTree

FROM base as dev

# The development image requires the source code to be mounted to /home/inventree/
# So from here, we don't actually "do" anything, apart from some file management

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
