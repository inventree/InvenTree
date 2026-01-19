#!/bin/bash
#
# packager.io postinstall script functions
#
Color_Off='\033[0m'
On_Red='\033[41m'
PYTHON_FROM=11
PYTHON_TO=15

function detect_docker() {
  if [ -n "$(grep docker </proc/1/cgroup)" ]; then
    DOCKER="yes"
  else
    DOCKER="no"
  fi
  echo "# POI04| Running in docker: ${DOCKER}"
}

function detect_initcmd() {
  if [ -n "$(which systemctl 2>/dev/null)" ]; then
    INIT_CMD="systemctl"
  elif [ -n "$(which initctl 2>/dev/null)" ]; then
    INIT_CMD="initctl"
  else
    function sysvinit() {
      service $2 $1
    }
    INIT_CMD="sysvinit"
  fi

  if [ "${DOCKER}" == "yes" ]; then
    INIT_CMD="initctl"
  fi
  echo "# POI05| Using init command: ${INIT_CMD}"
}

function detect_ip() {
  # Get the IP address of the server

  if [ "${SETUP_NO_CALLS}" == "true" ]; then
    # Use local IP address
    echo "# POI06| Getting the IP address of the first local IP address"
    export INVENTREE_IP=$(hostname -I | awk '{print $1}')
  else
    # Use web service to get the IP address
    echo "# POI06| Getting the IP address of the server via web service"
    export INVENTREE_IP=$(curl -s https://checkip.amazonaws.com)
  fi

  echo "# POI06| IP address is ${INVENTREE_IP}"
}

function detect_python() {
  # Detect if there is already a python version installed in /opt/inventree/env/lib
  if test -f "${APP_HOME}/env/bin/python"; then
    echo "# POI07| Python environment already present"
    # Extract earliest python version initialised from /opt/inventree/env/lib
    SETUP_PYTHON=$(ls -1 ${APP_HOME}/env/bin/python* | sort | head -n 1)
    echo "# POI07| Found earlier used version: ${SETUP_PYTHON}"
  else
    echo "# POI07| No python environment found - using environment variable: ${SETUP_PYTHON}"
  fi

  # Try to detect a python between lowest and highest supported in reverse order
  if [ -z "$(which ${SETUP_PYTHON})" ]; then
    echo "# POI07| Trying to detecting python3.${PYTHON_FROM} to python3.${PYTHON_TO} - using newest version"
    for i in $(seq $PYTHON_TO -1 $PYTHON_FROM); do
      echo "# POI07| Checking for python3.${i}"
      if [ -n "$(which python3.${i})" ]; then
        SETUP_PYTHON="python3.${i}"
        echo "# POI07| Found python3.${i} installed - using for setup ${SETUP_PYTHON}"
        break
      fi
    done
  fi

  # Ensure python can be executed - abort if not
  if [ -z "$(which ${SETUP_PYTHON})" ]; then
    echo "${On_Red}"
    echo "# POI07| Python ${SETUP_PYTHON} not found - aborting!"
    echo "# POI07| Please ensure python can be executed with the command '$SETUP_PYTHON' by the current user '$USER'."
    echo "# POI07| If you are using a different python version, please set the environment variable SETUP_PYTHON to the correct command - eg. 'python3.11'."
    echo "${Color_Off}"
    exit 1
  fi

  echo "# POI07| Using python command: ${SETUP_PYTHON}"
}

function get_env() {
  envname=$1

  pid=$$
  while [ -z "${!envname}" -a $pid != 1 ]; do
      ppid=`ps -oppid -p$pid|tail -1|awk '{print $1}'`
      env=`strings /proc/$ppid/environ`
      export $envname=`echo "$env"|awk -F= '$1 == "'$envname'" { print $2; }'`
      pid=$ppid
  done

  if [ -n "${SETUP_DEBUG}" ]; then
    echo "# POI02| Done getting env $envname: ${!envname}"
  fi
}

function detect_local_env() {
  # Get all possible envs for the install

  if [ -n "${SETUP_DEBUG}" ]; then
    echo "# POI02| Printing local envs - before #++#"
    printenv
  fi

  for i in ${SETUP_ENVS//,/ }
  do
      get_env $i
  done

  if [ -n "${SETUP_DEBUG}" ]; then
    echo "# POI02| Printing local envs - after #++#"
    printenv
  fi

  # Print branch and dir from VERSION file
  if [ -f "${APP_HOME}/VERSION" ]; then
    echo "# POI02| Loading environment variables from VERSION file"
    content=$(cat "${APP_HOME}/VERSION")
    # use grep to get the branch and target
    INVENTREE_PKG_BRANCH=($(echo $content | grep -oP 'INVENTREE_PKG_BRANCH=\K[^ ]+'))
    INVENTREE_PKG_TARGET=($(echo $content | grep -oP 'INVENTREE_PKG_TARGET=\K[^ ]+'))
    echo "Running in a package environment build on branch $INVENTREE_PKG_BRANCH for target $INVENTREE_PKG_TARGET"
  else
    echo "# POI02| VERSION file not found"
  fi
}

function detect_envs() {
  # Detect all envs that should be passed to setup commands

  echo "# POI03| Setting base environment variables"

  export INVENTREE_CONFIG_FILE=${INVENTREE_CONFIG_FILE:-${CONF_DIR}/config.yaml}

  if test -f "${INVENTREE_CONFIG_FILE}"; then
    echo "# POI03| Using existing config file: ${INVENTREE_CONFIG_FILE}"

    # Install parser
    echo "# POI03| Installing requirements"
    pip install --require-hashes -r ${APP_HOME}/contrib/dev_reqs/requirements.txt -q
    echo "# POI03| Installed requirements"

    # Load config
    export INVENTREE_CONF_DATA=$(cat ${INVENTREE_CONFIG_FILE} | jc --yaml)

    # Parse the config file
    export INVENTREE_MEDIA_ROOT=$(jq -r '.[].media_root' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_STATIC_ROOT=$(jq -r '.[].static_root' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_BACKUP_DIR=$(jq -r '.[].backup_dir' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_PLUGINS_ENABLED=$(jq -r '.[].plugins_enabled' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_PLUGIN_FILE=$(jq -r '.[].plugin_file' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_SECRET_KEY_FILE=$(jq -r '.[].secret_key_file' <<< ${INVENTREE_CONF_DATA})

    export INVENTREE_DB_ENGINE=$(jq -r '.[].database.ENGINE' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_DB_NAME=$(jq -r '.[].database.NAME' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_DB_USER=$(jq -r '.[].database.USER' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_DB_PASSWORD=$(jq -r '.[].database.PASSWORD' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_DB_HOST=$(jq -r '.[].database.HOST' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_DB_PORT=$(jq -r '.[].database.PORT' <<< ${INVENTREE_CONF_DATA})

    # Parse site URL if not already set
    if [ -z "${INVENTREE_SITE_URL}" ]; then
      # Try to read out the app config
      if [ -n "$(inventree config:get INVENTREE_SITE_URL)" ]; then
        echo "# POI03| Getting site URL from app config"
        export INVENTREE_SITE_URL=$(inventree config:get INVENTREE_SITE_URL)
      else
        echo "# POI03| Getting site URL from config file"
        export INVENTREE_SITE_URL=$(jq -r '.[].site_url' <<< ${INVENTREE_CONF_DATA})
      fi
    fi
  else
    echo "# POI03| No config file found: ${INVENTREE_CONFIG_FILE}, using envs or defaults"

    if [ -n "${SETUP_DEBUG}" ]; then
      echo "# POI03| Print current envs"
      printenv | grep INVENTREE_
      printenv | grep SETUP_
    fi

    export INVENTREE_MEDIA_ROOT=${INVENTREE_MEDIA_ROOT:-${DATA_DIR}/media}
    export INVENTREE_STATIC_ROOT=${DATA_DIR}/static
    export INVENTREE_BACKUP_DIR=${DATA_DIR}/backup
    export INVENTREE_PLUGINS_ENABLED=true
    export INVENTREE_PLUGIN_FILE=${CONF_DIR}/plugins.txt
    export INVENTREE_SECRET_KEY_FILE=${CONF_DIR}/secret_key.txt
    export INVENTREE_OIDC_PRIVATE_KEY_FILE=${CONF_DIR}/oidc.pem

    export INVENTREE_DB_ENGINE=${INVENTREE_DB_ENGINE:-sqlite3}
    export INVENTREE_DB_NAME=${INVENTREE_DB_NAME:-${DATA_DIR}/database.sqlite3}
    export INVENTREE_DB_USER=${INVENTREE_DB_USER:-sampleuser}
    export INVENTREE_DB_PASSWORD=${INVENTREE_DB_PASSWORD:-samplepassword}
    export INVENTREE_DB_HOST=${INVENTREE_DB_HOST:-samplehost}
    export INVENTREE_DB_PORT=${INVENTREE_DB_PORT:-123456}

    export INVENTREE_SITE_URL=${INVENTREE_SITE_URL:-http://${INVENTREE_IP}}

    export SETUP_CONF_LOADED=true
  fi

  # For debugging pass out the envs
  echo "# POI03| Collected environment variables:"
  echo "# POI03|    INVENTREE_MEDIA_ROOT=${INVENTREE_MEDIA_ROOT}"
  echo "# POI03|    INVENTREE_STATIC_ROOT=${INVENTREE_STATIC_ROOT}"
  echo "# POI03|    INVENTREE_BACKUP_DIR=${INVENTREE_BACKUP_DIR}"
  echo "# POI03|    INVENTREE_PLUGINS_ENABLED=${INVENTREE_PLUGINS_ENABLED}"
  echo "# POI03|    INVENTREE_PLUGIN_FILE=${INVENTREE_PLUGIN_FILE}"
  echo "# POI03|    INVENTREE_SECRET_KEY_FILE=${INVENTREE_SECRET_KEY_FILE}"
  echo "# POI03|    INVENTREE_DB_ENGINE=${INVENTREE_DB_ENGINE}"
  echo "# POI03|    INVENTREE_DB_NAME=${INVENTREE_DB_NAME}"
  echo "# POI03|    INVENTREE_DB_USER=${INVENTREE_DB_USER}"
  if [ -n "${SETUP_DEBUG}" ]; then
    echo "# POI03|    INVENTREE_DB_PASSWORD=${INVENTREE_DB_PASSWORD}"
  fi
  echo "# POI03|    INVENTREE_DB_HOST=${INVENTREE_DB_HOST}"
  echo "# POI03|    INVENTREE_DB_PORT=${INVENTREE_DB_PORT}"
  echo "# POI03|    INVENTREE_SITE_URL=${INVENTREE_SITE_URL}"
}

function create_initscripts() {

  # Make sure python env exists
  if test -f "${APP_HOME}/env"; then
    echo "# POI09| python environment already present - skipping"
  else
    echo "# POI09| Setting up python environment"
    sudo -u ${APP_USER} --preserve-env=$SETUP_ENVS bash -c "cd ${APP_HOME} && ${SETUP_PYTHON} -m venv env"
    sudo -u ${APP_USER} --preserve-env=$SETUP_ENVS bash -c "cd ${APP_HOME} && env/bin/pip install invoke wheel"

    # Check INSTALLER_EXTRA exists and load it
    if test -f "${APP_HOME}/INSTALLER_EXTRA"; then
      echo "# POI09| Loading extra packages from INSTALLER_EXTRA"
      source ${APP_HOME}/INSTALLER_EXTRA
    fi

    if [ -n "${SETUP_EXTRA_PIP}" ]; then
      echo "# POI09| Installing extra pip packages"
      if [ -n "${SETUP_DEBUG}" ]; then
        echo "# POI09| Extra pip packages: ${SETUP_EXTRA_PIP}"
      fi
      sudo -u ${APP_USER} --preserve-env=$SETUP_ENVS bash -c "cd ${APP_HOME} && env/bin/pip install ${SETUP_EXTRA_PIP}"
      # Write extra packages to INSTALLER_EXTRA
      echo "SETUP_EXTRA_PIP='${SETUP_EXTRA_PIP}'" >>${APP_HOME}/INSTALLER_EXTRA
    fi
  fi

  # Unlink default config if it exists
  if test -f "/etc/nginx/sites-enabled/default"; then
    echo "# POI09| Unlinking default nginx config\n# POI09| Old file still in /etc/nginx/sites-available/default"
    sudo unlink /etc/nginx/sites-enabled/default
    echo "# POI09| Unlinked default nginx config"
  fi

  # Create InvenTree specific nginx config
  echo "# POI09| Stopping nginx"
  ${INIT_CMD} stop nginx
  echo "# POI09| Stopped nginx"
  echo "# POI09| Setting up nginx to ${SETUP_NGINX_FILE}"
  # Always use the latest nginx config; important if new headers are added / needed for security
  cp ${APP_HOME}/contrib/packager.io/nginx.prod.conf ${SETUP_NGINX_FILE}
  sed -i s/inventree-server:8000/localhost:6000/g ${SETUP_NGINX_FILE}
  sed -i s=var/www=opt/inventree/data=g ${SETUP_NGINX_FILE}
  # Start nginx
  echo "# POI09| Starting nginx"
  ${INIT_CMD} start nginx
  echo "# POI09| Started nginx"

  echo "# POI09| (Re)creating init scripts"
  # This resets scale parameters to a known state
  inventree scale web="1" worker="1"

  echo "# POI09| Enabling InvenTree on boot"
  ${INIT_CMD} enable inventree
  echo "# POI09| Enabled InvenTree on boot"
}

function create_admin() {
  # Create data for admin users - stop with setting SETUP_ADMIN_NOCREATION to true
  if [ "${SETUP_ADMIN_NOCREATION}" == "true" ]; then
    echo "# POI10| Admin creation is disabled - skipping"
    return
  fi

  if test -f "${SETUP_ADMIN_PASSWORD_FILE}"; then
    echo "# POI10| Admin data already exists - skipping"
  else
    echo "# POI10| Creating admin user data"

    # Static admin data
    export INVENTREE_ADMIN_USER=${INVENTREE_ADMIN_USER:-admin}
    export INVENTREE_ADMIN_EMAIL=${INVENTREE_ADMIN_EMAIL:-admin@example.com}

    # Create password if not set
    if [ -z "${INVENTREE_ADMIN_PASSWORD}" ]; then
      openssl rand -base64 32 >${SETUP_ADMIN_PASSWORD_FILE}
      export INVENTREE_ADMIN_PASSWORD=$(cat ${SETUP_ADMIN_PASSWORD_FILE})
    fi
  fi
}

function start_inventree() {
  echo "# POI15| Starting InvenTree"
  ${INIT_CMD} start inventree
  echo "# POI15| Started InvenTree"
}

function stop_inventree() {
  echo "# POI11| Stopping InvenTree"
  ${INIT_CMD} stop inventree
  echo "# POI11| Stopped InvenTree"
}

function update_or_install() {
  set -e

  # Set permissions so app user can write there
  chown ${APP_USER}:${APP_GROUP} ${APP_HOME} -R

  # Run update as app user
  echo "# POI12| Updating InvenTree"
  sudo -u ${APP_USER} --preserve-env=$SETUP_ENVS bash -c "cd ${APP_HOME} && pip install wheel python-dotenv"
  sudo -u ${APP_USER} --preserve-env=$SETUP_ENVS bash -c "cd ${APP_HOME} && set -e && invoke update | sed -e 's/^/# POI12| u | /;'"

  # Make sure permissions are correct again
  echo "# POI12| Set permissions for data dir and media: ${DATA_DIR}"
  chown ${APP_USER}:${APP_GROUP} ${DATA_DIR} -R
  chown ${APP_USER}:${APP_GROUP} ${CONF_DIR} -R
}

function set_env() {
  echo "# POI13| Setting up InvenTree config values"

  inventree config:set INVENTREE_CONFIG_FILE=${INVENTREE_CONFIG_FILE}

  # Changing the config file
  echo "# POI13| Writing the settings to the config file ${INVENTREE_CONFIG_FILE}"
  # Media Root
  sed -i s=#media_root:\ \'/home/inventree/data/media\'=media_root:\ \'${INVENTREE_MEDIA_ROOT}\'=g ${INVENTREE_CONFIG_FILE}
  # Static Root
  sed -i s=#static_root:\ \'/home/inventree/data/static\'=static_root:\ \'${INVENTREE_STATIC_ROOT}\'=g ${INVENTREE_CONFIG_FILE}
  # Backup dir
  sed -i s=#backup_dir:\ \'/home/inventree/data/backup\'=backup_dir:\ \'${INVENTREE_BACKUP_DIR}\'=g ${INVENTREE_CONFIG_FILE}
  # Plugins enabled
  sed -i s=plugins_enabled:\ False=plugins_enabled:\ ${INVENTREE_PLUGINS_ENABLED}=g ${INVENTREE_CONFIG_FILE}
  # Plugin file
  sed -i s=#plugin_file:\ \'/path/to/plugins.txt\'=plugin_file:\ \'${INVENTREE_PLUGIN_FILE}\'=g ${INVENTREE_CONFIG_FILE}
  # Secret key file
  sed -i s=#secret_key_file:\ \'/etc/inventree/secret_key.txt\'=secret_key_file:\ \'${INVENTREE_SECRET_KEY_FILE}\'=g ${INVENTREE_CONFIG_FILE}
  # OIDC private key file
  sed -i s=#oidc_private_key_file:\ \'/etc/inventree/oidc.pem\'=oidc_private_key_file:\ \'${INVENTREE_OIDC_PRIVATE_KEY_FILE}\'=g ${INVENTREE_CONFIG_FILE}
  # Debug mode
  sed -i s=debug:\ True=debug:\ False=g ${INVENTREE_CONFIG_FILE}

  # Database engine
  sed -i s=#\ ENGINE:\ Database\ engine.\ Selection\ from:=ENGINE:\ ${INVENTREE_DB_ENGINE}=g ${INVENTREE_CONFIG_FILE}
  # Database name
  sed -i s=#\ NAME:\ Database\ name=NAME:\ \'${INVENTREE_DB_NAME}\'=g ${INVENTREE_CONFIG_FILE}
  # Database user
  sed -i s=#\ USER:\ Database\ username\ \(if\ required\)=USER:\ ${INVENTREE_DB_USER}=g ${INVENTREE_CONFIG_FILE}
  # Database password
  sed -i s=#\ PASSWORD:\ Database\ password\ \(if\ required\)=PASSWORD:\ ${INVENTREE_DB_PASSWORD}=g ${INVENTREE_CONFIG_FILE}
  # Database host
  sed -i s=#\ HOST:\ Database\ host\ address\ \(if\ required\)=HOST:\ ${INVENTREE_DB_HOST}=g ${INVENTREE_CONFIG_FILE}
  # Database port
  sed -i s=#\ PORT:\ Database\ host\ port\ \(if\ required\)=PORT:\ ${INVENTREE_DB_PORT}=g ${INVENTREE_CONFIG_FILE}

  # Fixing the permissions
  chown ${APP_USER}:${APP_GROUP} ${DATA_DIR} ${INVENTREE_CONFIG_FILE}

  echo "# POI13| Done setting up InvenTree config values"
}

function set_site() {
  # Ensure IP is known
  if [ -z "${INVENTREE_IP}" ]; then
    echo "# POI14| No IP address found - skipping"
    return
  fi

  # Check if INVENTREE_SITE_URL in inventree config
  if [ -z "$(inventree config:get INVENTREE_SITE_URL)" ]; then
    # Prefer current INVENTREE_SITE_URL if set
    if [ -n "${INVENTREE_SITE_URL}" ]; then
      inventree config:set INVENTREE_SITE_URL=${INVENTREE_SITE_URL}
    else
      echo "# POI14| Setting up InvenTree site URL"
      inventree config:set INVENTREE_SITE_URL=http://${INVENTREE_IP}
    fi
  else
    echo "# POI14| Site URL already set to '$INVENTREE_SITE_URL' - skipping"
  fi
}

function final_message() {
  echo "# POI16| Printing Final message"
  echo -e "####################################################################################"
  echo -e "This InvenTree install uses nginx, the settings for the webserver can be found in"
  echo -e "${SETUP_NGINX_FILE}"
  echo -e "Try opening InvenTree with any of \n${INVENTREE_SITE_URL} , http://localhost/ or http://${INVENTREE_IP}/ \n"
  # Print admin user data only if set
  if [ -n "${INVENTREE_ADMIN_USER}" ]; then
    echo -e "Admin user data:"
    echo -e "   Email: ${INVENTREE_ADMIN_EMAIL}"
    echo -e "   Username: ${INVENTREE_ADMIN_USER}"
    echo -e "   Password: ${INVENTREE_ADMIN_PASSWORD}"
  else
    echo -e "No admin set during this operation - depending on the deployment method a admin user might have been created with an initial password saved in `$SETUP_ADMIN_PASSWORD_FILE`"
  fi
  echo -e "####################################################################################"
}


function update_checks() {
  echo "# POI08| Running upgrade"
  local old_version=$1
  local old_version_rev=$(echo ${old_version} | cut -d'-' -f1 | cut -d'.' -f2)
  local new_version=$(dpkg-query --show --showformat='${Version}' inventree)
  local new_version_rev=$(echo ${new_version} | cut -d'-' -f1 | cut -d'.' -f2)
  echo "# POI08| Old version is: ${old_version} | ${old_version_rev} - updating to ${new_version} | ${old_version_rev}"

  local ABORT=false
  function check_config_value() {
    local env_key=$1
    local config_key=$2
    local name=$3

    local value=$(inventree config:get ${env_key})
    if [ -z "${value}" ] || [ "$value" == "null" ]; then
      value=$(jq -r ".[].${config_key}" <<< ${INVENTREE_CONF_DATA})
    fi
    if [ -z "${value}" ] || [ "$value" == "null" ]; then
      echo "# POI08| No setting for ${name} found - please set it manually either in ${INVENTREE_CONFIG_FILE} under '${config_key}' or with 'inventree config:set ${env_key}=value'"
      ABORT=true
    else
      echo "# POI08| Found setting for ${name} - ${value}"
    fi
  }

  # Custom checks if old version is below 0.8.0
  if [ "${old_version_rev}" -lt "9" ]; then
    echo "# POI08| Old version is below 0.9.0 - You might be missing some configs"

    # Check for BACKUP_DIR and SITE_URL in INVENTREE_CONF_DATA and config
    check_config_value "INVENTREE_SITE_URL" "site_url" "site URL"
    check_config_value "INVENTREE_BACKUP_DIR" "backup_dir" "backup dir"

    if [ "${ABORT}" = true ]; then
      echo "# POI08| Aborting - please set the missing values and run the update again"
      exit 1
    fi
    echo "# POI08| All checks passed - continuing with the update"
  fi
}
