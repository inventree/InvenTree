"""Static files management for InvenTree plugins.

All of the public functions in this module read and/or write the same shared
'plugins/' static output directory tree, and are not safe to run concurrently
with each other - see inventree#12769. Each one therefore acquires
PLUGIN_STATIC_FILES_LEASE for its full duration; nothing below should touch
`staticfiles_storage` outside of a section that holds this lease.

Everything that touches `staticfiles_storage` goes through the Storage API only
(`.save`/`.delete`/`.exists`/`.listdir`/`.open`) - STATIC_ROOT is not assumed to
be local disk, since some deployments configure a remote backend (e.g. S3),
which has no rename/move primitive and no local filesystem path to operate on
directly.
"""

import tempfile
from pathlib import Path

from django.contrib.staticfiles.storage import staticfiles_storage

import structlog

from plugin.registry import _acquire_lease_blocking, _release_lease, registry

logger = structlog.get_logger('inventree')

# Only one static-file collection operation (bulk or per-plugin) may run at a time.
PLUGIN_STATIC_FILES_LEASE = '_PLUGIN_STATIC_FILES'


def clear_static_dir(path: str, recursive: bool = True):
    """Clear the specified directory from the 'static' output directory.

    Arguments:
        path: The path to the directory to clear
        recursive: If True, clear the directory recursively

    Caller must already hold PLUGIN_STATIC_FILES_LEASE.
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

    logger.info('Cleared static directory: %s', path)


def _parent_dirs(relative_paths) -> set:
    """Return every directory (relative, no trailing slash) implied by a set of file paths.

    e.g. {'a/b/c.js'} -> {'a', 'a/b'}
    """
    dirs = set()

    for relative_path in relative_paths:
        parts = relative_path.split('/')[:-1]

        for i in range(1, len(parts) + 1):
            dirs.add('/'.join(parts[:i]))

    return dirs


def _iter_storage_files(prefix: str):
    """Recursively yield paths, relative to `prefix`, of every file under a storage prefix.

    Arguments:
        prefix: The storage prefix to search under

    Yields:
        Relative paths of every file under the specified prefix, with no leading slash.
    """
    if not staticfiles_storage.exists(prefix):
        return

    dirs, files = staticfiles_storage.listdir(prefix)

    yield from files

    for d in dirs:
        for relative_path in _iter_storage_files(f'{prefix}{d}/'):
            yield f'{d}/{relative_path}'


def _copy_plugin_static_files(slug: str):
    """Copy static files for the specified plugin.

    First copies the plugin's static files into a local temporary directory, so
    that a failure reading the plugin's own source files (a crash, a permission
    error, a source file disappearing mid-read) is caught before anything is
    written to the live destination at all. Only once that full copy has
    succeeded are the files written into the live destination - one at a time,
    deleting any existing file of the same name first (the storage API has no
    in-place overwrite: saving over an existing name otherwise gets a
    '_XXXXXXX' collision-avoidance suffix instead, which is one of the ways the
    original bug corrupted the output). Files that existed at the destination
    before but are not part of the new content are only removed as the final
    step, so files that are not being replaced are never affected.

    This does not give the same guarantee for a file that *is* being replaced:
    the delete-then-save pair for that one file is not atomic (the storage API
    has no rename/replace primitive to make it so), so a write failure at that
    exact moment can leave that single file transiently missing, even though
    every other file keeps whatever content (old or new) it already had. This
    is a large reduction in blast radius versus clearing the whole directory
    up front (the original bug), and self-heals on the next successful run,
    but it is not an absolute guarantee for the one in-flight file.

    Caller must already hold PLUGIN_STATIC_FILES_LEASE.
    """
    plugin = registry.get_plugin(slug)

    if not plugin:
        return

    logger.info("Collecting static files for plugin '%s'", slug)

    # Get the source path for the plugin
    source_path = plugin.path().joinpath('static')

    if not source_path.is_dir():
        return

    destination_prefix = f'plugins/{slug}/'
    previous_files = set(_iter_storage_files(destination_prefix))

    with tempfile.TemporaryDirectory(prefix=f'inventree-plugin-{slug}-') as tmp_dir:
        staging_path = Path(tmp_dir)
        relative_paths = []

        for item in source_path.rglob('*'):
            if not item.is_file():
                continue

            relative_path = item.relative_to(source_path).as_posix()
            target = staging_path / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(item.read_bytes())

            relative_paths.append(relative_path)

        # Deterministic order, so behaviour (and any partial-failure outcome)
        # does not depend on filesystem directory iteration order
        relative_paths.sort()

        # Everything is readable and staged locally - now write it to the live
        # destination, one file at a time
        for relative_path in relative_paths:
            destination_path = f'{destination_prefix}{relative_path}'

            if staticfiles_storage.exists(destination_path):
                staticfiles_storage.delete(destination_path)

            with (staging_path / relative_path).open('rb') as content:
                staticfiles_storage.save(destination_path, content)

            logger.debug('- copied %s to %s', relative_path, destination_path)

    # Remove any files that were part of the previous content but are not part
    # of this one - only now that the new content is fully in place
    stale_files = previous_files - set(relative_paths)

    for stale_path in stale_files:
        staticfiles_storage.delete(f'{destination_prefix}{stale_path}')

    # A directory that only contained stale files is now empty, but not removed
    # by the file deletions above - remove any such directories too (deepest
    # first, so each is already empty by the time its own turn comes)
    stale_dirs = _parent_dirs(stale_files) - _parent_dirs(relative_paths)

    for stale_dir in sorted(stale_dirs, key=lambda d: d.count('/'), reverse=True):
        staticfiles_storage.delete(f'{destination_prefix}{stale_dir}/')

    if relative_paths:
        logger.info(
            "Copied %s static files for plugin '%s'.", len(relative_paths), slug
        )


def collect_plugins_static_files():
    """Copy static files from all installed plugins into the static directory."""
    registry.check_reload()

    if not _acquire_lease_blocking(PLUGIN_STATIC_FILES_LEASE):
        logger.error(
            'Could not acquire plugin static files lease - skipping collection'
        )
        return

    try:
        logger.info('Collecting static files for all installed plugins.')

        for slug in registry.plugins:
            _copy_plugin_static_files(slug)
    finally:
        _release_lease(PLUGIN_STATIC_FILES_LEASE)


def clear_plugins_static_files():
    """Clear out static files for plugins which are no longer active."""
    if not _acquire_lease_blocking(PLUGIN_STATIC_FILES_LEASE):
        logger.error('Could not acquire plugin static files lease - skipping cleanup')
        return

    try:
        installed_plugins = set(registry.plugins.keys())

        path = 'plugins/'

        # Check that the directory actually exists
        if not staticfiles_storage.exists(path):
            return

        # Get all static files in the 'plugins' static directory
        dirs, _files = staticfiles_storage.listdir('plugins/')

        for d in dirs:
            # Check if the directory is a plugin directory
            if d not in installed_plugins:
                # Clear out the static files for this plugin
                clear_static_dir(f'plugins/{d}/', recursive=True)
    finally:
        _release_lease(PLUGIN_STATIC_FILES_LEASE)


def copy_plugin_static_files(slug, check_reload=True):
    """Copy static files for the specified plugin."""
    if check_reload:
        registry.check_reload()

    if not _acquire_lease_blocking(PLUGIN_STATIC_FILES_LEASE):
        logger.error(
            "Could not acquire plugin static files lease - skipping collection for plugin '%s'",
            slug,
        )
        return

    try:
        _copy_plugin_static_files(slug)
    finally:
        _release_lease(PLUGIN_STATIC_FILES_LEASE)


def clear_plugin_static_files(slug: str, recursive: bool = True):
    """Clear static files for the specified plugin."""
    if not _acquire_lease_blocking(PLUGIN_STATIC_FILES_LEASE):
        logger.error(
            "Could not acquire plugin static files lease - skipping removal for plugin '%s'",
            slug,
        )
        return

    try:
        clear_static_dir(f'plugins/{slug}/', recursive=recursive)
    finally:
        _release_lease(PLUGIN_STATIC_FILES_LEASE)
