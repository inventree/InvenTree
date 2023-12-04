#!/bin/ash

# Install system packages required for building InvenTree python libraries

apk add --no-cache \
    gcc g++ musl-dev openssl-dev libffi-dev cargo python3-dev openldap-dev \
    jpeg-dev openjpeg-dev libwebp-dev zlib-dev \
    postgresql-dev sqlite-dev mariadb-dev \
    $@
