# Dockerfile for the InvenTree devcontainer

# In contrast with the "production" image (which is based on an Alpine image)
# we use a Debian-based image for the devcontainer

FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

# InvenTree paths
ENV INVENTREE_HOME="/home/inventree"
ENV INVENTREE_DATA_DIR="${INVENTREE_HOME}/dev"
ENV INVENTREE_STATIC_ROOT="${INVENTREE_DATA_DIR}/static"
ENV INVENTREE_MEDIA_ROOT="${INVENTREE_DATA_DIR}/media"
ENV INVENTREE_BACKUP_DIR="${INVENTREE_DATA_DIR}/backup"
ENV INVENTREE_PLUGIN_DIR="${INVENTREE_DATA_DIR}/plugins"

ENV INVENTREE_DOCKER="true"

COPY contrib/container/init.sh ./
RUN chmod +x init.sh

# Install required base packages
RUN apt update && apt install -y \
   python3.11-dev python3.11-venv \
   postgresql-client \
   libldap2-dev libsasl2-dev \
   libpango1.0-0 libcairo2 \
   weasyprint

# Install python database connectors

ENTRYPOINT ["/bin/bash", "./init.sh"]
