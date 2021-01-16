FROM python:alpine AS production

ARG VERSION=master
RUN echo installing $VERSION of inventree

ENV PYTHONUNBUFFERED 1
ENV INVENTREE_ROOT="/usr/src/app"
ENV INVENTREE_HOME="$INVENTREE_ROOT/InvenTree"
ENV INVENTREE_DOCKER_RUN_PATH="$INVENTREE_HOME/docker"
ENV INVENTREE_STATIC="/usr/src/static"
ENV INVENTREE_MEDIA="/usr/src/media"
ENV VIRTUAL_ENV="/opt/venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH:$INVENTREE_DOCKER_RUN_PATH"
ENV INVENTREE_REPO="https://github.com/inventree/InvenTree.git"

RUN echo "Installing ${VERSION} of inventree from ${INVENTREE_REPO}"

RUN apk add --no-cache gcc libgcc g++ libstdc++ postgresql-contrib postgresql-dev libjpeg-turbo zlib jpeg libffi \
    zlib-dev cairo pango gdk-pixbuf musl libpq fontconfig libjpeg-turbo-dev zlib-dev jpeg-dev libffi-dev cairo-dev \
    pango-dev gdk-pixbuf-dev musl-dev ttf-dejavu ttf-opensans ttf-ubuntu-font-family font-croscore font-noto \
    ttf-droid ttf-liberation msttcorefonts-installer git make bash python3 ttf-dejavu ttf-opensans \
    ttf-ubuntu-font-family font-croscore font-noto ttf-droid ttf-liberation msttcorefonts-installer sqlite \
    mariadb-dev mariadb-connector-c

RUN update-ms-fonts
RUN fc-cache -fv

RUN python -m venv $VIRTUAL_ENV && pip install --upgrade pip setuptools wheel
RUN python -m venv $VIRTUAL_ENV && pip install --no-cache-dir -U gunicorn psycopg2 pgcli mariadb

RUN git clone --branch $VERSION --depth 1 ${INVENTREE_REPO} ${INVENTREE_ROOT}

RUN python -m venv $VIRTUAL_ENV && pip install --no-cache-dir -U -r /usr/src/app/requirements.txt

ENV DEV_FILE="False"
RUN if [ $DEV_FILE = True ] ; then pip install --no-cache-dir -U -r /usr/src/dev_requirements.txt; fi

RUN apk del --no-cache gcc g++ postgresql-dev libjpeg-turbo-dev zlib-dev jpeg-dev libffi-dev cairo-dev pango-dev \
    gdk-pixbuf-dev git make musl-dev mariadb-dev

RUN chmod 755 ${INVENTREE_DOCKER_RUN_PATH}/start_gunicorn.sh ${INVENTREE_DOCKER_RUN_PATH}/wait-for.sh

LABEL org.label-schema.schema-version="1.0" \
    org.label-schema.build-date=$DATE \
    org.label-schema.vendor="inventree" \
    org.label-schema.name="inventree/inventree" \
    org.label-schema.url="https://hub.docker.com/r/inventree/inventree-docker" \
    org.label-schema.version=$VERSION \
    org.label-schema.vcs-url=$URL \
    org.label-schema.vcs-branch=$BRANCH \
    org.label-schema.vcs-ref=$COMMIT

WORKDIR ${INVENTREE_HOME}
CMD ${INVENTREE_DOCKER_RUN_PATH}/start_gunicorn.sh
