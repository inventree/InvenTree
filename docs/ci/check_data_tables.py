"""Check that the tables generated from exported backend data rendered correctly.

The following macros render tables directly from data files exported from the
backend (docs/generated/*). For each macro call in the markdown sources, the
rendered page must contain a table whose rows match the exported data:

- statuscodes(class_name)      -> inventree_status_codes.json
- roles()                      -> inventree_roles.json
- audited_models()             -> inventree_audited_models.json
- report_context(type_, model) -> inventree_report_context.json
- reportable_model_context()   -> inventree_report_context.json ('models')
- related_model_context()      -> inventree_report_context.json ('related_models')
- tags_and_filters()           -> inventree_tags.yml / inventree_filters.yml

Usage:
    python docs/ci/check_data_tables.py [--site-dir <path>]
"""

import json
from pathlib import Path

import yaml
from docs_checks import (
    GENERATED_DIR,
    Checker,
    MacroCall,
    Page,
    check_macro_errors,
    find_macro_calls,
    find_tables,
    iter_pages,
    normalize,
    run,
    table_headers,
    table_rows,
)


def load_json(name: str):
    """Load a generated JSON data file."""
    with open(GENERATED_DIR / name, encoding='utf-8') as f:
        return json.load(f)


def load_yaml(name: str):
    """Load a generated YAML data file."""
    with open(GENERATED_DIR / name, encoding='utf-8') as f:
        return yaml.safe_load(f)


def rows(*rows) -> list[list[str]]:
    """Normalize expected table rows, for comparison with rendered table rows."""
    return [[normalize(str(cell)) for cell in row] for row in rows]


def describe_mismatch(expected: list, found: list) -> str:
    """Return a short description of the difference between two lists of table rows."""
    if len(expected) != len(found):
        return f'expected {len(expected)} rows, found {len(found)}'

    for idx, (exp, fnd) in enumerate(zip(expected, found, strict=True)):
        if exp != fnd:
            return f'row {idx + 1}: expected {exp}, found {fnd}'

    return 'no difference'


def check_table(page, call, headers, expected, checker, scope=None):
    """Check that a table with the provided headers and expected rows is rendered.

    Arguments:
        page: The page being checked
        call: The macro call (for error messages), or a label string
        headers: Expected table headers
        expected: Expected (normalized) table rows
        checker: Checker instance
        scope: Element to search within (default: the whole page)
    """
    label = (
        f'{page.label}:{call.line} {call.name}{tuple(call.args)}'
        if isinstance(call, MacroCall)
        else f'{page.label}: {call}'
    )

    tables = find_tables(scope or page.soup, headers)

    if not checker.check(
        bool(tables), f'{label} no table rendered with headers {headers}'
    ):
        return

    found = [table_rows(table) for table in tables]

    checker.check(
        expected in found,
        f'{label} no rendered table matches the exported data ({describe_mismatch(expected, found[0])})',
    )


def expected_statuscodes(status_codes: dict, class_name: str) -> list:
    """Expected table rows for the statuscodes() macro."""
    return rows(*[
        (item['label'], item['key'], item['description'] or item['label'])
        for item in status_codes[class_name]['values']
    ])


def expected_roles(roles: list) -> list:
    """Expected table rows for the roles() macro."""
    return rows(*[
        (role['label'], role['description'] or role['label']) for role in roles
    ])


def expected_audited_models(models: list) -> list:
    """Expected table rows for the audited_models() macro."""
    result = []

    for model in models:
        notes = model['parent_note']

        if fields := model['include_fields']:
            notes = 'Only the following fields are recorded: ' + ', '.join(fields)

        result.append((
            model['app'],
            model['name'],
            model['model_type'],
            model['parent'],
            notes,
        ))

    return rows(*result)


def expected_context(context: dict, sort: bool = False) -> list:
    """Expected table rows for a report context / attribute table."""
    items = sorted(context.items()) if sort else context.items()

    return rows(*[
        (key, value['type'], ' '.join(value['description'].split()))
        for key, value in items
    ])


def expected_tags(tags: list) -> list:
    """Expected table rows for a tags / filters table."""
    return rows(*[
        (tag['library'], tag['name'], tag['title'].replace('\n', ' ')) for tag in tags
    ])


def section_elements(heading) -> list:
    """Return the elements following a heading, up to the next heading of the same (or higher) level."""
    level = int(heading.name[1])
    elements = []

    for sibling in heading.find_next_siblings():
        if sibling.name in [f'h{n}' for n in range(1, level + 1)]:
            break
        elements.append(sibling)

    return elements


def check_model_sections(page: Page, macro: str, models: dict, checker: Checker):
    """Check the per-model sections rendered by reportable/related_model_context()."""
    content = page.soup.select_one('article') or page.soup
    headings = {
        h.get_text(' ', strip=True).rstrip('¶').strip(): h
        for h in content.find_all('h3')
    }

    for info in sorted(models.values(), key=lambda item: item['name']):
        label = f'{page.label}: {macro}() model "{info["name"]}"'
        heading = headings.get(info['name'])

        if not checker.check(heading is not None, f'{label} heading not rendered'):
            continue

        blocks = {
            details.summary.get_text(strip=True): details
            for element in section_elements(heading)
            for details in (
                [element] if element.name == 'details' else element.find_all('details')
            )
            if details.summary
        }

        for title, key in [('Fields', 'fields'), ('Properties', 'properties')]:
            attributes = info.get(key) or {}

            if not attributes:
                checker.check(
                    title not in blocks, f'{label} unexpected "{title}" block rendered'
                )
                continue

            if checker.check(title in blocks, f'{label} "{title}" block not rendered'):
                check_table(
                    page,
                    f'{macro}() model "{info["name"]}" {title}',
                    ['Variable', 'Type', 'Description'],
                    expected_context(attributes, sort=True),
                    checker,
                    scope=blocks[title],
                )


def check_tags_and_filters(page: Page, tags: list, filters: list, checker: Checker):
    """Check the tables rendered by the tags_and_filters() macro."""
    content = page.soup.select_one('article') or page.soup

    for title, data in [('Tags', tags), ('Filters', filters)]:
        heading = next(
            (
                h
                for h in content.find_all('h3')
                if h.get_text(' ', strip=True).rstrip('¶').strip() == title
            ),
            None,
        )

        if not checker.check(
            heading is not None,
            f'{page.label}: tags_and_filters() "{title}" heading not rendered',
        ):
            continue

        table = next(
            (
                element
                for element in section_elements(heading)
                if element.name == 'table'
            ),
            None,
        )

        if not checker.check(
            table is not None
            and table_headers(table) == ['Namespace', 'Name', 'Description'],
            f'{page.label}: tags_and_filters() "{title}" table not rendered',
        ):
            continue

        expected = expected_tags(data)
        found = table_rows(table)

        checker.check(
            found == expected,
            f'{page.label}: tags_and_filters() "{title}" table does not match exported data ({describe_mismatch(expected, found)})',
        )


MACROS = [
    'statuscodes',
    'roles',
    'audited_models',
    'report_context',
    'reportable_model_context',
    'related_model_context',
    'tags_and_filters',
]


def check_data_tables(site_dir: Path, checker: Checker):
    """Check all data table macro calls against the rendered documentation."""
    status_codes = load_json('inventree_status_codes.json')
    roles = load_json('inventree_roles.json')
    audited = load_json('inventree_audited_models.json')
    report_context = load_json('inventree_report_context.json')
    tags = load_yaml('inventree_tags.yml')
    filters = load_yaml('inventree_filters.yml')

    counts = dict.fromkeys(MACROS, 0)

    for page in iter_pages(site_dir):
        page_calls = []

        for macro in MACROS:
            calls, skipped = find_macro_calls(page, macro)
            counts[macro] += len(calls)
            page_calls.extend(calls)

            checker.check(
                skipped == 0,
                f'{page.label}: {skipped} {macro}() calls with non-literal arguments cannot be checked',
            )

        if not page_calls:
            continue

        if not checker.check(
            page.output.exists(), f'{page.label}: Missing rendered page {page.output}'
        ):
            continue

        check_macro_errors(page, checker)

        for call in page_calls:
            label = f'{page.label}:{call.line} {call.name}{tuple(call.args)}'

            if call.name == 'statuscodes':
                class_name = call.arg(0, 'class_name')

                if checker.check(
                    class_name in status_codes, f'{label} unknown status code class'
                ):
                    check_table(
                        page,
                        call,
                        ['Status', 'Value', 'Description'],
                        expected_statuscodes(status_codes, class_name),
                        checker,
                    )

            elif call.name == 'roles':
                check_table(
                    page, call, ['Role', 'Description'], expected_roles(roles), checker
                )

            elif call.name == 'audited_models':
                check_table(
                    page,
                    call,
                    ['Category', 'Model', 'Model Type', 'Parent', 'Notes'],
                    expected_audited_models(audited),
                    checker,
                )

            elif call.name == 'report_context':
                type_ = call.arg(0, 'type_')
                model = call.arg(1, 'model')
                context = report_context.get(type_, {}).get(model)

                if checker.check(
                    context is not None, f'{label} unknown report context'
                ):
                    check_table(
                        page,
                        call,
                        ['Variable', 'Type', 'Description'],
                        expected_context(context['context']),
                        checker,
                    )

            elif call.name == 'reportable_model_context':
                check_model_sections(
                    page, call.name, report_context.get('models', {}), checker
                )

            elif call.name == 'related_model_context':
                check_model_sections(
                    page, call.name, report_context.get('related_models', {}), checker
                )

            elif call.name == 'tags_and_filters':
                check_tags_and_filters(page, tags, filters, checker)

    for macro, count in counts.items():
        checker.check(count > 0, f'No {macro}() macro calls found in documentation')

    print(
        '  Checked '
        + ', '.join(f'{count} {macro}()' for macro, count in counts.items())
        + ' calls'
    )


if __name__ == '__main__':
    run('Checking tables generated from exported data', check_data_tables)
