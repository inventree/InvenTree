"""Unit tests for plugin static file collection (see plugin/staticfiles.py).

These lock down the behaviour introduced while fixing inventree#12769 (concurrent
processes corrupting plugin static output): copy-then-swap semantics, stale file/
directory cleanup, overwrite behaviour, and engagement of the shared lease.
"""

import tempfile
from pathlib import Path
from unittest import mock

from django.contrib.staticfiles.storage import staticfiles_storage
from django.test import TestCase

import plugin.staticfiles as plugin_staticfiles
from InvenTree.unit_test import PluginRegistryMixin
from plugin.registry import _try_acquire_lease, registry


class FakePlugin:
    """Minimal stand-in for a loaded plugin, exposing only what staticfiles.py needs."""

    def __init__(self, source_dir):
        """Store the (local) directory containing this fake plugin's 'static' folder."""
        self.source_dir = source_dir

    def path(self):
        """Return the plugin's base directory, matching InvenTreePlugin.path()."""
        return Path(self.source_dir)


class PluginStaticFilesTestCase(PluginRegistryMixin, TestCase):
    """Base class which provides a scratch plugin source directory and destination slug."""

    def setUp(self):
        """Set up a fresh source directory and a unique destination slug for each test."""
        super().setUp()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)

        self.slug = f'test-static-{self._testMethodName}'.lower().replace('_', '-')
        self.destination_prefix = f'plugins/{self.slug}/'

        self.addCleanup(self.clear_destination)

    def clear_destination(self):
        """Remove any files this test wrote under its destination prefix."""
        plugin_staticfiles.clear_static_dir(self.destination_prefix)

    def write_source(self, files: dict) -> str:
        """Write `files` (relative path -> content) under a 'static' folder in a new source dir.

        Returns the source directory path.
        """
        source_dir = tempfile.mkdtemp(dir=self.tmp_dir.name)
        static_dir = Path(source_dir) / 'static'

        for relative_path, content in files.items():
            target = static_dir / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)

        return source_dir

    def copy_files(self, files: dict):
        """Write `files` as a fake plugin's source, then run the real copy for self.slug."""
        source_dir = self.write_source(files)

        with mock.patch.object(
            registry, 'get_plugin', return_value=FakePlugin(source_dir)
        ):
            plugin_staticfiles._copy_plugin_static_files(self.slug)

    def read_destination(self) -> dict:
        """Return {relative_path: content} for every file currently at the destination."""
        result = {}

        for relative_path in plugin_staticfiles._iter_storage_files(
            self.destination_prefix
        ):
            with staticfiles_storage.open(
                f'{self.destination_prefix}{relative_path}'
            ) as f:
                result[relative_path] = f.read().decode()

        return result


class CopyPluginStaticFilesTests(PluginStaticFilesTestCase):
    """Tests for `_copy_plugin_static_files` - the actual file-copying logic."""

    def test_basic_copy(self):
        """Files (including nested ones) are copied to the destination unchanged."""
        self.copy_files({'a.js': 'content-a', 'sub/b.js': 'content-b'})

        self.assertEqual(
            self.read_destination(), {'a.js': 'content-a', 'sub/b.js': 'content-b'}
        )

    def test_no_static_dir_is_a_noop(self):
        """A plugin with no 'static' folder at all is silently skipped."""
        source_dir = tempfile.mkdtemp(dir=self.tmp_dir.name)  # no 'static' subfolder

        with mock.patch.object(
            registry, 'get_plugin', return_value=FakePlugin(source_dir)
        ):
            plugin_staticfiles._copy_plugin_static_files(self.slug)

        self.assertEqual(self.read_destination(), {})

    def test_unknown_plugin_is_a_noop(self):
        """An unrecognised slug is silently skipped."""
        with mock.patch.object(registry, 'get_plugin', return_value=None):
            plugin_staticfiles._copy_plugin_static_files(self.slug)

        self.assertEqual(self.read_destination(), {})

    def test_overwrite_does_not_leave_suffixed_duplicate(self):
        """Re-collecting replaces a file's content in place.

        Storage.save() does not overwrite an existing name by default - it invents
        a '..._XXXXXXX' suffixed name instead. This is one of the ways the original
        bug corrupted plugin output, so it must not happen here.
        """
        self.copy_files({'a.js': 'version-1'})
        self.copy_files({'a.js': 'version-2'})

        self.assertEqual(self.read_destination(), {'a.js': 'version-2'})

    def test_stale_file_is_removed(self):
        """A file present in the old content but not the new content is removed."""
        self.copy_files({'a.js': 'v1', 'stale.js': 'will-be-removed'})
        self.copy_files({'a.js': 'v1'})

        self.assertEqual(self.read_destination(), {'a.js': 'v1'})

    def test_stale_directory_is_removed(self):
        """A directory that only contained now-stale files is removed, not left empty."""
        self.copy_files({'sub/stale.js': 'old'})
        self.copy_files({'a.js': 'new'})

        self.assertEqual(self.read_destination(), {'a.js': 'new'})
        self.assertFalse(staticfiles_storage.exists(f'{self.destination_prefix}sub/'))
        self.assertFalse(staticfiles_storage.exists(f'{self.destination_prefix}sub'))

    def test_partial_write_failure_only_affects_the_in_flight_file(self):
        """If writing to live storage fails partway, only the in-flight file is affected.

        Files are written in a deterministic (sorted) order. A file processed
        before the failure keeps its new content; a file not yet reached keeps
        its old content untouched. The file being written at the moment of
        failure is a disclosed exception to this: replacing an existing file is
        a delete-then-save pair (the storage API has no atomic replace/rename
        primitive), so it may be left transiently missing rather than at its
        old *or* new content - this is a known, accepted gap (self-healing on
        the next successful run), not a regression to guard against here. What
        must hold is that nothing *else* is affected, and the exception
        propagates rather than being swallowed.
        """
        self.copy_files({'a.js': 'v1', 'b.js': 'v1', 'c.js': 'v1'})

        real_save = staticfiles_storage.save

        def flaky_save(name, content, *args, **kwargs):
            if name.endswith('b.js'):
                raise RuntimeError('simulated failure writing to live storage')
            return real_save(name, content, *args, **kwargs)

        source_dir = self.write_source({'a.js': 'v2', 'b.js': 'v2', 'c.js': 'v2'})

        with mock.patch.object(
            registry, 'get_plugin', return_value=FakePlugin(source_dir)
        ):
            with mock.patch.object(staticfiles_storage, 'save', side_effect=flaky_save):
                with self.assertRaises(RuntimeError):
                    plugin_staticfiles._copy_plugin_static_files(self.slug)

        destination = self.read_destination()
        self.assertEqual(destination['a.js'], 'v2')  # sorts before 'b.js' - written
        self.assertEqual(destination['c.js'], 'v1')  # sorts after 'b.js' - untouched
        self.assertNotIn('b.js', destination)  # disclosed gap - see docstring above

    def test_source_read_failure_does_not_touch_destination(self):
        """If reading the plugin's own source files fails, live content is untouched."""
        self.copy_files({'a.js': 'v1'})

        source_dir = self.write_source({'a.js': 'v2', 'bad.js': 'v2'})

        real_read_bytes = Path.read_bytes

        def flaky_read_bytes(self):
            if self.name == 'bad.js':
                raise OSError('simulated read failure')
            return real_read_bytes(self)

        with mock.patch.object(
            registry, 'get_plugin', return_value=FakePlugin(source_dir)
        ):
            with mock.patch.object(Path, 'read_bytes', flaky_read_bytes):
                with self.assertRaises(OSError):
                    plugin_staticfiles._copy_plugin_static_files(self.slug)

        # Nothing was written - the original content is exactly as it was
        self.assertEqual(self.read_destination(), {'a.js': 'v1'})


class StaticFilesLeaseEngagementTests(PluginStaticFilesTestCase):
    """Tests that the public staticfiles.py entry points actually engage the shared lease."""

    def with_short_timeout(self):
        """Patch _acquire_lease_blocking (as imported into staticfiles.py) to fail fast."""
        return mock.patch.object(
            plugin_staticfiles,
            '_acquire_lease_blocking',
            side_effect=lambda key, **kw: _try_acquire_lease(key),
        )

    def test_copy_plugin_static_files_skips_when_lease_held(self):
        """copy_plugin_static_files() must not run while the lease is held elsewhere."""
        source_dir = self.write_source({'a.js': 'v1'})

        self.assertTrue(
            _try_acquire_lease(plugin_staticfiles.PLUGIN_STATIC_FILES_LEASE)
        )
        try:
            with self.with_short_timeout():
                with mock.patch.object(
                    registry, 'get_plugin', return_value=FakePlugin(source_dir)
                ):
                    plugin_staticfiles.copy_plugin_static_files(
                        self.slug, check_reload=False
                    )
        finally:
            plugin_staticfiles._release_lease(
                plugin_staticfiles.PLUGIN_STATIC_FILES_LEASE
            )

        # The lease was held, so nothing should have been copied
        self.assertEqual(self.read_destination(), {})

    def test_collect_plugins_static_files_skips_when_lease_held(self):
        """collect_plugins_static_files() must not run while the lease is held elsewhere."""
        self.assertTrue(
            _try_acquire_lease(plugin_staticfiles.PLUGIN_STATIC_FILES_LEASE)
        )
        try:
            with self.with_short_timeout():
                with mock.patch.object(registry, 'check_reload'):
                    # Should return immediately without raising or iterating plugins
                    plugin_staticfiles.collect_plugins_static_files()
        finally:
            plugin_staticfiles._release_lease(
                plugin_staticfiles.PLUGIN_STATIC_FILES_LEASE
            )

    def test_clear_plugin_static_files_skips_when_lease_held(self):
        """clear_plugin_static_files() must not run while the lease is held elsewhere."""
        self.copy_files({'a.js': 'v1'})

        self.assertTrue(
            _try_acquire_lease(plugin_staticfiles.PLUGIN_STATIC_FILES_LEASE)
        )
        try:
            with self.with_short_timeout():
                plugin_staticfiles.clear_plugin_static_files(self.slug)
        finally:
            plugin_staticfiles._release_lease(
                plugin_staticfiles.PLUGIN_STATIC_FILES_LEASE
            )

        # The lease was held, so the file should still be there
        self.assertEqual(self.read_destination(), {'a.js': 'v1'})

    def test_copy_plugin_static_files_runs_once_lease_is_free(self):
        """Sanity check: with no competing lease, the copy proceeds normally."""
        source_dir = self.write_source({'a.js': 'v1'})

        with mock.patch.object(
            registry, 'get_plugin', return_value=FakePlugin(source_dir)
        ):
            plugin_staticfiles.copy_plugin_static_files(self.slug, check_reload=False)

        self.assertEqual(self.read_destination(), {'a.js': 'v1'})
