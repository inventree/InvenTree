# Dockerfile for the InvenTree devcontainer

# In contrast with the "production" image (which is based on an Alpine image)
# we use a Debian-based image for the devcontainer

FROM mcr.microsoft.com/devcontainers/python:3.13-bookworm@sha256:11690b54090a0a649321728d5f278288b3bab1b45c37218a715ee63f5716e546

# InvenTree paths
ENV INVENTREE_HOME="/home/inventree"
ENV INVENTREE_DATA_DIR="${INVENTREE_HOME}/dev"
ENV INVENTREE_STATIC_ROOT="${INVENTREE_DATA_DIR}/static"
ENV INVENTREE_MEDIA_ROOT="${INVENTREE_DATA_DIR}/media"
ENV INVENTREE_BACKUP_DIR="${INVENTREE_DATA_DIR}/backup"
ENV INVENTREE_PLUGIN_DIR="${INVENTREE_DATA_DIR}/plugins"
ENV INVENTREE_CONFIG_FILE="${INVENTREE_DATA_DIR}/config.yaml"

# Required for running playwright within devcontainer
ENV DISPLAY=:0
ENV LIBGL_ALWAYS_INDIRECT=1

COPY contrib/container/init.sh ./
RUN chmod +x init.sh

# Install required base packages
RUN apt update && apt install -y \
   python3.11-dev python3.11-venv \
   postgresql-client \
   libldap2-dev libsasl2-dev \
   libpango1.0-0 libcairo2 \
   poppler-utils weasyprint

# Install packages required for frontend development
RUN apt install -y \
   yarn nodejs npm

RUN yarn config set network-timeout 600000 -g

ENTRYPOINT ["/bin/bash", "./init.sh"]
