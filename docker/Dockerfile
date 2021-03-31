FROM python:alpine as production

# Configuration params
ARG INVENTREE_REPO="https://github.com/inventree/InvenTree.git"
ARG INVENTREE_VERSION="master"
ARG INVENTREE_HOME="/home/inventree"

ENV PYTHONUNBUFFERED 1

# InvenTree paths
ENV INVENTREE_SRC_DIR="$INVENTREE_HOME/src"
ENV INVENTREE_STATIC_ROOT="$INVENTREE_HOME/static"
ENV INVENTREE_MEDIA_ROOT="$INVENTREE_HOME/media"
ENV INVENTREE_LOG_DIR="$INVENTREE_HOME/log"
ENV INVENTREE_BACKUP_DIR="$INVENTREE_HOME/backup"
ENV INVENTREE_VENV="$INVENTREE_HOME/env"

RUN echo "Installing InvenTree '${INVENTREE_VERSION}' from ${INVENTREE_REPO}"

# Create user account
RUN addgroup -S inventreegroup && adduser -S inventree -G inventreegroup
WORKDIR /home/inventree

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
RUN git clone --branch $INVENTREE_VERSION --depth 1 ${INVENTREE_REPO} ${INVENTREE_SRC_DIR}

# Install required PIP packages
RUN python -m venv $INVENTREE_VENV && pip install --upgrade pip setuptools wheel
RUN python -m venv $INVENTREE_VENV && pip install --no-cache-dir -U invoke
RUN python -m venv $INVENTREE_VENV && pip install --no-cache-dir -U psycopg2 mysqlclient pgcli mariadb

# Install InvenTree packages
RUN python -m venv $INVENTREE_VENV && pip install --no-cache-dir -U -r $INVENTREE_SRC_DIR/requirements.txt

# Install supervisor
RUN apt add --no-cache supervisor

# Create required directories
RUN mkdir /home/inventree/media /home/inventree/static /home/inventree/log /home/inventree/backup

# Copy supervisor file
COPY deploy/inventree.conf /etc/supervisor/conf.d/inventree.conf

RUN sudo service supervisor start
