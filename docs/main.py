"""Main entry point for the documentation build process."""

import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Literal, Optional

import requests
import yaml

# Read in the InvenTree settings file
here = Path(__file__).parent

gen_base = here.joinpath('generated')

# Generated data is loaded (and cached) by a separate module, as some static site
# generators (e.g. zensical) re-execute this file for every page.
if str(here) not in sys.path:
    sys.path.append(str(here))

import docs_data


def get_repo_url(raw=False):
    """Return the repository URL for the current project."""
    mkdocs_yml = here.joinpath('mkdocs.yml')

    with open(mkdocs_yml, encoding='utf-8') as f:
        mkdocs_config = yaml.load(f, yaml.BaseLoader)
        repo_name = mkdocs_config['repo_name']

    if raw:
        return f'https://raw.githubusercontent.com/{repo_name}'
    else:
        return f'https://github.com/{repo_name}'


def check_link(url) -> bool:
    """Check that a provided URL is valid.

    We allow a number attempts and a lengthy timeout,
    as we do not want false negatives.
    """
    CACHE_FILE = gen_base.joinpath('url_cache.txt')

    # Keep a local cache file of URLs we have already checked
    if CACHE_FILE.exists():
        with open(CACHE_FILE, encoding='utf-8') as f:
            cache = f.read().splitlines()

        if url in cache:
            return True

    attempts = 5

    while attempts > 0:
        response = requests.head(url, timeout=5000)

        # Ensure GH is not causing issues
        if response.status_code in (200, 429):
            # Update the cache file
            with open(CACHE_FILE, 'a', encoding='utf-8') as f:
                f.write(f'{url}\n')

            return True

        attempts -= 1

        print(f'URL check failed with status code {response.status_code}')

    return False


def get_build_environment() -> Optional[str]:
    """Returns the branch we are currently building on, based on the environment variables of the various CI platforms."""
    # Check if we are in ReadTheDocs
    if os.environ.get('READTHEDOCS') == 'True':
        for var in ['READTHEDOCS_GIT_COMMIT_HASH', 'READTHEDOCS_GIT_IDENTIFIER']:
            if val := os.environ.get(var):
                return val
    # We are in GitHub Actions
    elif os.environ.get('GITHUB_ACTIONS') == 'true':
        return os.environ.get('GITHUB_REF')

    # Default to 'master' branch
    return 'master'


def apply_hook_config(env):
    """Provide values normally injected by the 'on_config' mkdocs hook.

    Zensical does not support mkdocs hooks, so 'config.releases',
    'config.assets_dir' etc are never set. Run the hook ourselves and
    inject the results into the template 'config' variable.
    """
    template_config = env.variables.get('config')

    if template_config is None:
        return

    hook_config = docs_data.hook_config(template_config.get('site_url'))

    for key in ['releases', 'assets_dir', 'readthedocs', 'version_banner']:
        if key in hook_config:
            template_config[key] = hook_config[key]


def define_env(env):
    """Define custom environment variables for the documentation build process."""
    apply_hook_config(env)

    config = env.variables.get('config') or env.config
    assets_dir = config.get('assets_dir', None)

    if assets_dir is None:
        # Construct the assets directory based on the current build environment
        rtd_version = os.environ.get('READTHEDOCS_VERSION')
        rtd_language = os.environ.get('READTHEDOCS_LANGUAGE')

        if rtd_version and rtd_language:
            assets_dir = f'/{rtd_language}/{rtd_version}/assets'
        else:
            assets_dir = '/assets'

    @env.macro
    def sourcedir(dirname: str, branch=None):
        """Return a link to a directory within the source code repository.

        Arguments:
            dirname: The name of the directory to link to (relative to the top-level directory)
            branch: The branch of the repository to link to (defaults to the current build environment)

        Returns:
            A fully qualified URL to the source code directory on GitHub

        Raises:
            FileNotFoundError: If the directory does not exist, or the generated URL is invalid
        """
        if branch == None:
            branch = get_build_environment()

        if dirname.startswith('/'):
            dirname = dirname[1:]

        # This file exists at ./docs/main.py, so any directory we link to must be relative to the top-level directory
        directory = here.parent.joinpath(dirname)
        if not directory.exists() or not directory.is_dir():
            raise FileNotFoundError(f'Source directory {dirname} does not exist.')

        repo_url = get_repo_url()

        url = f'{repo_url}/tree/{branch}/{dirname}'

        # Check that the URL exists before returning it
        if not check_link(url):
            raise FileNotFoundError(f'URL {url} does not exist.')

        return url

    @env.macro
    def sourcefile(filename, branch=None, raw=False):
        """Return a link to a file within the source code repository.

        Arguments:
            filename: The name of the file to link to (relative to the top-level directory)
            branch: The branch of the repository to link to (defaults to the current build environment)
            raw: If True, return the raw URL to the file (defaults to False)

        Returns:
            A fully qualified URL to the source code file on GitHub

        Raises:
            FileNotFoundError: If the file does not exist, or the generated URL is invalid
        """
        if branch == None:
            branch = get_build_environment()

        if filename.startswith('/'):
            filename = filename[1:]

        # This file exists at ./docs/main.py, so any file we link to must be relative to the top-level directory
        file_path = here.parent.joinpath(filename)
        if not file_path.exists():
            raise FileNotFoundError(f'Source file {filename} does not exist.')

        # Construct repo URL
        repo_url = get_repo_url(raw=False)
        url = f'{repo_url}/blob/{branch}/{filename}'

        # Check that the URL exists before returning it
        if not check_link(url):
            raise FileNotFoundError(f'URL {url} does not exist.')

        if raw:
            # If requesting the 'raw' URL, take this into account here...
            repo_url = get_repo_url(raw=True)
            url = f'{repo_url}/{branch}/{filename}'

        return url

    @env.macro
    def invoke_commands(command: str = '--list'):
        """Provides an output of the available commands."""
        tasks = here.parent.joinpath('tasks.py')
        output = gen_base.joinpath('invoke-commands.txt')

        command = f'invoke -f {tasks} {command} > {output}'

        assert subprocess.call(command, shell=True) == 0

        with open(output, encoding='utf-8') as f:
            content = f.read()

        return content

    @env.macro
    def listimages(subdir):
        """Return a listing of all asset files in the provided subdir."""
        directory = here.joinpath('docs', 'assets', 'images', subdir)

        assets = []

        allowed = ['.png', '.jpg']

        for asset in directory.iterdir():
            if any(str(asset).endswith(x) for x in allowed):
                assets.append(str(subdir / asset.relative_to(directory)))

        return assets

    @env.macro
    def includefile(filename: str, title: str, fmt: str = ''):
        """Include a file in the documentation, in a 'collapse' block.

        Arguments:
            filename: The name of the file to include (relative to the top-level directory)
            title: The title of the collapse block in the documentation
            fmt: The format of the included file (e.g., 'python', 'html', etc.)
        """
        path = here.parent.joinpath(filename)

        if not path.exists():
            raise FileNotFoundError(f'Required file {path} does not exist.')

        with open(path, encoding='utf-8') as f:
            content = f.read()

        data = f'??? abstract "{title}"\n\n'
        data += f'    ```{fmt}\n'
        data += textwrap.indent(content, '    ')
        data += '\n\n'
        data += '    ```\n\n'

        return data

    @env.macro
    def templatefile(filename):
        """Include code for a provided template file."""
        base = Path(filename).name
        fn = Path('src', 'backend', 'InvenTree', 'report', 'templates', filename)

        return includefile(fn, f'Template: {base}', fmt='html')

    @env.macro
    def statuscodes(class_name: str):
        """Render a markdown table of status codes for the given StatusCode class.

        Arguments:
            class_name: The name of the `StatusCode` subclass to render (e.g. 'BuildStatus')

        The table is built directly from `docs/generated/inventree_status_codes.json`
        (produced by the `export_status_codes` management command), so it can never
        drift out of sync with the status codes actually defined in the source code.
        """
        status_class = docs_data.status_codes()[class_name]

        # Record that this status code class has been rendered somewhere in the docs
        docs_data.observe_status_code(class_name)

        ret_data = '| Status | Value | Description |\n| --- | --- | --- |\n'

        for item in status_class['values']:
            description = item['description'] or item['label']
            ret_data += f'| {item["label"]} | {item["key"]} | {description} |\n'

        return ret_data

    def observe_setting(key: str, group: str):
        """Record that a particular setting has been observed.

        This is used to ensure that all settings are documented in the generated documentation.

        Arguments:
            key: The name of the setting to observe
            group: The group of the setting (e.g. 'global', 'user')
        """
        docs_data.observe_setting(key, group)

    @env.macro
    def rendersetting(
        key: str, setting: dict, short: bool = False, default: Optional[str] = None
    ):
        """Render a provided setting object into a table row.

        Arguments:
            key: The name of the setting to extract information for.
            setting: The setting object to render.
            short: If True, return a short version of the setting (default: False)
            default: An optional default value to override the setting's default display value.
        """
        name = setting['name']
        description = setting['description']
        default = default or setting.get('default')
        units = setting.get('units')

        default = f'`{default}`' if default else ''
        units = f'`{units}`' if units else ''

        if short:
            return f'<span title="{key}"><strong>{name}</strong></span>'

        return f'| <div title="{key}"><strong>{name}</strong></div> | {description} | {default} | {units} |'

    @env.macro
    def globalsetting(key: str, short: bool = False, default: Optional[str] = None):
        """Extract information on a particular global setting.

        Arguments:
            key: The name of the global setting to extract information for.
            short: If True, return a short version of the setting (default: False)
            default: An optional default value to override the setting's default display value.
        """
        setting = docs_data.settings('global')[key]

        # Settings are only 'observed' if they are displayed in full
        if not short:
            observe_setting(key, 'global')

        return rendersetting(key, setting, short=short, default=default)

    @env.macro
    def usersetting(key: str, short: bool = False):
        """Extract information on a particular user setting.

        Arguments:
            key: The name of the user setting to extract information for.
            short: If True, return a short version of the setting (default: False)
        """
        setting = docs_data.settings('user')[key]

        # Settings are only 'observed' if they are displayed in full
        if not short:
            observe_setting(key, 'user')

        return rendersetting(key, setting, short=short)

    @env.macro
    def configtable():
        """Generate a header for the configuration settings table."""
        return '| Environment Variable | Configuration File | Default | Description |\n| --- | --- | --- | --- |'

    @env.macro
    def configsetting(key: str, default: Optional[str] = None):
        """Extract information on a particular configuration setting.

        Arguments:
            key: The name of the configuration setting to extract information for.
            default: An optional default value to override the setting's default display value.
        """
        setting = docs_data.settings('config')[key]

        observe_setting(key, 'config')

        cfg_key = setting.get('config_key', None)
        cfg_key = f'`{cfg_key}`' if cfg_key else '-'

        default = default or setting.get('default_value', None)

        if default is None:
            default = '*Not Specified*'

        return f'| <span title="{key}" style="white-space: nowrap;"><code>{key}</code></span> | {cfg_key} | {default} |'

    @env.macro
    def tags_and_filters():
        """Return a list of all tags and filters."""
        ret_data = ''
        for ref in [['Tags', docs_data.tags()], ['Filters', docs_data.filters()]]:
            ret_data += f'### {ref[0]}\n\n| Namespace | Name | Description |\n| --- | --- | --- |\n'
            for value in ref[1]:
                title = (
                    value['title']
                    .replace('\n', ' ')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                )
                ret_data += f'| {value["library"]} | {value["name"]} | {title} |\n'
            ret_data += '\n'
        ret_data += '\n'

        return ret_data

    @env.macro
    def roles():
        """Render a markdown table of the available user permission roles.

        The table is built directly from `docs/generated/inventree_roles.json`
        (produced by the `export_roles` management command, sourced from
        `users.ruleset.RULESET_CHOICES`), so it can never drift out of sync with
        the roles actually defined in the source code.
        """
        ret_data = '| Role | Description |\n| --- | --- |\n'

        for role in docs_data.roles():
            description = role['description'] or role['label']
            ret_data += f'| **{role["label"]}** | {description} |\n'

        return ret_data

    @env.macro
    def audited_models():
        """Render a markdown table of the models which are recorded in the audit log.

        The table is built directly from `docs/generated/inventree_audited_models.json`
        (produced by the `export_audited_models` management command, sourced from
        the models which implement `InvenTreeAuditMixin`), so it can never drift out
        of sync with the models actually audited in the source code.
        """
        ret_data = '| Category | Model | Model Type | Parent | Notes |\n'
        ret_data += '| --- | --- | --- | --- | --- |\n'

        for model in docs_data.audited_models():
            parent = model['parent']
            notes = model['parent_note']

            if fields := model['include_fields']:
                fields = ', '.join(f'`{field}`' for field in fields)
                notes = f'Only the following fields are recorded: {fields}'

            ret_data += f'| {model["app"]} | {model["name"]} | `{model["model_type"]}` | {parent} | {notes} |\n'

        return ret_data

    @env.macro
    def report_context(type_: Literal['models', 'base'], model: str):
        """Extract information on a particular report context."""
        context = docs_data.report_context().get(type_).get(model)

        ret_data = '| Variable | Type | Description |\n| --- | --- | --- |\n'
        for k, v in context['context'].items():
            ret_data += f'| {k} | `{v["type"]}` | {v["description"]} |\n'

        return ret_data

    def render_attribute_table(attributes: dict, title: str) -> str:
        """Render a table of field/property information, in a collapsible (collapsed by default) block.

        Returns an empty string (including no block) if there is nothing to display.
        """
        if not attributes:
            return ''

        table = '| Variable | Type | Description |\n| --- | --- | --- |\n'

        for k, v in sorted(attributes.items()):
            description = ' '.join(v['description'].split())
            table += f'| {k} | `{v["type"]}` | {description} |\n'

        ret_data = f'??? note "{title}"\n\n'
        ret_data += textwrap.indent(table, '    ')

        # Trailing blank line, so consecutive macro calls (e.g. fields followed by
        # properties) don't run together when the template places them on adjacent lines
        return ret_data + '\n'

    @env.macro
    def reportable_model_context():
        """Render the full 'reportable model types' section.

        One heading plus fields/properties tables per model which templates can be
        rendered against (e.g. `Part`, `SalesOrder`, `StockItem`). The list of models
        comes directly from what `export_report_context` discovered via the
        `InvenTreeReportMixin`, so there is no manually-maintained per-model heading
        list to keep in sync here.
        """
        models = docs_data.report_context().get('models', {})

        ret_data = ''

        for info in sorted(models.values(), key=lambda item: item['name']):
            ret_data += f'### {info["name"]}\n\n'
            ret_data += render_attribute_table(info.get('fields', {}), 'Fields')
            ret_data += render_attribute_table(info.get('properties', {}), 'Properties')

        return ret_data

    @env.macro
    def related_model_context():
        """Render the full 'related model types' section.

        A "related" model is one which is not itself reportable, but which is
        referenced by a field or `@report_attribute` property on a reportable model
        (e.g. `PartCategory` via `Part.category`, `SupplierPart` via `Part.default_supplier`).

        These are discovered automatically (one hop out from the reportable models) by
        the `export_report_context` management command, so there is no manually-maintained
        list of related models to keep in sync here.
        """
        related = docs_data.report_context().get('related_models', {})

        ret_data = ''

        for info in sorted(related.values(), key=lambda item: item['name']):
            ret_data += f'### {info["name"]}\n\n'
            ret_data += render_attribute_table(info.get('fields', {}), 'Fields')
            ret_data += render_attribute_table(info.get('properties', {}), 'Properties')

        return ret_data

    @env.macro
    def icon(
        source: str,
        size: str = '20px',
        color: Optional[str] = None,
        title: Optional[str] = None,
    ):
        """Return a tabler icon for a given source.

        Arguments:
            source: The name of the icon to display (e.g. 'check', 'cross', etc.)
            size: The size of the icon (default: 20px)
            color: The color of the icon (default: None)
            title: The title of the icon (default: None)

        Requires CSS to be loaded from:
        https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.31.0/dist/tabler-icons.min.css
        """
        c = f' color: {color};' if color else ''
        t = f' <i>{title}</i>' if title else ''

        return f"<i class='ti ti-{source}' style='font-size: {size};{c}'></i>{t}"

    @env.macro
    def image(
        source: str,
        title: Optional[str] = '',
        iid: Optional[str] = '',
        alt: Optional[str] = '',
        base: Optional[str] = '',
        maxwidth: Optional[str] = '',
        maxheight: Optional[str] = '',
    ):
        """Render an image within the documentation.

        Arguments:
            title: The title of the image (default: '')
            source: The name of the image to display (e.g. 'check', 'cross', etc.)
            iid: The ID of the image (default: '')
            alt: The alt text for the image (default: '')
            base: The base directory for the image (default: './assets/images/')
            maxwidth: The maximum width of the image (default: '')
            maxheight: The maximum height of the image (default: '')

        - This will render an image which can be clicked on to expand to full size.
        - It will also validate that the image exists in the specified directory.

        The image must be located in the './docs/assets/images/' directory
        """
        # Allow external images too - without validation
        if source.startswith('http'):
            img = source
        else:
            basedir = os.path.dirname(__file__)
            basedir = os.path.join(basedir, 'docs', 'assets', 'images')

            if base:
                basedir = os.path.abspath(os.path.join(basedir, base))
            filename = os.path.join(basedir, source)

            if not os.path.exists(filename):
                raise FileNotFoundError(f'Image {filename} does not exist.')

            # Now, create a proper URL to the image
            img = os.path.join(assets_dir, 'images', base, source)

        if not title:
            title = os.path.splitext(source)[0]

        if not iid:
            iid = title.replace(' ', '_').replace('-', '_')

        if not alt:
            alt = iid

        styles = []

        if maxwidth:
            styles.append(f'max-width: {maxwidth};')
        if maxheight:
            styles.append(f'max-height: {maxheight};')

        style = f"style='{' '.join(styles)}' " if styles else ''

        return textwrap.dedent(f"""
        <figure class='image image-inventree'>
            <a href='#{iid}'>
                <img class='img-inline' src='{img}' alt='{alt}' title='{title}' {style}/>
            </a>
            <a href='#_' class='overlay' id='{iid}'>
                <img src='{img}' alt='{alt}' />
            </a>
        </figure>
        """)
