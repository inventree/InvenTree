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

ARG base_image=python:3.10-alpine3.18
FROM ${base_image} as inventree_base

# Build arguments for this image
ARG commit_hash=""
ARG commit_date=""
ARG commit_tag=""

ENV PYTHONUNBUFFERED 1
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV INVOKE_RUN_SHELL="/bin/ash"

ENV INVENTREE_LOG_LEVEL="WARNING"
ENV INVENTREE_DOCKER="true"

# InvenTree paths
ENV INVENTREE_HOME="/home/inventree"
ENV INVENTREE_MNG_DIR="${INVENTREE_HOME}/InvenTree"
ENV INVENTREE_DATA_DIR="${INVENTREE_HOME}/data"
ENV INVENTREE_STATIC_ROOT="${INVENTREE_DATA_DIR}/static"
ENV INVENTREE_MEDIA_ROOT="${INVENTREE_DATA_DIR}/media"
ENV INVENTREE_BACKUP_DIR="${INVENTREE_DATA_DIR}/backup"
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
      org.label-schema.vcs-url="https://github.com/inventree/InvenTree.git" \
      org.label-schema.vcs-ref=${commit_tag}

# Install required system level packages
RUN apk add --no-cache \
    git gettext py-cryptography \
    # Image format support
    libjpeg libwebp zlib \
    # Weasyprint requirements : https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#alpine-3-12
    py3-pip py3-pillow py3-cffi py3-brotli pango poppler-utils openldap \
    # SQLite support
    sqlite \
    # PostgreSQL support
    postgresql-libs postgresql-client \
    # MySQL / MariaDB support
    mariadb-connector-c-dev mariadb-client && \
    # fonts
    apk --update --upgrade --no-cache add fontconfig ttf-freefont font-noto terminus-font && fc-cache -f

EXPOSE 8000

RUN mkdir -p ${INVENTREE_HOME}
WORKDIR ${INVENTREE_HOME}

COPY ./docker/requirements.txt base_requirements.txt
COPY ./requirements.txt ./
COPY ./docker/install_build_packages.sh .
RUN chmod +x install_build_packages.sh

# For ARMv7 architecture, add the piwheels repo (for cryptography library)
# Otherwise, we have to build from source, which is difficult
# Ref: https://github.com/inventree/InvenTree/pull/4598
RUN if [ `apk --print-arch` = "armv7" ]; then \
    printf "[global]\nextra-index-url=https://www.piwheels.org/simple\n" > /etc/pip.conf ; \
    fi

COPY tasks.py docker/gunicorn.conf.py docker/init.sh ./
RUN chmod +x init.sh

ENTRYPOINT ["/bin/sh", "./init.sh"]

FROM inventree_base as prebuild

RUN ./install_build_packages.sh --no-cache --virtual .build-deps && \
    pip install -r base_requirements.txt -r requirements.txt --no-cache-dir && \
    apk --purge del .build-deps

# Frontend builder image:
FROM prebuild as frontend

RUN apk add --no-cache --update nodejs npm && npm install -g yarn
RUN yarn config set network-timeout 600000 -g
COPY InvenTree ${INVENTREE_HOME}/InvenTree
COPY src ${INVENTREE_HOME}/src
COPY tasks.py ${INVENTREE_HOME}/tasks.py
RUN cd ${INVENTREE_HOME}/InvenTree && inv frontend-compile

# InvenTree production image:
# - Copies required files from local directory
# - Starts a gunicorn webserver
FROM prebuild as production

ENV INVENTREE_DEBUG=False

# As .git directory is not available in production image, we pass the commit information via ENV
ENV INVENTREE_COMMIT_HASH="${commit_hash}"
ENV INVENTREE_COMMIT_DATE="${commit_date}"

# Copy source code
COPY InvenTree ./InvenTree
COPY --from=frontend ${INVENTREE_HOME}/InvenTree/web/static/web ./InvenTree/web/static/web

# Launch the production server
# TODO: Work out why environment variables cannot be interpolated in this command
# TODO: e.g. -b ${INVENTREE_WEB_ADDR}:${INVENTREE_WEB_PORT} fails here
CMD gunicorn -c ./gunicorn.conf.py InvenTree.wsgi -b 0.0.0.0:8000 --chdir ./InvenTree

FROM inventree_base as dev

# Vite server (for local frontend development)
EXPOSE 5173

# Install packages required for building python packages
RUN ./install_build_packages.sh

RUN pip install -r base_requirements.txt --no-cache-dir

# Install nodejs / npm / yarn

RUN apk add --no-cache --update nodejs npm && npm install -g yarn
RUN yarn config set network-timeout 600000 -g

# The development image requires the source code to be mounted to /home/inventree/
# So from here, we don't actually "do" anything, apart from some file management

ENV INVENTREE_DEBUG=True

# Location for python virtual environment
# If the INVENTREE_PY_ENV variable is set, the entrypoint script will use it!
ENV INVENTREE_PY_ENV="${INVENTREE_DATA_DIR}/env"

WORKDIR ${INVENTREE_HOME}

# Entrypoint ensures that we are running in the python virtual environment
ENTRYPOINT ["/bin/ash", "./docker/init.sh"]

# Launch the development server
CMD ["invoke", "server", "-a", "${INVENTREE_WEB_ADDR}:${INVENTREE_WEB_PORT}"]

# Image target for devcontainer
FROM dev as devcontainer

ARG workspace="/workspaces/InvenTree"

WORKDIR ${WORKSPACE}
