FROM alpine:3.13 as base

# GitHub source
ARG repository="https://github.com/inventree/InvenTree.git"
ARG branch="master"

# Optionally specify a particular tag to checkout
ARG tag=""

ENV PYTHONUNBUFFERED 1

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

ENV INVENTREE_CONFIG_FILE="${INVENTREE_DATA_DIR}/config.yaml"
ENV INVENTREE_SECRET_KEY_FILE="${INVENTREE_DATA_DIR}/secret_key.txt"

# Worker configuration (can be altered by user)
ENV INVENTREE_GUNICORN_WORKERS="4"
ENV INVENTREE_BACKGROUND_WORKERS="4"

# Default web server address:port
ENV INVENTREE_WEB_ADDR="0.0.0.0"
ENV INVENTREE_WEB_PORT="8000"

LABEL org.label-schema.schema-version="1.0" \
      org.label-schema.build-date=${DATE} \
      org.label-schema.vendor="inventree" \
      org.label-schema.name="inventree/inventree" \
      org.label-schema.url="https://hub.docker.com/r/inventree/inventree" \
      org.label-schema.version=${INVENTREE_VERSION} \
      org.label-schema.vcs-url=${INVENTREE_REPO} \
      org.label-schema.vcs-branch=${BRANCH} \
      org.label-schema.vcs-ref=${COMMIT}

# Create user account
RUN addgroup -S inventreegroup && adduser -S inventree -G inventreegroup

WORKDIR ${INVENTREE_HOME}

# Install required system packages
RUN apk add --no-cache git make bash \
    gcc libgcc g++ libstdc++ \
    libjpeg-turbo libjpeg-turbo-dev jpeg jpeg-dev \
    libffi libffi-dev \
    zlib zlib-dev

# Cairo deps for WeasyPrint (these will be deprecated once WeasyPrint drops cairo requirement)
RUN apk add --no-cache cairo cairo-dev pango pango-dev
RUN apk add --no-cache fontconfig ttf-droid ttf-liberation ttf-dejavu ttf-opensans ttf-ubuntu-font-family font-croscore font-noto

# Python
RUN apk add --no-cache python3 python3-dev py3-pip

# SQLite support
RUN apk add --no-cache sqlite

# PostgreSQL support
RUN apk add --no-cache postgresql postgresql-contrib postgresql-dev libpq

# MySQL support
RUN apk add --no-cache mariadb-connector-c mariadb-dev mariadb-client

# Install required python packages
RUN pip install --no-cache-dir -U psycopg2 mysqlclient pgcli mariadb

FROM base as production
# Clone source code
RUN echo "Downloading InvenTree from ${INVENTREE_GIT_REPO}"

RUN git clone --branch ${INVENTREE_GIT_BRANCH} --depth 1 ${INVENTREE_GIT_REPO} ${INVENTREE_HOME}

# Checkout against a particular git tag
RUN if [ -n "${INVENTREE_GIT_TAG}" ] ; then cd ${INVENTREE_HOME} && git fetch --all --tags && git checkout tags/${INVENTREE_GIT_TAG} -b v${INVENTREE_GIT_TAG}-branch ; fi

# Install InvenTree packages
RUN pip install --no-cache-dir -U -r ${INVENTREE_HOME}/requirements.txt

# Copy gunicorn config file
COPY gunicorn.conf.py ${INVENTREE_HOME}/gunicorn.conf.py

# Copy startup scripts
COPY start_prod_server.sh ${INVENTREE_HOME}/start_prod_server.sh
COPY start_prod_worker.sh ${INVENTREE_HOME}/start_prod_worker.sh

RUN chmod 755 ${INVENTREE_HOME}/start_prod_server.sh
RUN chmod 755 ${INVENTREE_HOME}/start_prod_worker.sh

WORKDIR ${INVENTREE_HOME}

# Let us begin
CMD ["bash", "./start_prod_server.sh"]

FROM base as dev

# The development image requires the source code to be mounted to /home/inventree/
# So from here, we don't actually "do" anything, apart from some file management

ENV INVENTREE_DEV_DIR="${INVENTREE_HOME}/dev"

# Override default path settings
ENV INVENTREE_STATIC_ROOT="${INVENTREE_DEV_DIR}/static"
ENV INVENTREE_MEDIA_ROOT="${INVENTREE_DEV_DIR}/media"
ENV INVENTREE_CONFIG_FILE="${INVENTREE_DEV_DIR}/config.yaml"
ENV INVENTREE_SECRET_KEY_FILE="${INVENTREE_DEV_DIR}/secret_key.txt"

WORKDIR ${INVENTREE_HOME}

# Launch the development server
CMD ["bash", "/home/inventree/docker/start_dev_server.sh"]
