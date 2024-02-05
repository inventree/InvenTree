#!/bin/ash

# Install system packages required for building InvenTree python libraries
# Note that for postgreslql, we use the 13 version, which matches the version used in the InvenTree docker image

apk add gcc g++ musl-dev openssl-dev libffi-dev cargo python3-dev openldap-dev \
    jpeg-dev openjpeg-dev libwebp-dev zlib-dev \
    sqlite sqlite-dev \
    mariadb-connector-c-dev mariadb-client maridb-dev \
    postgresql13-dev postgresql-libs postgresql13-client \
    $@
