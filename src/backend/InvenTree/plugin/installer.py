"""Install a plugin into the python virtual environment."""

import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import structlog

import plugin.models
import plugin.staticfiles
from InvenTree.exceptions import log_error

logger = structlog.get_logger('inventree')


def pip_command(*args) -> str:
    """Build and run a pip command using using the current python executable.

    Returns: The output of the pip command

    Raises:
        subprocess.CalledProcessError: If the pip command fails
    """
    python = sys.executable

    command = [python, '-m', 'pip']

    command.extend(args)

    command = [str(x) for x in command]

    logger.info('Running pip command: %s', ' '.join(command))

    ret = subprocess.check_output(
        command, cwd=settings.BASE_DIR.parent, stderr=subprocess.STDOUT
    ).decode('utf-8')
    if 'No module named pip' in ret:
        raise ValidationError(_('Pip is not installed in the current environment'))
    return ret


def handle_pip_error(error, path: str) -> list:
    """Raise a ValidationError when the pip command fails.

    - Log the error to the database
    - Format the output from a pip command into a list of error messages.
    - Raise an appropriate error
    """
    log_error(path, scope='pip')

    output = error.output.decode('utf-8')

    logger.error('Pip command failed: %s', output)

    errors = []

    for line in output.split('\n'):
        line = line.strip()

        if line:
            errors.append(line)

    if len(errors) > 1:
        raise ValidationError(errors)
    else:
        raise ValidationError(errors[0])


def get_install_info(packagename: str) -> dict:
    """Determine the install information for a particular package.

    - Uses 'pip show' to determine the install location of a package.
    """
    logger.debug('get_install_info: %s', packagename)

    # Remove version information
    for c in '<>=!@ ':
        packagename = packagename.split(c)[0]

    info = {}

    try:
        result = pip_command('show', packagename)

        output = result.split('\n')

        for line in output:
            parts = line.split(':')

            if len(parts) >= 2:
                key = str(parts[0].strip().lower().replace('-', '_'))
                value = str(parts[1].strip())

                info[key] = value

    except subprocess.CalledProcessError as error:
        log_error('get_install_info', scope='pip')

        output = error.output.decode('utf-8')
        info['error'] = output
        logger.exception('Plugin lookup failed: %s', output)
    except Exception:
        log_error('get_install_info', scope='pip')

    return info


def plugins_file_hash():
    """Return the file hash for the plugins file."""
    import hashlib

    pf = settings.PLUGIN_FILE

    if not pf or not pf.exists():
        return None

    try:
        with pf.open('rb') as f:
            return hashlib.file_digest(f, 'sha256').hexdigest()
    except Exception:
        log_error('plugins_file_hash', scope='plugins')
        return None


def plugin_env_marker_path() -> Path:
    """Return the path to the plugin-install marker file for the *current* python environment.

    This lives inside the running interpreter's environment (``sys.prefix``)
    rather than in the database, so it disappears along with the rest of the
    environment whenever a fresh virtual environment is created - e.g. a
    container replaced without a persistent venv volume. A database-only hash
    cannot tell such a fresh environment apart from one that already has the
    packages installed (inventree/InvenTree#12848).
    """
    return Path(sys.prefix) / '.inventree_plugins_hash'


# Process-local fallback for get_env_plugin_hash(), used when the marker file
# itself cannot be written (e.g. a read-only sys.prefix).
_env_plugin_hash_cache: Optional[str] = None


def get_env_plugin_hash() -> Optional[str]:
    """Return the plugin file hash last installed into the *current* python environment.

    Returns None if no install has been recorded here (e.g. a fresh environment).
    """
    if _env_plugin_hash_cache is not None:
        return _env_plugin_hash_cache

    path = plugin_env_marker_path()

    if not path.exists():
        return None

    try:
        return path.read_text().strip()
    except Exception:
        log_error('get_env_plugin_hash', scope='plugins')
        return None


def set_env_plugin_hash(file_hash: str) -> None:
    """Record that the current python environment has installed the given plugin file hash."""
    global _env_plugin_hash_cache

    _env_plugin_hash_cache = file_hash

    try:
        plugin_env_marker_path().write_text(file_hash)
    except Exception:
        # Not logged via log_error/the database error log: on a deployment
        # where sys.prefix is not writable (by design, e.g. a read-only
        # root filesystem) this would otherwise happen on every single
        # process start forever, and it is an environment property rather
        # than an application bug.
        logger.warning(
            "Could not persist plugin install marker to '%s' - this "
            'environment will be re-verified on every process restart '
            'instead of only when %s changes',
            plugin_env_marker_path(),
            settings.PLUGIN_FILE,
        )


def install_plugins_file():
    """Install plugins from the plugins file."""
    logger.info('Installing plugins from plugins file')

    pf = settings.PLUGIN_FILE

    if not pf or not pf.exists():
        logger.warning('Plugin file %s does not exist', pf)
        return

    cmd = ['install', '--disable-pip-version-check', '-U', '-r', str(pf)]

    try:
        pip_command(*cmd)
    except subprocess.CalledProcessError as error:
        output = error.output.decode('utf-8')
        logger.exception('Plugin file installation failed: %s', output)
        log_error('install_plugins_file', scope='pip')
        return False
    except Exception as exc:
        logger.exception('Plugin file installation failed: %s', exc)
        log_error('install_plugins_file', scope='pip')
        return False

    # Collect plugin static files
    try:
        plugin.staticfiles.collect_plugins_static_files()
    except Exception:
        log_error('collect_plugins_static_files', scope='plugins')

    # At this point, the plugins file has been installed
    return True


def update_plugins_file(package_reference: str, remove: bool = False):
    """Add a plugin to the plugins file."""
    if remove:
        logger.info('Removing plugin from plugins file: %s', package_reference)
    else:
        logger.info('Adding plugin to plugins file: %s', package_reference)

    pf = settings.PLUGIN_FILE

    if not pf or not pf.exists():
        logger.warning('Plugin file %s does not exist', pf)
        return

    def compare_line(line: str):
        """Check if a line in the file matches the installname."""
        return re.match(rf'^{re.escape(package_reference)}(?:[\s=@]|$)', line.strip())

    # First, read in existing plugin file
    try:
        with pf.open(mode='r') as f:
            lines = f.readlines()
    except Exception as exc:
        logger.exception('Failed to read plugins file: %s', exc)
        log_error('update_plugins_file', scope='plugins')
        return

    # Reconstruct output file
    output = []

    found = False

    # Check if plugin is already in file
    for line in lines:
        # Ignore processing for any commented lines
        if line.strip().startswith('#'):
            output.append(line)
            continue

        if compare_line(line):
            found = True
            if not remove:
                # Replace line with new install name
                output.append(package_reference)
        else:
            output.append(line)

    # Append plugin to file
    if not found and not remove:
        output.append(package_reference)

    # Write file back to disk
    try:
        with pf.open(mode='w') as f:
            for line in output:
                f.write(line)

                if not line.endswith('\n'):
                    f.write('\n')
    except Exception as exc:
        logger.exception('Failed to add plugin to plugins file: %s', exc)
        log_error('update_plugins_file', scope='plugins')


def install_plugin(
    user: Optional[User] = None,
    url: Optional[str] = None,
    packagename: Optional[str] = None,
    version: Optional[str] = None,
):
    """Install a plugin into the python virtual environment.

    Args:
        user: user performing the installation
        packagename: Optional package name to install
        url: Optional URL to install from
        version: Optional version specifier
    """
    if user and not user.is_superuser:
        raise ValidationError(_('Only superuser accounts can administer plugins'))

    if settings.PLUGINS_INSTALL_DISABLED:
        raise ValidationError(_('Plugin installation is disabled'))

    logger.info('install_plugin: %s, %s', url, packagename)

    # build up the command
    package_ref: Optional[str] = None
    index_url = None

    if url:
        # VCS based install - this can just be a VCS reference
        if url.startswith(('git+https://', 'hg+https://', 'svn+svn://')):
            # using a VCS provider
            package_ref = f'{packagename}@{url}' if packagename else url
        # http based index reference
        elif url.startswith(('http://', 'https://')) and packagename:
            package_ref = packagename
            index_url = url
        # Ignore url and just use default index
        elif packagename:
            package_ref = packagename
        else:
            raise ValidationError(_('Invalid URL and no package name provided'))

    elif packagename:
        # use default index - most often pypi
        package_ref = packagename

        if version:
            package_ref = f'{packagename}=={version}'
    else:
        raise ValidationError(_('No package name or URL provided for installation'))

    # Sanitize the package name for installation
    if any(c in package_ref for c in ';&|`$()'):
        raise ValidationError(_('Invalid characters in package name or URL'))

    # Execute installation via pip
    cmd: list[str] = ['install', '-U', '--disable-pip-version-check']
    if index_url:
        cmd += ['-i', index_url]

    ret = {}
    try:
        result = pip_command(*cmd, package_ref)

        ret['result'] = ret['success'] = _('Installed plugin successfully')
        ret['output'] = result

        if packagename and (info := get_install_info(packagename)):
            if path := info.get('location'):
                ret['result'] = _(f'Installed plugin into {path}')
                ret['version'] = info.get('version')

    except subprocess.CalledProcessError as error:
        handle_pip_error(error, 'plugin_install')
    except Exception:
        log_error('install_plugin', scope='plugins')

    if version := ret.get('version'):
        # Save plugin to plugins file
        update_plugins_file(package_reference=package_ref)

        # Reload the plugin registry, to discover the new plugin
        from plugin.registry import registry

        registry.reload_plugins(full_reload=True, force_reload=True, collect=True)

        # Update static files
        plugin.staticfiles.collect_plugins_static_files()

    return ret


def validate_package_plugin(cfg: plugin.models.PluginConfig, user=None):
    """Validate a package plugin for update or removal."""
    if not cfg.plugin:
        raise ValidationError(_('Plugin was not found in registry'))

    if not cfg.is_package():
        raise ValidationError(_('Plugin is not a packaged plugin'))

    if not cfg.package_name:
        raise ValidationError(_('Plugin package name not found'))

    if user and not user.is_staff:
        raise ValidationError(_('Only staff users can administer plugins'))


def uninstall_plugin(cfg: plugin.models.PluginConfig, user=None, delete_config=True):
    """Uninstall a plugin from the python virtual environment.

    - The plugin must not be active
    - The plugin must be a "package" and have a valid package name

    Args:
        cfg: PluginConfig object
        user: User performing the uninstall
        delete_config: If True, delete the plugin configuration from the database
    """
    from plugin.registry import registry

    if user and not user.is_superuser:
        raise ValidationError(_('Only superuser accounts can administer plugins'))

    if settings.PLUGINS_INSTALL_DISABLED:
        raise ValidationError(_('Plugin uninstalling is disabled'))

    if cfg.active:
        raise ValidationError(
            _('Plugin cannot be uninstalled as it is currently active')
        )

    if cfg.is_mandatory():  # pragma: no cover
        # This is only an additional check, as mandatory plugins cannot be deactivated
        raise ValidationError(
            'INVE-E10' + _('Plugin cannot be uninstalled as it is mandatory')
        )

    if cfg.is_sample():
        raise ValidationError(
            'INVE-E10' + _('Plugin cannot be uninstalled as it is a sample plugin')
        )

    if cfg.is_builtin():
        raise ValidationError(
            'INVE-E10' + _('Plugin cannot be uninstalled as it is a built-in plugin')
        )

    if not cfg.is_installed():
        raise ValidationError(_('Plugin is not installed'))

    validate_package_plugin(cfg, user)
    package_name = cfg.package_name

    pkg_info = get_install_info(package_name)

    if path := pkg_info.get('location'):
        # Uninstall the plugin using pip
        logger.info('Uninstalling plugin: %s from %s', package_name, path)
        try:
            pip_command('uninstall', '-y', package_name)
        except subprocess.CalledProcessError as error:
            handle_pip_error(error, 'plugin_uninstall')
        except Exception:
            log_error('uninstall_plugin', scope='plugins')
    else:
        # No matching install target found
        raise ValidationError(_('Plugin installation not found'))

    # Update the plugins file
    update_plugins_file(package_reference=package_name, remove=True)

    if delete_config:
        logger.info('Deleting plugin configuration from database: %s', cfg.key)
        # Remove the plugin configuration from the database
        cfg.delete()

    # Remove static files associated with this plugin
    plugin.staticfiles.clear_plugin_static_files(cfg.key)

    # Reload the plugin registry
    registry.reload_plugins(full_reload=True, force_reload=True, collect=True)

    return {'result': _('Uninstalled plugin successfully'), 'success': True}
