FROM python:alpine as production

# GitHub source
ARG INVENTREE_REPO="https://github.com/inventree/InvenTree.git"
ARG INVENTREE_VERSION="master"

# InvenTree server port
ARG INVENTREE_PORT="80"

# Database configuration options
ARG INVENTREE_DB_ENGINE="sqlite"
ARG INVENTREE_DB_NAME="inventree_db.sqlite3"
ARG INVENTREE_DB_HOST="127.0.0.1"
ARG INVENTREE_DB_PORT=""
ARG INVENTREE_DB_USER=""
ARG INVENTREE_DB_PASSWORD=""

ENV PYTHONUNBUFFERED 1

# InvenTree key settings
ENV INVENTREE_HOME="/home/inventree"
ENV INVENTREE_PORT="${INVENTREE_PORT}"

# InvenTree paths
ENV INVENTREE_SRC_DIR="${INVENTREE_HOME}/src"
ENV INVENTREE_STATIC_ROOT="${INVENTREE_HOME}/static"
ENV INVENTREE_MEDIA_ROOT="${INVENTREE_HOME}/media"
ENV INVENTREE_LOG_DIR="${INVENTREE_HOME}/log"
ENV INVENTREE_BACKUP_DIR="${INVENTREE_HOME}/backup"
ENV INVENTREE_VENV="${INVENTREE_HOME}/env"

# Pass DB configuration through as environment variables
ENV INVENTREE_DB_ENGINE="${INVENTREE_DB_ENGINE}"
ENV INVENTREE_DB_NAME="${INVENTREE_DB_NAME}"
ENV INVENTREE_DB_HOST="${INVENTREE_DB_HOST}"
ENV INVENTREE_DB_PORT="${INVENTREE_DB_PORT}"
ENV INVENTREE_DB_USER="${INVENTREE_DB_USER}"
ENV INVENTREE_DB_PASSWORD="${INVENTREE_DB_PASSWORD}"

LABEL org.label-schema.schema-version="1.0" \
      org.label-schema.build-date=${DATE} \
      org.label-schema.vendor="inventree" \
      org.label-schema.name="inventree/inventree" \
      org.label-schema.url="https://hub.docker.com/r/inventree/inventree-docker" \
      org.label-schema.version=${INVENTREE_VERSION} \
      org.label-schema.vcs-url=${INVENTREE_REPO} \
      org.label-schema.vcs-branch=${BRANCH} \
      org.label-schema.vcs-ref=${COMMIT}

RUN echo "Installing InvenTree '${INVENTREE_VERSION}' from ${INVENTREE_REPO}"

# Create user account
RUN addgroup -S inventreegroup && adduser -S inventree -G inventreegroup
WORKDIR ${INVENTREE_HOME}

# Install required system packages
RUN apk add --no-cache git make bash \
    gcc libgcc g++ libstdc++ \
    libjpeg-turbo libjpeg-turbo-dev jpeg jpeg-dev \
    libffi libffi-dev \
    zlib zlib-dev
RUN apk add --no-cache cairo cairo-dev pango pango-dev
RUN apk add --no-cache fontconfig ttf-droid ttf-liberation ttf-dejavu ttf-opensans ttf-ubuntu-font-family font-croscore font-noto
RUN apk add --no-cache python3
RUN apk add --no-cache postgresql-contrib postgresql-dev libpq
RUN apk add --no-cache mariadb-connector-c mariadb-dev

# Clone source code
RUN git clone --branch ${INVENTREE_VERSION} --depth 1 ${INVENTREE_REPO} ${INVENTREE_SRC_DIR}

# Setup Python virtual environment
RUN python3 -m venv ${INVENTREE_VENV}

# Install required PIP packages (into the virtual environment!)
RUN source ${INVENTREE_VENV}/bin/activate && pip install --upgrade pip setuptools wheel
RUN source ${INVENTREE_VENV}/bin/activate && pip install --no-cache-dir -U invoke
RUN source ${INVENTREE_VENV}/bin/activate && pip install --no-cache-dir -U psycopg2 mysqlclient pgcli mariadb
RUN source ${INVENTREE_VENV}/bin/activate && pip install --no-cache-dir -U gunicorn

# Install InvenTree packages
RUN source ${INVENTREE_VENV}/bin/activate && pip install --no-cache-dir -U -r ${INVENTREE_SRC_DIR}/requirements.txt

# Install supervisor
RUN apk add --no-cache supervisor

# Create required directories
RUN mkdir ${INVENTREE_HOME}/media ${INVENTREE_HOME}/static ${INVENTREE_HOME}/backup

# Copy supervisor file
COPY docker/supervisor.conf /etc/supervisord.conf

# Copy gunicorn config file
COPY docker/gunicorn.conf.py ${INVENTREE_HOME}/gunicorn.conf.py

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
