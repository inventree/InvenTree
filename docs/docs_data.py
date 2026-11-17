"""Shared data for the documentation build process.

This module loads the generated InvenTree definition files (settings, status codes,
report context, etc) which are used by the custom macros defined in 'main.py'.

It is deliberately separate from 'main.py', as some static site generators
(e.g. zensical) re-execute the macros module for *every* page. As a regular
module, this file is imported (and cached) only once per build process:

- Generated data files are loaded lazily, and reloaded only if they change on disk
- Observed settings / status codes are accumulated across all pages of the build
- The 'on_config' hook values are computed once (for generators without hook support)
"""

import importlib.util
import json
import os
import threading
from pathlib import Path
from typing import Any, Optional

import yaml

HERE = Path(__file__).parent
GENERATED_DIR = HERE.joinpath('generated')

# Files where we *store* information on what has been documented during the build.
# These are checked after the build completes (see 'on_post_build' in docs/hooks.py)
OBSERVED_SETTINGS_FILE = GENERATED_DIR.joinpath('observed_settings.json')
OBSERVED_STATUS_CODES_FILE = GENERATED_DIR.joinpath('observed_status_codes.json')

_lock = threading.RLock()

# Cache of loaded data files: {filename: (mtime, data)}
_file_cache: dict[str, tuple[float, Any]] = {}

# Things which have been rendered somewhere in the documentation
_observed_settings: dict[str, dict[str, bool]] = {'global': {}, 'user': {}}
_observed_status_codes: dict[str, bool] = {}

# Cached result of the 'on_config' hook
_hook_config: Optional[dict] = None


def print_build_environment():
    """Print some useful debugging information - useful for diagnosing CI build issues.

    Ref: https://docs.readthedocs.io/en/stable/reference/environment-variables.html
    """
    print('loading ./docs/docs_data.py...')

    for key in [
        'GITHUB_ACTIONS',
        'GITHUB_REF',
        'READTHEDOCS',
        'READTHEDOCS_GIT_IDENTIFIER',
        'READTHEDOCS_GIT_CLONE_URL',
        'READTHEDOCS_GIT_COMMIT_HASH',
        'READTHEDOCS_PROJECT',
        'READTHEDOCS_VERSION',
        'READTHEDOCS_VERSION_NAME',
        'READTHEDOCS_VERSION_TYPE',
    ]:
        val = os.environ.get(key, None) or '-- MISSING --'
        print(f' - {key}: {val}')


def _write_json(path: Path, data: Any):
    """Write data to a JSON file."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


def reset_observations():
    """Reset the record of observed settings and status codes.

    Called once when this module is first imported (i.e. once per build process).
    """
    with _lock:
        _observed_settings.clear()
        _observed_settings.update({'global': {}, 'user': {}})
        _observed_status_codes.clear()

        _write_json(OBSERVED_SETTINGS_FILE, _observed_settings)
        _write_json(OBSERVED_STATUS_CODES_FILE, _observed_status_codes)


def observe_setting(key: str, group: str):
    """Record that a particular setting has been documented.

    Arguments:
        key: The name of the setting
        group: The group of the setting (e.g. 'global', 'user', 'config')
    """
    with _lock:
        group_data = _observed_settings.setdefault(group, {})

        if key not in group_data:
            group_data[key] = True
            _write_json(OBSERVED_SETTINGS_FILE, _observed_settings)


def observe_status_code(class_name: str):
    """Record that a particular status code class has been documented."""
    with _lock:
        if class_name not in _observed_status_codes:
            _observed_status_codes[class_name] = True
            _write_json(OBSERVED_STATUS_CODES_FILE, _observed_status_codes)


def load_file(filename: str) -> Any:
    """Load a generated data file (JSON or YAML), caching the result.

    The file is reloaded only if it has been modified since it was last loaded.

    Arguments:
        filename: Name of the file, relative to the 'generated' directory
    """
    path = GENERATED_DIR.joinpath(filename)
    mtime = path.stat().st_mtime

    with _lock:
        cached = _file_cache.get(filename)

        if cached and cached[0] == mtime:
            return cached[1]

        with open(path, encoding='utf-8') as f:
            if path.suffix in ('.yml', '.yaml'):
                data = yaml.load(f, yaml.BaseLoader)
            else:
                data = json.load(f)

        _file_cache[filename] = (mtime, data)
        return data


def settings(group: str) -> dict:
    """Return the settings definitions for a given group ('global', 'user', 'config')."""
    return load_file('inventree_settings.json')[group]


def tags() -> Any:
    """Return the custom template tags definitions."""
    return load_file('inventree_tags.yml')


def filters() -> Any:
    """Return the custom template filters definitions."""
    return load_file('inventree_filters.yml')


def status_codes() -> dict:
    """Return the status code class definitions."""
    return load_file('inventree_status_codes.json')


def report_context() -> dict:
    """Return the report context definitions."""
    return load_file('inventree_report_context.json')


def roles() -> Any:
    """Return the user permission role definitions."""
    return load_file('inventree_roles.json')


def audited_models() -> Any:
    """Return the audited model definitions."""
    return load_file('inventree_audited_models.json')


def hook_config(site_url: Optional[str] = None) -> dict:
    """Return the config values provided by the 'on_config' hook in docs/hooks.py.

    Zensical does not run mkdocs hooks, so
    the hook is run once here, and the result cached for subsequent pages.
    """
    global _hook_config

    with _lock:
        if _hook_config is None:
            spec = importlib.util.spec_from_file_location(
                'inventree_docs_hooks', HERE.joinpath('docs', 'hooks.py')
            )
            hooks = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(hooks)
            _hook_config = hooks.on_config({'site_url': site_url})

        return _hook_config


print_build_environment()
reset_observations()
