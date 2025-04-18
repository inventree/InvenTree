#!/bin/ash

# Install system packages required for building InvenTree python libraries

apk add gcc g++ musl-dev openssl-dev libffi-dev cargo python3-dev openldap-dev \
    libstdc++ build-base linux-headers py3-grpcio \
    jpeg-dev openjpeg-dev libwebp-dev zlib-dev \
    sqlite sqlite-dev \
    mariadb-connector-c-dev mariadb-client mariadb-dev \
    postgresql16-dev postgresql-libs \
    $@
