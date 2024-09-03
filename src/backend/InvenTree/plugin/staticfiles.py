"""Static files management for InvenTree plugins."""

import logging

from django.contrib.staticfiles.storage import staticfiles_storage

from plugin.registry import registry

logger = logging.getLogger('inventree')


def clear_static_dir(path, recursive=True):
    """Clear the specified directory from the 'static' output directory.

    Arguments:
        path: The path to the directory to clear
        recursive: If True, clear the directory recursively
    """
    if not staticfiles_storage.exists(path):
        return

    dirs, files = staticfiles_storage.listdir(path)

    for f in files:
        staticfiles_storage.delete(f'{path}{f}')

    if recursive:
        for d in dirs:
            clear_static_dir(f'{path}{d}/', recursive=True)
            staticfiles_storage.delete(f'{path}{d}')

    # Finally, delete the directory itself to remove orphan folders when uninstalling a plugin
    staticfiles_storage.delete(path)


def collect_plugins_static_files():
    """Copy static files from all installed plugins into the static directory."""
    registry.check_reload()

    logger.info('Collecting static files for all installed plugins.')

    for slug in registry.plugins:
        copy_plugin_static_files(slug, check_reload=False)


def copy_plugin_static_files(slug, check_reload=True):
    """Copy static files for the specified plugin."""
    if check_reload:
        registry.check_reload()

    plugin = registry.get_plugin(slug)

    if not plugin:
        return

    logger.info("Copying static files for plugin '%s'", slug)

    # Get the source path for the plugin
    source_path = plugin.path().joinpath('static')

    if not source_path.is_dir():
        return

    # Create prefix for the destination path
    destination_prefix = f'plugins/{slug}/'

    # Clear the destination path
    clear_static_dir(destination_prefix)

    items = list(source_path.glob('*'))

    idx = 0
    copied = 0

    while idx < len(items):
        item = items[idx]

        idx += 1

        if item.is_dir():
            items.extend(item.glob('*'))
            continue

        if item.is_file():
            relative_path = item.relative_to(source_path)

            destination_path = f'{destination_prefix}{relative_path}'

            with item.open('rb') as src:
                staticfiles_storage.save(destination_path, src)

            logger.debug('- copied %s to %s', str(item), str(destination_path))
            copied += 1

    logger.info("Copied %s static files for plugin '%s'.", copied, slug)
