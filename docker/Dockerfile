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

# Default web server port is 8000
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
RUN apk add --no-cache tini \
    git make bash \
    gcc libgcc g++ libstdc++ \
    libjpeg-turbo libjpeg-turbo-dev jpeg jpeg-dev \
    libffi libffi-dev \
    zlib zlib-dev \
    # Cairo deps for WeasyPrint (these will be deprecated once WeasyPrint drops cairo requirement) 
    cairo cairo-dev pango pango-dev \
    #fonts
    fontconfig ttf-droid ttf-liberation ttf-dejavu ttf-opensans ttf-ubuntu-font-family font-croscore font-noto \
    # Python
    python3 python3-dev py3-pip \
    # SQLite support
    sqlite \
    # Postgres support
    postgresql postgresql-contrib postgresql-dev libpq \
    # MySQL/Mariadb support
    mariadb-connector-c mariadb-dev mariadb-client

ENTRYPOINT ["/sbin/tini", "--"]

 
FROM base as production
# Clone source code
RUN echo "Downloading InvenTree from ${INVENTREE_GIT_REPO}" \
  &&  git clone --branch ${INVENTREE_GIT_BRANCH} --depth 1 ${INVENTREE_GIT_REPO} ${INVENTREE_HOME}

# Checkout against a particular git tag
RUN if [ -n "${INVENTREE_GIT_TAG}" ] ; then cd ${INVENTREE_HOME} && git fetch --all --tags && git checkout tags/${INVENTREE_GIT_TAG} -b v${INVENTREE_GIT_TAG}-branch ; fi
RUN chown -R inventree:inventreegroup ${INVENTREE_HOME}/*

WORKDIR ${INVENTREE_HOME}
#temporary entrypoint copy test. Can be removed after merge
RUN if test -f docker/init-server.sh; then \
	cp docker/init-server.sh /init-server.sh; \
	cp docker/init-worker.sh /init-worker.sh; \
    cp docker/wait-for-it.sh /wait-for-it.sh; \
	fi;

# Install InvenTree packages
RUN pip3 install --no-cache-dir --disable-pip-version-check pip==21.2.3 setuptools==57.4.0 wheel>=0.37.0 \
 && pip3 install --no-cache-dir --disable-pip-version-check -r ${INVENTREE_HOME}/requirements.txt

#Drop to the inventree user
USER inventree

# Example production command
CMD ["gunicorn -c ./docker/gunicorn.conf.py -b 0.0.0.0:8000 InvenTree.wsgi"]
 

FROM production as local

# This development image is to avoid a locally produced virtualenv and is to produce an 'as close'
# to prod environment as possible. 
# This image adds the local repository owned as the inventree user. To run a live-restarting variant
# simply mount the code directory (as per the dev image) and add `--user root`

USER root
ADD --chown=inventree:inventreegroup requirements.txt ${INVENTREE_HOME}/requirements.txt
RUN pip3 install --no-cache-dir --disable-pip-version-check -r ${INVENTREE_HOME}/requirements.txt
USER inventree

ADD --chown=inventree:inventreegroup . ${INVENTREE_HOME}/
#replace the entrypoints in case they have changed
COPY ./docker/init-server.sh ./docker/init-worker.sh ./docker/wait-for-it.sh /


FROM local as dev

# The development image requires the source code to be mounted to /home/inventree/
# So from here, we don't actually "do" anything, apart from some file management

ENV INVENTREE_DEV_DIR = "${INVENTREE_HOME}/dev"

# Override default path settings
ENV INVENTREE_STATIC_ROOT="${INVENTREE_DEV_DIR}/static"
ENV INVENTREE_MEDIA_ROOT="${INVENTREE_DEV_DIR}/media"
ENV INVENTREE_CONFIG_FILE="${INVENTREE_DEV_DIR}/config.yaml"
ENV INVENTREE_SECRET_KEY_FILE="${INVENTREE_DEV_DIR}/secret_key.txt"

WORKDIR ${INVENTREE_HOME}

# Launch the development server
CMD ["python3 manage.py runserver 0.0.0.0:8000"]

