"""Check the rendered API schema pages in the built documentation.

Each schema section page must be rendered, contain every API operation (and
schema component) defined for that section, and the combined set of rendered
operations must match the full API schema.

Usage:
    python docs/ci/check_api_schema.py [--site-dir <path>]
"""

import html
import importlib.util
import re
from pathlib import Path

import yaml
from docs_checks import DOCS_DIR, GENERATED_DIR, Checker, run

# Generated (full) API schema file, produced by 'invoke build-docs'
SCHEMA_FILE = GENERATED_DIR / 'schema.yml'

# Directory containing the per-section schema files, produced by extract_schema.py
SECTION_SCHEMA_DIR = DOCS_DIR / 'docs' / 'api' / 'schema'

HTTP_METHODS = ('get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace')

# Lower bounds on the overall API size - catch a truncated / empty schema
MIN_OPERATIONS = 500
MIN_SCHEMAS = 300

# Well-known endpoints which must be documented on the specified section page
EXPECTED_OPERATIONS = [
    ('general', 'GET', '/api/'),
    ('part', 'GET', '/api/part/'),
    ('part', 'POST', '/api/part/'),
    ('part', 'GET', '/api/part/{id}/'),
    ('part', 'GET', '/api/part/category/'),
    ('stock', 'GET', '/api/stock/'),
    ('stock', 'GET', '/api/stock/location/'),
    ('build', 'GET', '/api/build/'),
    ('order', 'GET', '/api/order/po/'),
    ('order', 'GET', '/api/order/so/'),
    ('company', 'GET', '/api/company/'),
    ('bom', 'GET', '/api/bom/'),
    ('user', 'GET', '/api/user/me/'),
    ('barcode', 'POST', '/api/barcode/'),
    ('settings', 'GET', '/api/settings/global/'),
    ('label', 'GET', '/api/label/template/'),
    ('report', 'GET', '/api/report/template/'),
    ('plugins', 'GET', '/api/plugins/'),
    ('machine', 'GET', '/api/machine/'),
    ('auth', 'POST', '/api/auth/v1/auth/login'),
    ('background-task', 'GET', '/api/background-task/'),
]

# Well-known schema components which must be documented on the specified section page
EXPECTED_SCHEMAS = [
    ('part', 'Part'),
    ('part', 'Category'),
    ('stock', 'StockItem'),
    ('stock', 'Location'),
    ('build', 'Build'),
    ('order', 'PurchaseOrder'),
    ('order', 'SalesOrder'),
    ('company', 'Company'),
    ('bom', 'BomItem'),
]

# Rendered operation heading, e.g.
# <h3 id="get-apipart"><span class="http-get">GET</span> /api/part/<a class="headerlink" ...
OPERATION_RE = re.compile(
    r'<h3 id="[^"]*"><span class="http-(\w+)">\w+</span>\s*(.*?)<a class="headerlink"'
)

# Any level-2 heading (used to delimit page sections)
H2_RE = re.compile(r'<h2 id="([^"]*)"')

# Level-3 heading text (used for schema component names)
H3_TEXT_RE = re.compile(r'<h3 id="[^"]*">(.*?)<a class="headerlink"')

# Rendered API title, e.g. <h1 id="inventree-api-571">InvenTree API <span class="api-version">571</span>
API_VERSION_RE = re.compile(r'<span class="api-version">([^<]*)</span>')


def load_yaml(path: Path) -> dict:
    """Load a YAML file."""
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def read_html(path: Path) -> str:
    """Read a rendered HTML page."""
    with open(path, encoding='utf-8') as f:
        return f.read()


def schema_operations(schema: dict) -> set:
    """Return the set of (METHOD, path) operations defined in an OpenAPI schema."""
    ops = set()

    for path, item in (schema.get('paths') or {}).items():
        for method in item or {}:
            if method.lower() in HTTP_METHODS:
                ops.add((method.upper(), path))

    return ops


def strip_tags(text: str) -> str:
    """Remove any HTML tags and unescape entities."""
    return html.unescape(re.sub(r'<[^>]+>', '', text)).strip()


def split_operations(page: str) -> dict:
    """Split a rendered schema page into {(METHOD, path): html_chunk}."""
    matches = list(OPERATION_RE.finditer(page))
    boundaries = [m.start() for m in H2_RE.finditer(page)]

    chunks = {}

    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(page)

        # Do not run past the start of the next tag group / "Schemas" section
        next_h2 = [b for b in boundaries if start < b < end]
        if next_h2:
            end = next_h2[0]

        key = (match.group(1).upper(), strip_tags(match.group(2)))
        chunks[key] = page[start:end]

    return chunks


def rendered_schema_names(page: str) -> set:
    """Return the names of all schema components rendered in the 'Schemas' section."""
    start = page.find('<h2 id="schemas"')

    if start < 0:
        return set()

    nxt = H2_RE.search(page, start + 1)
    end = nxt.start() if nxt else len(page)

    return {strip_tags(m.group(1)) for m in H3_TEXT_RE.finditer(page[start:end])}


def section_keys() -> list:
    """Return the list of API schema sections, as defined in extract_schema.py."""
    spec = importlib.util.spec_from_file_location(
        'extract_schema', DOCS_DIR / 'extract_schema.py'
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return [*module.SPECIAL_PATHS.keys(), module.GENERAL_PATH]


def check_api_schema(site_dir: Path, checker: Checker):
    """Check that the rendered API schema pages contain sensible information."""
    if not checker.check(
        SCHEMA_FILE.exists(), f'API schema file not found: {SCHEMA_FILE}'
    ):
        return

    schema = load_yaml(SCHEMA_FILE)
    version = str(schema.get('info', {}).get('version', ''))
    all_ops = schema_operations(schema)
    all_schemas = set((schema.get('components') or {}).get('schemas') or {})

    checker.check(bool(version), 'API schema does not define info.version')
    checker.check(
        len(all_ops) >= MIN_OPERATIONS,
        f'API schema defines only {len(all_ops)} operations (expected >= {MIN_OPERATIONS})',
    )
    checker.check(
        len(all_schemas) >= MIN_SCHEMAS,
        f'API schema defines only {len(all_schemas)} schemas (expected >= {MIN_SCHEMAS})',
    )

    # Index page
    index_file = site_dir / 'api' / 'schema' / 'index.html'

    if checker.check(index_file.exists(), f'Missing schema index page: {index_file}'):
        index = read_html(index_file)
        checker.check(
            f'API version: <code>{version}</code>' in index,
            f'Schema index page does not reference API version {version}',
        )

    rendered_ops = {}
    rendered_schemas = {}

    for key in section_keys():
        page_file = site_dir / 'api' / 'schema' / key / 'index.html'
        section_file = SECTION_SCHEMA_DIR / f'{key}.yml'
        label = f'[api/schema/{key}]'

        if not checker.check(
            page_file.exists(), f'{label} Missing rendered page: {page_file}'
        ):
            continue

        if index_file.exists():
            checker.check(
                f'href="{key}/"' in index,
                f'Schema index page does not link to section "{key}"',
            )

        page = read_html(page_file)

        # The OAD plugin directive must have been replaced with rendered content
        checker.check('[OAD(' not in page, f'{label} Contains unrendered OAD directive')

        page_versions = API_VERSION_RE.findall(page)
        checker.check(
            page_versions == [version],
            f'{label} Rendered API version {page_versions} does not match schema version {version}',
        )

        if not checker.check(
            section_file.exists(), f'{label} Missing section schema: {section_file}'
        ):
            continue

        section = load_yaml(section_file)
        expected_ops = schema_operations(section)
        expected_schemas = set((section.get('components') or {}).get('schemas') or {})

        checker.check(bool(expected_ops), f'{label} Section defines no API operations')

        ops = split_operations(page)
        rendered_ops[key] = set(ops)

        missing = expected_ops - set(ops)
        extra = set(ops) - expected_ops

        checker.check(
            not missing,
            f'{label} {len(missing)} operations not rendered: {sorted(missing)[:10]}',
        )
        checker.check(
            not extra,
            f'{label} {len(extra)} unexpected operations rendered: {sorted(extra)[:10]}',
        )

        no_response = sorted(
            op for op, chunk in ops.items() if '<strong>Responses</strong>' not in chunk
        )
        checker.check(
            not no_response,
            f'{label} {len(no_response)} operations have no responses documented: {no_response[:10]}',
        )

        names = rendered_schema_names(page)
        rendered_schemas[key] = names
        missing_schemas = expected_schemas - names

        checker.check(
            not missing_schemas,
            f'{label} {len(missing_schemas)} schemas not rendered: {sorted(missing_schemas)[:10]}',
        )

    # Every operation in the full schema must appear on exactly one section page
    combined = set().union(*rendered_ops.values()) if rendered_ops else set()
    missing = all_ops - combined

    checker.check(
        not missing,
        f'{len(missing)} API operations not rendered on any page: {sorted(missing)[:10]}',
    )

    total = sum(len(ops) for ops in rendered_ops.values())
    checker.check(
        total == len(combined),
        'Some API operations are rendered on more than one section page',
    )

    # Spot-check well-known endpoints and models
    for key, method, path in EXPECTED_OPERATIONS:
        checker.check(
            (method, path) in rendered_ops.get(key, set()),
            f'[api/schema/{key}] Expected operation not rendered: {method} {path}',
        )

    for key, name in EXPECTED_SCHEMAS:
        checker.check(
            name in rendered_schemas.get(key, set()),
            f'[api/schema/{key}] Expected schema not rendered: {name}',
        )

    print(
        f'  API version {version}: {len(combined)} operations across '
        f'{len(rendered_ops)} section pages'
    )


if __name__ == '__main__':
    run('Checking API schema pages', check_api_schema)
